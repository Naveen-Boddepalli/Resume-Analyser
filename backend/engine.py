"""Lazy singleton for the EviMatch scoring engine."""

from __future__ import annotations

import os
import threading
from pathlib import Path

from resumatch import EviMatch, HashingEmbedder, SentenceTransformerEmbedder
from resumatch.pipeline import DEFAULT_ARTIFACT

_lock = threading.Lock()
_engine: EviMatch | None = None


def build_engine(artifact: str | Path = DEFAULT_ARTIFACT, embedder_kind: str | None = None) -> EviMatch:
    kind = (embedder_kind or os.getenv("EVIMATCH_EMBEDDER", "minilm")).lower()
    if kind == "hashing":
        # Lexical stand-in for offline demos and tests. NOT what the artefact was trained with.
        embedder = HashingEmbedder(256)
    else:
        embedder = SentenceTransformerEmbedder("sentence-transformers/all-MiniLM-L6-v2", 128)
    return EviMatch.load(embedder, artifact)


def get_engine() -> EviMatch:
    global _engine
    with _lock:
        if _engine is None:
            _engine = build_engine()
        return _engine


def set_engine(engine: EviMatch | None) -> None:
    """Override the engine (used by tests)."""
    global _engine
    with _lock:
        _engine = engine
