# GPU Server Patch: Speaker Identification

## 部署方法

1. 将 `speaker_session.py` 上传到 GPU 服务器 `/root/whisperx_server/`
2. 在 `server.py` 中添加以下代码：

### 导入（文件顶部）

```python
from speaker_session import SpeakerSessionStore
import numpy as np
```

### 初始化（app 创建后）

```python
speaker_store = SpeakerSessionStore()
```

### 新接口（现有接口之后添加）

```python
@app.post("/transcribe-with-speaker")
async def transcribe_with_speaker(
    file: UploadFile = File(...),
    language: str = Form(None),
    session_id: str = Form(None),
):
    """Transcribe audio and identify speaker via CAM++ embedding."""
    import tempfile, os

    # Save uploaded file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # 1. Qwen3-ASR transcription (reuse existing transcription logic)
        text = transcribe_audio(tmp_path, language)

        # 2. Speaker embedding via CAM++
        speaker_id = None
        speaker_confidence = None

        if session_id and os.path.getsize(tmp_path) > 4800:  # >0.3s at 16kHz
            try:
                embedding = extract_speaker_embedding(tmp_path)
                if embedding is not None:
                    speaker_id, speaker_confidence = speaker_store.identify_or_register(
                        session_id, embedding
                    )
                    speaker_confidence = round(speaker_confidence, 4)
            except Exception as e:
                print(f"[Speaker] Embedding extraction failed: {e}")

        return {
            "text": text,
            "language": language or "auto",
            "speaker_id": speaker_id,
            "speaker_confidence": speaker_confidence,
        }
    finally:
        os.unlink(tmp_path)


def extract_speaker_embedding(audio_path: str):
    """Extract 192-dim speaker embedding using CAM++."""
    # Adjust import based on your actual CAM++ setup
    # Option A: If using FunASR CAM++
    try:
        from funasr import AutoModel
        # Initialize once (cache at module level for production)
        if not hasattr(extract_speaker_embedding, "_model"):
            extract_speaker_embedding._model = AutoModel(
                model="iic/speech_campplus_sv_zh-cn_16k-common",
                device="cuda",
            )
        model = extract_speaker_embedding._model
        result = model.generate(input=audio_path)
        if result and len(result) > 0:
            embedding = result[0].get("spk_embedding") or result[0].get("embedding")
            if embedding is not None:
                return np.array(embedding, dtype=np.float32)
    except Exception as e:
        print(f"[Speaker] CAM++ error: {e}")

    return None
```

### 注意事项

- `transcribe_audio()` 需替换为你现有 server.py 中的实际转录函数名
- `extract_speaker_embedding()` 中的 CAM++ 模型初始化需匹配你的实际环境
- 首次加载 CAM++ 模型会较慢，后续请求使用缓存的模型实例
