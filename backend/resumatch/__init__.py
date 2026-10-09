"""EviMatch: evidence-grounded, bias-audited resume-job matching."""

from .embed import CachedEmbedder, Embedder, HashingEmbedder, SentenceTransformerEmbedder
from .features import ALL_FEATURES, FEATURE_GROUPS, FEATURE_NAMES, IDENTITY_FEATURES, CorpusStats
from .model import CLASSES, DECISIONS, FitModel, fit_score
from .pipeline import VERSION, EviMatch
from .redact import RedactionReport, redact
from .skills import SkillLexicon

__all__ = [
    "ALL_FEATURES",
    "IDENTITY_FEATURES",
    "CLASSES",
    "DECISIONS",
    "FEATURE_GROUPS",
    "FEATURE_NAMES",
    "VERSION",
    "CachedEmbedder",
    "CorpusStats",
    "Embedder",
    "EviMatch",
    "FitModel",
    "HashingEmbedder",
    "RedactionReport",
    "SentenceTransformerEmbedder",
    "SkillLexicon",
    "fit_score",
    "redact",
]
