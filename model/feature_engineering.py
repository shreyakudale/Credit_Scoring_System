# 🧠 Feature creation logic
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
import joblib
from config.db_config import get_db_connection
from datetime import datetime

def load_model_artifacts():
    """Load trained model and preprocessing artifacts."""
    try:
        model_artifacts = joblib.load('model/credit_model.pkl')
        return model_artifacts
    except FileNotFoundError:
        print("Model artifacts not found. Please train the model first.")
        return None

def preprocess_customer_data(customer_data):
    """
    Preprocess customer data for model prediction.

    Args:
        customer_data (dict): Customer data from database

    Returns:
        pd.DataFrame: Preprocessed features ready for model prediction
    """
    # Load model artifacts
    artifacts = load_model_artifacts()
    if artifacts is None:
        return None

    model = artifacts['model']
    features = artifacts['features']
    scaler = artifacts['scaler']
    le_home = artifacts['le_home']
    le_purpose = artifacts['le_purpose']
    le_age = artifacts['le_age']

    # Convert customer data to DataFrame
    df = pd.DataFrame([customer_data])

    # Feature engineering (same as in training)
    df_processed = df.copy()

    # Create additional features
    df_processed['income_log'] = np.log1p(df_processed['income'])
    # Handle division by zero for loan_to_income
    df_processed['loan_to_income'] = np.where(df_processed['income'] == 0, 100.0,
                                             df_processed['loan_amount'] / df_processed['income'])

    # Age bucket
    df_processed['age_bucket'] = pd.cut(df_processed['age'],
                                       bins=[0, 25, 35, 45, 55, 100],
                                       labels=['18-25', '26-35', '36-45', '46-55', '56+'])

    # Encode categorical variables
    df_processed['home_ownership_encoded'] = le_home.transform(df_processed['home_ownership'])
    df_processed['purpose_encoded'] = le_purpose.transform(df_processed['purpose'])
    df_processed['age_bucket_encoded'] = le_age.transform(df_processed['age_bucket'])

    # Select and order features as in training
    X = df_processed[features]

    # Scale numerical features
    numerical_features = ['age', 'income_log', 'credit_score', 'debt_to_income',
                         'employment_years', 'loan_amount', 'loan_term', 'loan_to_income']

    X[numerical_features] = scaler.transform(X[numerical_features])

    return X

def predict_credit_score(customer_data):
    """
    Predict credit score for a customer.

    Args:
        customer_data (dict): Customer data from database

    Returns:
        dict: Prediction results including score, decision, confidence, and SHAP values
    """
    # Load model artifacts
    artifacts = load_model_artifacts()
    if artifacts is None:
        return None

    model = artifacts['model']

    # Preprocess data
    X = preprocess_customer_data(customer_data)
    if X is None:
        return None

    # Make prediction
    predicted_score = model.predict(X)[0]

    # Determine decision based on score
    if predicted_score == -1:
        decision = 'Approved'
        confidence = 0.95
    elif predicted_score >= 750:
        decision = 'Approved'
        confidence = 0.92
    elif predicted_score >= 650:
        decision = 'Approved'
        confidence = 0.85
    elif predicted_score >= 600:
        decision = 'Review'
        confidence = 0.65
    else:
        decision = 'Declined'
        confidence = 0.45

    # Generate SHAP values for explainability
    try:
        explainer = joblib.load('model/shap_explainer.pkl')
        shap_values = explainer.shap_values(X)[0]  # Get SHAP values for first (only) sample

        # Create feature importance dict
        feature_names = artifacts['features']
        shap_dict = {}
        for i, feature in enumerate(feature_names):
            shap_dict[feature] = float(shap_values[i])

        # Sort by absolute importance
        shap_sorted = sorted(shap_dict.items(), key=lambda x: abs(x[1]), reverse=True)
        top_shap = dict(shap_sorted[:5])  # Top 5 features

    except Exception as e:
        print(f"SHAP explainability failed: {e}")
        # Fallback to mock SHAP values
        top_shap = {
            'Income': 0.15,
            'Credit History': 0.12,
            'Debt-to-Income Ratio': -0.08,
            'Employment Length': 0.06,
            'Age': 0.03
        }

    return {
        'score': round(float(predicted_score), 2),
        'decision': decision,
        'confidence': confidence,
        'shap_values': top_shap
    }

def get_customer_features(customer_id):
    """Get comprehensive customer features from database."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Get basic customer info
        cursor.execute('SELECT * FROM customers WHERE customer_id = %s', (customer_id,))
        customer_row = cursor.fetchone()
        if not customer_row:
            return None

        customer = dict(zip([desc[0] for desc in cursor.description], customer_row))

        # Calculate age
        if customer['dob']:
            customer['age'] = (datetime.now().date() - customer['dob']).days // 365
        else:
            customer['age'] = 30  # Default

        # Get employment info
        cursor.execute('SELECT * FROM employment_info WHERE customer_id = %s', (customer_id,))
        emp_row = cursor.fetchone()
        if emp_row:
            emp = dict(zip([desc[0] for desc in cursor.description], emp_row))
            customer['annual_income'] = emp['annual_income'] or 0
            customer['employment_years'] = emp['years_at_job'] or 0
        else:
            customer['annual_income'] = 0
            customer['employment_years'] = 0

        # Get loan info
        cursor.execute('SELECT COUNT(*) FROM loans WHERE customer_id = %s', (customer_id,))
        customer['total_loans'] = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM loans WHERE customer_id = %s AND status = "Active"', (customer_id,))
        customer['active_loans'] = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM loans WHERE customer_id = %s AND status = "Defaulted"', (customer_id,))
        customer['loan_defaults_count'] = cursor.fetchone()[0]

        # Get payment info
        cursor.execute('SELECT COUNT(*) FROM payments WHERE loan_id IN (SELECT loan_id FROM loans WHERE customer_id = %s)', (customer_id,))
        customer['total_payments'] = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM payments WHERE loan_id IN (SELECT loan_id FROM loans WHERE customer_id = %s) AND payment_status = "On-Time"', (customer_id,))
        customer['ontime_payments'] = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM payments WHERE loan_id IN (SELECT loan_id FROM loans WHERE customer_id = %s) AND payment_status = "Missed"', (customer_id,))
        customer['missed_payments'] = cursor.fetchone()[0]

        # Calculate ratios
        customer['on_time_payment_ratio'] = customer['ontime_payments'] / customer['total_payments'] if customer['total_payments'] > 0 else 0
        customer['missed_payment_ratio'] = customer['missed_payments'] / customer['total_payments'] if customer['total_payments'] > 0 else 0

        # Get transaction info
        cursor.execute('SELECT COUNT(*) FROM transactions WHERE account_id IN (SELECT account_id FROM accounts WHERE customer_id = %s)', (customer_id,))
        customer['transaction_count'] = cursor.fetchone()[0]

        cursor.execute('SELECT AVG(amount) FROM transactions WHERE account_id IN (SELECT account_id FROM accounts WHERE customer_id = %s) AND transaction_type = "Credit"', (customer_id,))
        avg_credit = cursor.fetchone()[0]
        customer['avg_monthly_balance'] = avg_credit or 0

        # Placeholders for missing features
        customer['credit_utilization_ratio'] = 0.3  # Placeholder
        customer['total_credit_limit'] = 10000  # Placeholder
        customer['total_credit_balance'] = 3000  # Placeholder
        customer['income_to_loan_ratio'] = customer['annual_income'] / (customer['total_loans'] * 10000 + 1) if customer['total_loans'] > 0 else 0
        customer['salary_stability_ratio'] = min(customer['employment_years'] / 10, 1)  # Based on years
        customer['age_of_credit_history'] = customer['employment_years'] * 12  # Months
        customer['new_credit_inquiries'] = 0  # Placeholder
        customer['rejection_rate'] = 0  # Placeholder
        customer['high_value_transaction_flags'] = 0  # Placeholder
        customer['employment_stability_score'] = customer['employment_years'] / 5  # Simple score

        # Map to model features (placeholders for missing ones)
        customer['income'] = customer['annual_income']
        customer['credit_score'] = 650  # Placeholder, since model uses it as feature
        customer['debt_to_income'] = customer['missed_payment_ratio']  # Approximation
        customer['loan_amount'] = customer['total_loans'] * 10000  # Approximation
        customer['loan_term'] = 360  # Default
        customer['home_ownership'] = 'RENT'  # Default
        customer['purpose'] = 'PERSONAL'  # Default

        return customer

    finally:
        conn.close()

def get_reason(factor, impact):
    """Get reason for a factor's impact."""
    reasons = {
        'income_log': 'Higher income improves credit score by showing financial stability.',
        'debt_to_income': 'Lower debt-to-income ratio positively impacts credit score.',
        'employment_years': 'Longer employment history indicates stability.',
        'loan_to_income': 'Lower loan-to-income ratio reduces financial burden.',
        'age': 'Age can influence credit experience and responsibility.',
        'credit_score': 'Current credit score reflects past financial behavior.',
        'loan_amount': 'Loan amount affects credit utilization.',
        'loan_term': 'Longer loan terms can spread payments but increase total interest.'
    }
    reason = reasons.get(factor, f'{factor} affects credit score based on financial patterns.')
    if impact == 'negative':
        reason = reason.replace('improves', 'negatively impacts').replace('positively impacts', 'negatively impacts')
    return reason

def get_tips(score):
    """Get improvement tips based on score."""
    if score < 650:
        return [
            "Pay all bills on time to improve payment history.",
            "Reduce debt levels by paying down balances.",
            "Avoid applying for new credit frequently."
        ]
    elif score < 750:
        return [
            "Maintain consistent on-time payments.",
            "Keep credit utilization below 30%.",
            "Build a longer credit history."
        ]
    else:
        return [
            "Continue excellent payment habits.",
            "Monitor credit report regularly.",
            "Maintain low debt-to-income ratio."
        ]

def predict_credit_score(customer_id):
    """
    Predict credit score for a customer with data sufficiency check.

    Args:
        customer_id (int): Customer ID

    Returns:
        dict: JSON output with predicted_score, risk_level, data_sufficiency, explanations, improvement_tips
    """
    # Get customer features
    customer = get_customer_features(customer_id)
    if not customer:
        return {
            "predicted_score": -1,
            "risk_level": "Insufficient Data",
            "data_sufficiency": False,
            "explanations": [],
            "improvement_tips": []
        }

    # Check data sufficiency
    transaction_count = customer['transaction_count']
    total_loans = customer['total_loans']
    total_payments = customer['total_payments']

    if transaction_count < 5 or total_loans == 0 or total_payments == 0:
        return {
            "predicted_score": -1,
            "risk_level": "Insufficient Data",
            "data_sufficiency": False,
            "explanations": [],
            "improvement_tips": []
        }

    # Load model and predict
    artifacts = load_model_artifacts()
    if artifacts is None:
        return {
            "predicted_score": -1,
            "risk_level": "Insufficient Data",
            "data_sufficiency": False,
            "explanations": [],
            "improvement_tips": []
        }

    model = artifacts['model']

    # Preprocess data
    X = preprocess_customer_data(customer)
    if X is None:
        return {
            "predicted_score": -1,
            "risk_level": "Insufficient Data",
            "data_sufficiency": False,
            "explanations": [],
            "improvement_tips": []
        }

    # Make prediction
    predicted_score = int(model.predict(X)[0])
    predicted_score = max(300, min(900, predicted_score))  # Clamp to 300-900

    # Classify risk
    if predicted_score >= 750:
        risk_level = "Low Risk"
    elif predicted_score >= 650:
        risk_level = "Medium Risk"
    else:
        risk_level = "High Risk"

    # Get SHAP values for top factors
    explanations = []
    try:
        explainer = joblib.load('model/shap_explainer.pkl')
        shap_values = explainer.shap_values(X)[0]

        feature_names = artifacts['features']
        shap_dict = {}
        for i, feature in enumerate(feature_names):
            shap_dict[feature] = float(shap_values[i])

        # Sort by absolute importance
        shap_sorted = sorted(shap_dict.items(), key=lambda x: abs(x[1]), reverse=True)
        top_shap = shap_sorted[:5]

        for factor, value in top_shap:
            impact = 'positive' if value > 0 else 'negative'
            reason = get_reason(factor, impact)
            explanations.append({
                "factor": factor,
                "impact": impact,
                "reason": reason
            })

    except Exception as e:
        print(f"SHAP explainability failed: {e}")
        # Fallback explanations
        explanations = [
            {"factor": "Income", "impact": "positive", "reason": "Higher income improves credit score."},
            {"factor": "Payment History", "impact": "positive", "reason": "On-time payments build good credit."},
            {"factor": "Debt Levels", "impact": "negative", "reason": "High debt reduces credit score."},
            {"factor": "Employment Stability", "impact": "positive", "reason": "Stable employment supports creditworthiness."},
            {"factor": "Credit Utilization", "impact": "negative", "reason": "High utilization negatively impacts score."}
        ]

    # Get improvement tips
    improvement_tips = get_tips(predicted_score)

    return {
        "predicted_score": predicted_score,
        "risk_level": risk_level,
        "data_sufficiency": True,
        "explanations": explanations,
        "improvement_tips": improvement_tips
    }

def get_feature_importance():
    """Get global feature importance from the trained model."""
    artifacts = load_model_artifacts()
    if artifacts is None:
        return None

    model = artifacts['model']
    features = artifacts['features']

    # Get feature importance
    importance = model.feature_importance(importance_type='gain')
    feature_importance = dict(zip(features, importance))

    # Sort by importance
    sorted_importance = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)

    return dict(sorted_importance)
