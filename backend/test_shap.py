
import pandas as pd
import joblib
import shap


model = joblib.load('/Users/boddepallinaveen/Resume-Analyser/models/placement_model.pkl')
X_df = pd.DataFrame([{
    "cgpa": 8.5,
    "internships_count": 1,
    "projects_count": 3,
    "coding_skill_score": 100,
    "communication_skill_score": 80,
    "leadership_score": 50,
    "college_tier": "Tier 1",
    "branch": "CSE"
}])

# some dummy preprocessing if needed, wait, model uses pipeline or directly?
try:
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_df)
    print("type of shap_values:", type(shap_values))
    if isinstance(shap_values, list):
        print("list length:", len(shap_values))
        print("shape of shap_values[0]:", shap_values[0].shape)
        if len(shap_values) > 1:
            print("shape of shap_values[1]:", shap_values[1].shape)
    else:
        print("shape of shap_values:", shap_values.shape)
        
    print("expected_value:", explainer.expected_value)
    
    prob = model.predict_proba(X_df)
    print("predict_proba:", prob)
except Exception as e:
    print("Error:", e)
