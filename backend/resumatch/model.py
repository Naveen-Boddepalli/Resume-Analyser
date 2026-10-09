"""Fit classifier with prior-corrected decisions and occlusion attributions."""

from __future__ import annotations

from typing import Sequence

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .features import FEATURE_GROUPS, FEATURE_NAMES

CLASSES = ("No Fit", "Potential Fit", "Good Fit")
DECISIONS = ("Reject", "Review", "Shortlist")


def fit_score(proba: np.ndarray) -> np.ndarray:
    """Expected graded relevance rescaled to 0-100 (Good=1, Potential=0.5)."""
    proba = np.atleast_2d(proba)
    return 100.0 * (proba[:, 2] + 0.5 * proba[:, 1])


class FitModel:
    """Three-class model over a fixed feature list.

    Probabilities are trained *without* class re-weighting so they stay
    calibrated to the training base rate. Decisions divide by the prior, which
    is the Bayes rule for balanced accuracy and keeps minority classes visible.
    """

    def __init__(
        self,
        kind: str = "logreg",
        feature_names: Sequence[str] | None = None,
        C: float = 0.3,
        max_depth: int = 3,
        learning_rate: float = 0.05,
        max_iter: int = 150,
        seed: int = 13,
    ):
        self.kind = kind
        self.feature_names = list(feature_names or FEATURE_NAMES)
        self.params = {"C": C, "max_depth": max_depth, "learning_rate": learning_rate, "max_iter": max_iter}
        self.seed = seed
        self.pipeline: Pipeline | None = None
        self.prior = np.full(3, 1 / 3)
        self.means: np.ndarray | None = None

    def _make(self) -> Pipeline:
        if self.kind == "logreg":
            clf = LogisticRegression(C=self.params["C"], max_iter=5000, random_state=self.seed)
        elif self.kind == "gbm":
            clf = HistGradientBoostingClassifier(
                max_depth=self.params["max_depth"],
                learning_rate=self.params["learning_rate"],
                max_iter=self.params["max_iter"],
                random_state=self.seed,
            )
        else:
            raise ValueError(f"unknown model kind {self.kind!r}")
        return Pipeline([("scale", StandardScaler()), ("clf", clf)])

    def fit(self, X: np.ndarray, y: np.ndarray) -> "FitModel":
        self.pipeline = self._make().fit(X, y)
        counts = np.bincount(y, minlength=3).astype(float)
        self.prior = counts / counts.sum()
        self.means = X.mean(0)
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        assert self.pipeline is not None, "model is not fitted"
        P = np.zeros((len(X), 3))
        P[:, self.pipeline.classes_.astype(int)] = self.pipeline.predict_proba(X)
        return P

    def decide(self, proba: np.ndarray) -> np.ndarray:
        return np.argmax(np.atleast_2d(proba) / self.prior, axis=1)

    def score(self, X: np.ndarray) -> np.ndarray:
        return fit_score(self.predict_proba(X))

    def occlusion(self, x: np.ndarray) -> dict[str, float]:
        """Change in fit score when one feature is replaced by its training mean.

        Positive values mean the feature raised this candidate's score. The
        method is model agnostic, deterministic and needs no extra library.
        """
        assert self.means is not None
        base = float(self.score(x[None, :])[0])
        variants = np.tile(x, (len(x), 1))
        idx = np.arange(len(x))
        variants[idx, idx] = self.means
        drops = base - self.score(variants)
        return {n: float(d) for n, d in zip(self.feature_names, drops)}

    def group_contributions(self, x: np.ndarray) -> dict[str, float]:
        occ = self.occlusion(x)
        return {g: float(sum(occ[f] for f in fs if f in occ)) for g, fs in FEATURE_GROUPS.items()}
