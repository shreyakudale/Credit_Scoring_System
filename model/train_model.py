# 🧩 Script to train LightGBM/ML model
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import joblib
import shap
import os
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import StandardScaler, LabelEncoder
import warnings
warnings.filterwarnings('ignore')

def generate_synthetic_data(n_samples=10000):
    """Generate synthetic credit scoring data for training."""
    np.random.seed(42)

    # Generate features
    data = {
        'age': np.random.normal(40, 10, n_samples).clip(18, 80),
        'income': np.random.lognormal(11, 0.5, n_samples),  # Mean ~60k
        'credit_score': np.random.normal(650, 100, n_samples).clip(300, 850),
        'debt_to_income': np.random.beta(2, 5, n_samples),  # Skewed towards lower values
        'employment_years': np.random.exponential(5, n_samples).clip(0, 40),
        'loan_amount': np.random.lognormal(12, 0.8, n_samples),  # Mean ~150k
        'loan_term': np.random.choice([120, 180, 240, 360], n_samples),
        'home_ownership': np.random.choice(['RENT', 'MORTGAGE', 'OWN'], n_samples, p=[0.3, 0.5, 0.2]),
        'purpose': np.random.choice(['DEBTCONSOLIDATION', 'HOMEIMPROVEMENT', 'PERSONAL', 'CREDITCARD', 'BUSINESS'],
                                   n_samples, p=[0.4, 0.2, 0.15, 0.15, 0.1])
    }

    df = pd.DataFrame(data)

    # Create target variable (credit risk score)
    # Higher score = lower risk (better credit)
    risk_factors = (
        -0.3 * (df['age'] - 40) / 10 +  # Age factor
        0.4 * (df['income'] - 60000) / 30000 +  # Income factor
        0.6 * (df['credit_score'] - 650) / 100 +  # Credit score factor
        -0.5 * df['debt_to_income'] +  # Debt-to-income factor
        0.2 * df['employment_years'] / 10 +  # Employment stability
        np.random.normal(0, 0.3, n_samples)  # Random noise
    )

    # Convert to score between 300-850
    df['target_score'] = (650 + risk_factors * 100).clip(300, 850)

    # Create categorical target for classification
    df['risk_category'] = pd.cut(df['target_score'],
                                bins=[0, 580, 670, 740, 850],
                                labels=['High Risk', 'Medium Risk', 'Low Risk', 'Very Low Risk'])

    return df

def preprocess_data(df):
    """Preprocess data for model training."""
    # Feature engineering
    df_processed = df.copy()

    # Create additional features
    df_processed['income_log'] = np.log1p(df_processed['income'])
    df_processed['loan_to_income'] = df_processed['loan_amount'] / df_processed['income']
    df_processed['age_bucket'] = pd.cut(df_processed['age'], bins=[0, 25, 35, 45, 55, 100],
                                       labels=['18-25', '26-35', '36-45', '46-55', '56+'])

    # Encode categorical variables
    le_home = LabelEncoder()
    le_purpose = LabelEncoder()
    le_age = LabelEncoder()

    df_processed['home_ownership_encoded'] = le_home.fit_transform(df_processed['home_ownership'])
    df_processed['purpose_encoded'] = le_purpose.fit_transform(df_processed['purpose'])
    df_processed['age_bucket_encoded'] = le_age.fit_transform(df_processed['age_bucket'])

    # Select features for model
    features = [
        'age', 'income_log', 'credit_score', 'debt_to_income', 'employment_years',
        'loan_amount', 'loan_term', 'home_ownership_encoded', 'purpose_encoded',
        'loan_to_income', 'age_bucket_encoded'
    ]

    # Scale numerical features
    scaler = StandardScaler()
    numerical_features = ['age', 'income_log', 'credit_score', 'debt_to_income',
                         'employment_years', 'loan_amount', 'loan_term', 'loan_to_income']

    df_processed[numerical_features] = scaler.fit_transform(df_processed[numerical_features])

    return df_processed, features, scaler, le_home, le_purpose, le_age

def train_model():
    """Train the credit scoring model."""
    print("Generating synthetic training data...")
    df = generate_synthetic_data(10000)

    print("Preprocessing data...")
    df_processed, features, scaler, le_home, le_purpose, le_age = preprocess_data(df)

    # Prepare target for regression (predict credit score)
    X = df_processed[features]
    y = df_processed['target_score']

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print("Training Random Forest model...")
    # Train Random Forest model
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1
    )

    model.fit(X_train, y_train)

    # Evaluate model
    y_pred = model.predict(X_test)
    rmse = np.sqrt(np.mean((y_test - y_pred)**2))
    print(".2f")

    # Create SHAP explainer
    print("Creating SHAP explainer...")
    explainer = shap.TreeExplainer(model)
    shap_values_sample = explainer.shap_values(X_test.head(100))

    # Save model and artifacts
    print("Saving model and artifacts...")
    os.makedirs('model', exist_ok=True)

    model_artifacts = {
        'model': model,
        'features': features,
        'scaler': scaler,
        'le_home': le_home,
        'le_purpose': le_purpose,
        'le_age': le_age,
        'rmse': rmse
    }

    joblib.dump(model_artifacts, 'model/credit_model.pkl')
    joblib.dump(explainer, 'model/shap_explainer.pkl')

    print("Model training completed successfully!")
    print(f"Model saved to: model/credit_model.pkl")
    print(f"SHAP explainer saved to: model/shap_explainer.pkl")

    return model_artifacts

if __name__ == "__main__":
    train_model()
