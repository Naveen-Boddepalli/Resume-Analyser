import shap
import pandas as pd

def get_shap_values(model, X_df: pd.DataFrame) -> dict:
    if model is None:
        return {"strengths": [], "weaknesses": []}
        
    try:
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_df)
        
        feature_names = X_df.columns.tolist()
        impacts = shap_values[0]
        
        name_map = {
            'cgpa': 'CGPA',
            'internships_count': 'Internships',
            'projects_count': 'Projects',
            'coding_skill_score': 'Coding Skills',
            'communication_skill_score': 'Communication',
            'leadership_score': 'Leadership'
        }
        
        features_impact = []
        for i, name in enumerate(feature_names):
            features_impact.append({
                "name": name_map.get(name, name),
                "impact": float(impacts[i])
            })
            
        features_impact.sort(key=lambda x: abs(x["impact"]), reverse=True)
        
        strengths = [f for f in features_impact if f["impact"] > 0]
        weaknesses = [f for f in features_impact if f["impact"] < 0]
        
        return {
            "strengths": strengths,
            "weaknesses": weaknesses
        }
    except Exception as e:
        print("SHAP Error:", e)
        return {"strengths": [], "weaknesses": []}
