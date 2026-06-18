import shap
import numpy as np
import pandas as pd

def get_shap_values(model, X_df: pd.DataFrame) -> dict:
    if model is None:
        return {"strengths": [], "weaknesses": [], "base_value": 0.5, "waterfall": []}
        
    try:
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_df)
        
        feature_names = X_df.columns.tolist()
        impacts = shap_values[0]
        
        # Extract base_value (expected_value) for the positive class
        ev = explainer.expected_value
        if isinstance(ev, (np.ndarray, list)):
            base_value = float(ev[1])
        else:
            base_value = float(ev)
        
        name_map = {
            'cgpa': 'CGPA',
            'internships_count': 'Internships',
            'projects_count': 'Projects',
            'coding_skill_score': 'Coding Skills',
            'communication_skill_score': 'Communication',
            'leadership_score': 'Leadership'
        }
        
        # Convert base_value (log-odds) to base probability
        import math
        def sigmoid(x):
            # bound x to avoid overflow
            x = max(min(x, 100), -100)
            return 1 / (1 + math.exp(-x))
            
        base_prob = sigmoid(base_value)
        
        # We need to map the impacts from log-odds to probability
        # Sort impacts by absolute magnitude first to build the waterfall properly
        features_list = []
        for i, name in enumerate(feature_names):
            features_list.append({
                "name": name,
                "raw_impact": float(impacts[i]),
                "value": str(X_df.iloc[0][name])
            })
            
        # Sort by absolute raw impact
        features_list.sort(key=lambda x: abs(x["raw_impact"]), reverse=True)
        
        # Calculate probability impacts cumulatively
        current_margin = base_value
        waterfall = []
        strengths = []
        weaknesses = []
        
        for feat in features_list:
            next_margin = current_margin + feat["raw_impact"]
            prob_impact = sigmoid(next_margin) - sigmoid(current_margin)
            current_margin = next_margin
            
            display_name = name_map.get(feat["name"], feat["name"])
            
            # Format for waterfall
            waterfall.append({
                "name": display_name,
                "impact": prob_impact,
                "value": feat["value"]
            })
            
            # For strengths/weaknesses, we can just use the prob_impact
            item = {
                "name": display_name,
                "impact": prob_impact
            }
            if prob_impact > 0:
                strengths.append(item)
            elif prob_impact < 0:
                weaknesses.append(item)
                
        return {
            "strengths": strengths,
            "weaknesses": weaknesses,
            "base_value": base_prob,
            "waterfall": waterfall
        }
    except Exception as e:
        print("SHAP Error:", e)
        return {"strengths": [], "weaknesses": [], "base_value": 0.5, "waterfall": []}
