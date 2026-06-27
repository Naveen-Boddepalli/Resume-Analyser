import os
import pandas as pd
import joblib
import shap
import pytest


def test_shap_basic():
    model_path = os.path.join(
        os.path.dirname(__file__), "../models/placement_model.pkl"
    )
    if not os.path.exists(model_path):
        pytest.skip("Model file not found")

    model = joblib.load(model_path)
    X_df = pd.DataFrame(
        [
            {
                "cgpa": 8.5,
                "internships_count": 1,
                "projects_count": 3,
                "coding_skill_score": 100,
                "communication_skill_score": 80,
                "leadership_score": 50,
                "college_tier": "Tier 1",
                "branch": "CSE",
            }
        ]
    )

    try:
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_df)
        prob = model.predict_proba(X_df)
        assert prob is not None
    except Exception as e:
        pytest.fail(f"SHAP explainer failed: {e}")
