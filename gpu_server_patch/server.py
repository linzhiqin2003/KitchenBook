import os
import tempfile
import time
import logging
import functools
import threading

import torch
_original_torch_load = torch.load
@functools.wraps(_original_torch_load)
def _patched_torch_load(*args, **kwargs):
    if "weights_only" not in kwargs:
        kwargs["weights_only"] = False
    return _original_torch_load(*args, **kwargs)
torch.load = _patched_torch_load

import numpy as np
import soundfile as sf
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("asr_server")

app = FastAPI(title="ASR Server (Qwen3-ASR + CAM++)", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

asr_model = None
vad_model = None
spk_model = None


# ── Speaker Session Store (cross-segment speaker tracking) ──

class SpeakerSessionStore:
    SIMILARITY_THRESHOLD = 0.55
    SESSION_TTL = 3600  # 1 hour

    def __init__(self):
        self._lock = threading.Lock()
        self._sessions: dict = {}
        self._start_cleanup_thread()

    def identify_or_register(self, session_id: str, embedding: np.ndarray) -> tuple:
        embedding = embedding / (np.linalg.norm(embedding) + 1e-8)
        with self._lock:
            if session_id not in self._sessions:
                self._sessions[session_id] = {"speakers": [], "last_active": time.time()}
            session = self._sessions[session_id]
            session["last_active"] = time.time()
            speakers = session["speakers"]

            best_idx = -1
            best_sim = -1.0
            for i, spk in enumerate(speakers):
                sim = float(np.dot(embedding, spk["centroid"]))
                if sim > best_sim:
                    best_sim = sim
                    best_idx = i

            if best_sim >= self.SIMILARITY_THRESHOLD and best_idx >= 0:
                spk = speakers[best_idx]
                n = spk["count"]
                new_centroid = (spk["centroid"] * n + embedding) / (n + 1)
                new_centroid = new_centroid / (np.linalg.norm(new_centroid) + 1e-8)
                spk["centroid"] = new_centroid
                spk["count"] = n + 1
                label = f"speaker_{best_idx + 1}"
                return label, best_sim
            else:
                speakers.append({"centroid": embedding.copy(), "count": 1})
                label = f"speaker_{len(speakers)}"
                return label, 1.0

    def _start_cleanup_thread(self):
        def cleanup():
            while True:
                time.sleep(300)
                cutoff = time.time() - self.SESSION_TTL
                with self._lock:
                    expired = [sid for sid, s in self._sessions.items() if s["last_active"] < cutoff]
                    for sid in expired:
                        del self._sessions[sid]
        t = threading.Thread(target=cleanup, daemon=True)
        t.start()


speaker_store = SpeakerSessionStore()


def load_asr_model():
    global asr_model
    if asr_model is not None:
        return asr_model
    from qwen_asr import Qwen3ASRModel
    logger.info("Loading Qwen3-ASR-1.7B...")
    asr_model = Qwen3ASRModel.from_pretrained(
        "Qwen/Qwen3-ASR-1.7B",
        dtype=torch.float16,
        device_map="cuda:0",
        max_inference_batch_size=32,
        max_new_tokens=512,
        forced_aligner="Qwen/Qwen3-ForcedAligner-0.6B",
        forced_aligner_kwargs=dict(
            dtype=torch.float16,
            device_map="cuda:0",
        ),
    )
    logger.info("Qwen3-ASR-1.7B loaded")
    return asr_model


def load_vad_model():
    global vad_model
    if vad_model is not None:
        return vad_model
    from funasr import AutoModel
    logger.info("Loading FunASR VAD (fsmn-vad)...")
    vad_model = AutoModel(model="fsmn-vad")
    logger.info("VAD loaded")
    return vad_model


def load_spk_model():
    global spk_model
    if spk_model is not None:
        return spk_model
    from funasr import AutoModel
    logger.info("Loading CAM++ speaker model...")
    spk_model = AutoModel(model="cam++", model_revision="v2.0.2")
    logger.info("CAM++ loaded")
    return spk_model


def extract_speaker_embeddings(audio_path, vad_segments):
    """Extract speaker embeddings for each VAD segment using CAM++."""
    model = load_spk_model()
    audio_data, sr = sf.read(audio_path)
    if len(audio_data.shape) > 1:
        audio_data = audio_data[:, 0]

    embeddings = []
    segment_info = []
    for seg in vad_segments:
        start_ms, end_ms = seg[0], seg[1]
        start_sample = int(start_ms / 1000 * sr)
        end_sample = int(end_ms / 1000 * sr)
        chunk = audio_data[start_sample:end_sample]

        if len(chunk) < sr * 0.3:  # skip segments < 300ms
            continue

        # Write chunk to temp file for CAM++
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            sf.write(tmp.name, chunk, sr)
            result = model.generate(input=tmp.name)
            os.unlink(tmp.name)

        if result and len(result) > 0 and "spk_embedding" in result[0]:
            emb = _to_numpy(result[0]["spk_embedding"])
            embeddings.append(emb)
            segment_info.append({"start": start_ms / 1000, "end": end_ms / 1000})

    return embeddings, segment_info


def cluster_speakers(embeddings, oracle_num=None):
    """Cluster speaker embeddings using cosine similarity + agglomerative clustering."""
    if not embeddings:
        return []

    from sklearn.cluster import AgglomerativeClustering
    from sklearn.preprocessing import normalize

    emb_matrix = np.stack(embeddings)
    emb_matrix = normalize(emb_matrix)

    if oracle_num and oracle_num > 0:
        n_clusters = oracle_num
    else:
        n_clusters = min(max(2, len(embeddings) // 5), 10)
        n_clusters = min(n_clusters, len(embeddings))

    if len(embeddings) == 1:
        return [0]

    clustering = AgglomerativeClustering(
        n_clusters=n_clusters,
        metric="cosine",
        linkage="average",
    )
    labels = clustering.fit_predict(emb_matrix)
    return labels.tolist()


def assign_speakers_to_asr(asr_segments, diar_segments):
    """Assign speaker labels to ASR segments by timestamp overlap."""
    for seg in asr_segments:
        best_speaker = "UNKNOWN"
        best_overlap = 0.0
        for diar in diar_segments:
            overlap_start = max(seg["start"], diar["start"])
            overlap_end = min(seg["end"], diar["end"])
            overlap = max(0, overlap_end - overlap_start)
            if overlap > best_overlap:
                best_overlap = overlap
                best_speaker = diar["speaker"]
        seg["speaker"] = best_speaker
    return asr_segments


def _to_numpy(embedding):
    """Convert embedding to 1D numpy array, handling both tensor and array inputs."""
    if hasattr(embedding, 'cpu'):
        arr = embedding.cpu().numpy().astype(np.float32)
    else:
        arr = np.array(embedding, dtype=np.float32)
    return arr.flatten()


def _extract_single_embedding(audio_path):
    """Extract a single speaker embedding from audio using CAM++."""
    model = load_spk_model()
    result = model.generate(input=audio_path)
    if result and len(result) > 0 and "spk_embedding" in result[0]:
        return _to_numpy(result[0]["spk_embedding"])
    return None


@app.on_event("startup")
async def startup():
    logger.info(f"Device: {DEVICE}")
    logger.info("Pre-loading models...")
    load_asr_model()
    load_vad_model()
    load_spk_model()
    logger.info("All models loaded. Server ready!")


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "device": DEVICE,
        "gpu": torch.cuda.get_device_name(0) if DEVICE == "cuda" else "N/A",
        "gpu_memory_mb": round(torch.cuda.memory_allocated(0) / 1024**2, 1) if DEVICE == "cuda" else 0,
        "models": {
            "asr": "Qwen3-ASR-1.7B" if asr_model else "not loaded",
            "vad": "fsmn-vad" if vad_model else "not loaded",
            "speaker": "CAM++" if spk_model else "not loaded",
        },
    }


@app.post("/transcribe")
async def transcribe(
    file: UploadFile = File(...),
    language: str = Form(None),
    diarize: bool = Form(True),
    oracle_num: int = Form(None),
):
    start_time = time.time()

    suffix = os.path.splitext(file.filename or "audio.wav")[1] or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Step 1: ASR
        logger.info(f"Transcribing: {file.filename}, lang={language}, diarize={diarize}")
        model = load_asr_model()
        asr_results = model.transcribe(
            audio=tmp_path,
            language=language,
            return_time_stamps=True,
        )

        result = asr_results[0]
        detected_language = result.language
        full_text = result.text
        logger.info(f"ASR done. Language: {detected_language}")

        # Build word-level segments from ForcedAlignItem list
        # FIX: result.time_stamps is a flat list of ForcedAlignItem,
        # NOT a list of lists. Each item has .text, .start_time, .end_time.
        segments = []
        if result.time_stamps:
            for ts in result.time_stamps:
                segments.append({
                    "text": ts.text,
                    "start": ts.start_time,
                    "end": ts.end_time,
                })

        # Step 2: Speaker diarization
        diar_result = []
        if diarize:
            try:
                # VAD
                vad = load_vad_model()
                vad_res = vad.generate(input=tmp_path)
                vad_segments = vad_res[0]["value"] if vad_res and len(vad_res) > 0 else []
                logger.info(f"VAD done: {len(vad_segments)} segments")

                if vad_segments:
                    # Speaker embeddings
                    embeddings, seg_info = extract_speaker_embeddings(tmp_path, vad_segments)
                    logger.info(f"Extracted {len(embeddings)} speaker embeddings")

                    if embeddings:
                        # Cluster
                        labels = cluster_speakers(embeddings, oracle_num)
                        for i, info in enumerate(seg_info):
                            info["speaker"] = f"speaker_{labels[i]}"
                        diar_result = seg_info

                        # Assign speakers to ASR segments
                        if segments:
                            segments = assign_speakers_to_asr(segments, diar_result)

                        logger.info(f"Diarization done: {len(set(labels))} speakers")

            except Exception as e:
                logger.warning(f"Diarization failed (non-fatal): {e}", exc_info=True)

        elapsed = time.time() - start_time

        return JSONResponse({
            "text": full_text,
            "language": detected_language,
            "segments": segments,
            "diarization": diar_result,
            "processing_time": round(elapsed, 2),
        })

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        os.unlink(tmp_path)


@app.post("/transcribe-with-speaker")
async def transcribe_with_speaker(
    file: UploadFile = File(...),
    language: str = Form(None),
    session_id: str = Form(""),
):
    """ASR + cross-segment speaker identification.

    Uses CAM++ to extract a speaker embedding from the entire audio clip,
    then matches it against the session's known speakers via SpeakerSessionStore.
    This enables consistent speaker labels across multiple short VAD segments.
    """
    start_time = time.time()

    suffix = os.path.splitext(file.filename or "audio.wav")[1] or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Step 1: ASR
        logger.info(f"Transcribe+Speaker: {file.filename}, lang={language}, session={session_id[:8] if session_id else 'none'}")
        model = load_asr_model()
        asr_results = model.transcribe(
            audio=tmp_path,
            language=language,
        )

        result = asr_results[0]
        text = result.text or ""
        detected_language = result.language or ""

        # Step 2: Speaker embedding
        speaker_id = None
        speaker_confidence = None

        if text.strip():
            try:
                embedding = _extract_single_embedding(tmp_path)
                if embedding is not None:
                    if session_id:
                        speaker_id, speaker_confidence = speaker_store.identify_or_register(
                            session_id, embedding
                        )
                    else:
                        speaker_id = "speaker_1"
                        speaker_confidence = 1.0
            except Exception as e:
                logger.warning(f"Speaker embedding failed: {e}")

        elapsed = time.time() - start_time
        logger.info(
            f"Transcribe+Speaker done: {len(text)} chars, lang={detected_language}, "
            f"speaker={speaker_id}, conf={speaker_confidence or 0:.2f}, {elapsed:.2f}s"
        )

        return JSONResponse({
            "text": text,
            "language": detected_language,
            "speaker_id": speaker_id,
            "speaker_confidence": speaker_confidence,
            "processing_time": round(elapsed, 2),
        })

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        os.unlink(tmp_path)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
