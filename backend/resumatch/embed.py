"""Sentence embedders behind one small interface, with an optional disk cache."""

from __future__ import annotations

import hashlib
import pickle
import re
from pathlib import Path
from typing import Protocol

import numpy as np

from .text import tokenize


class Embedder(Protocol):
    name: str

    def encode(self, texts: list[str]) -> np.ndarray:
        """Return L2-normalised float32 embeddings, shape ``(len(texts), dim)``."""


class SentenceTransformerEmbedder:
    """Wraps a ``sentence-transformers`` model (loaded lazily)."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", max_seq_length: int = 128):
        self.model_name = model_name
        self.name = f"{model_name}@{max_seq_length}"
        self.max_seq_length = max_seq_length
        self._model = None

    def _load(self):  # pragma: no cover - needs model download
        if self._model is None:
            import torch
            from sentence_transformers import SentenceTransformer

            device = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")
            self._model = SentenceTransformer(self.model_name, device=device)
            self._model.max_seq_length = self.max_seq_length
        return self._model

    def encode(self, texts: list[str]) -> np.ndarray:  # pragma: no cover - needs model download
        if not texts:
            return np.zeros((0, 1), dtype=np.float32)
        emb = self._load().encode(texts, batch_size=128, normalize_embeddings=True, show_progress_bar=False)
        return np.asarray(emb, dtype=np.float32)


class HashingEmbedder:
    """Dependency-free bag-of-words embedder used for tests and offline demos.

    It is *not* a semantic model: it only gives lexical overlap in a dense
    vector so the pipeline can be exercised without a model download.
    """

    def __init__(self, dim: int = 256):
        self.name = f"hashing-{dim}"
        self.dim = dim

    def encode(self, texts: list[str]) -> np.ndarray:
        out = np.zeros((len(texts), self.dim), dtype=np.float32)
        for row, text in enumerate(texts):
            for tok in tokenize(text):
                h = int(hashlib.md5(tok.encode(), usedforsecurity=False).hexdigest(), 16)
                out[row, h % self.dim] += 1.0 if (h >> 20) & 1 else -1.0
            norm = np.linalg.norm(out[row])
            if norm:
                out[row] /= norm
        return out


class CachedEmbedder:
    """Persist embeddings by content hash so experiments are re-runnable."""

    def __init__(self, inner: Embedder, cache_dir: str | Path):
        self.inner = inner
        self.name = inner.name
        self.path = Path(cache_dir) / (re.sub(r"[^\w.-]+", "_", inner.name) + ".pkl")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._store: dict[str, np.ndarray] = {}
        self._dirty = False
        if self.path.exists():
            with open(self.path, "rb") as fh:
                self._store = pickle.load(fh)  # nosec B301 - local cache we wrote

    @staticmethod
    def _key(text: str) -> str:
        return hashlib.sha1(text.encode("utf-8"), usedforsecurity=False).hexdigest()

    def encode(self, texts: list[str]) -> np.ndarray:
        keys = [self._key(t) for t in texts]
        missing = sorted({k: t for k, t in zip(keys, texts) if k not in self._store}.items())
        if missing:
            vecs = self.inner.encode([t for _, t in missing])
            for (k, _), v in zip(missing, vecs):
                self._store[k] = v
            self._dirty = True
        if not texts:
            return np.zeros((0, 1), dtype=np.float32)
        return np.stack([self._store[k] for k in keys])

    def save(self) -> None:
        if self._dirty:
            with open(self.path, "wb") as fh:
                pickle.dump(self._store, fh)
            self._dirty = False
