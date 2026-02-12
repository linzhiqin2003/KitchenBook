"""
Speaker Session Store — thread-safe in-memory speaker identification.

Each session maintains a list of known speakers (centroid embedding + count).
New embeddings are matched against existing speakers via cosine similarity.
"""

import threading
import time
import numpy as np


class SpeakerSessionStore:
    SIMILARITY_THRESHOLD = 0.75
    SESSION_TTL = 3600  # 1 hour

    def __init__(self):
        self._lock = threading.Lock()
        # session_id -> {"speakers": [{"centroid": np.array, "count": int}], "last_active": float}
        self._sessions: dict = {}
        self._start_cleanup_thread()

    def identify_or_register(self, session_id: str, embedding: np.ndarray) -> tuple:
        """Match embedding to existing speaker or register new one.

        Returns (speaker_label: str, confidence: float).
        """
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
                # Update centroid with running average
                spk = speakers[best_idx]
                n = spk["count"]
                new_centroid = (spk["centroid"] * n + embedding) / (n + 1)
                new_centroid = new_centroid / (np.linalg.norm(new_centroid) + 1e-8)
                spk["centroid"] = new_centroid
                spk["count"] = n + 1
                label = f"speaker_{best_idx + 1}"
                return label, best_sim
            else:
                # Register new speaker
                speakers.append({"centroid": embedding.copy(), "count": 1})
                label = f"speaker_{len(speakers)}"
                return label, 1.0

    def _start_cleanup_thread(self):
        def cleanup():
            while True:
                time.sleep(300)  # every 5 minutes
                cutoff = time.time() - self.SESSION_TTL
                with self._lock:
                    expired = [sid for sid, s in self._sessions.items() if s["last_active"] < cutoff]
                    for sid in expired:
                        del self._sessions[sid]

        t = threading.Thread(target=cleanup, daemon=True)
        t.start()
