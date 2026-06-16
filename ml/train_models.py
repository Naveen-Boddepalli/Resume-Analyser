import os
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from catboost import CatBoostClassifier, CatBoostRegressor
import joblib

def main():
    # Paths
    data_path = '../data/student_placement_prediction_dataset_2026.csv'
    models_dir = '../models'
    
    os.makedirs(models_dir, exist_ok=True)
    
    print("Loading data...")
    df = pd.read_csv(data_path)
    
    # Features and targets
    features = ['cgpa', 'internships_count', 'projects_count', 'coding_skill_score', 'communication_skill_score', 'leadership_score']
    
    df['placement_status'] = df['placement_status'].map({'Not Placed': 0, 'Placed': 1})
    
    X = df[features]
    y_class = df['placement_status']
    
    print("Training placement status classifiers...")
    # Train classifiers
    lr = LogisticRegression(random_state=42, max_iter=1000)
    lr.fit(X, y_class)
    
    rf = RandomForestClassifier(random_state=42)
    rf.fit(X, y_class)
    
    cb_class = CatBoostClassifier(verbose=0, random_state=42)
    cb_class.fit(X, y_class)
    
    # Save CatBoost classifier
    placement_model_path = os.path.join(models_dir, 'placement_model.pkl')
    joblib.dump(cb_class, placement_model_path)
    print(f"Saved placement model to {placement_model_path}")
    
    # Salary Regressor (only placed candidates)
    print("Training salary regressors...")
    df_placed = df[df['placement_status'] == 1]
    X_placed = df_placed[features]
    y_salary = df_placed['salary_package_lpa']
    
    # CatBoost Regressor - Low (alpha=0.25)
    cb_reg_low = CatBoostRegressor(loss_function='Quantile:alpha=0.25', verbose=0, random_state=42)
    cb_reg_low.fit(X_placed, y_salary)
    
    salary_low_path = os.path.join(models_dir, 'salary_low_model.pkl')
    joblib.dump(cb_reg_low, salary_low_path)
    print(f"Saved low salary model to {salary_low_path}")
    
    # CatBoost Regressor - High (alpha=0.75)
    cb_reg_high = CatBoostRegressor(loss_function='Quantile:alpha=0.75', verbose=0, random_state=42)
    cb_reg_high.fit(X_placed, y_salary)
    
    salary_high_path = os.path.join(models_dir, 'salary_high_model.pkl')
    joblib.dump(cb_reg_high, salary_high_path)
    print(f"Saved high salary model to {salary_high_path}")

if __name__ == "__main__":
    main()
