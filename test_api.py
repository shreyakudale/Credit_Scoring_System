import requests
import json

# Test the credit score predictor API
url = "http://localhost:5000/api/predict"

# Test with customer_id 1
data = {"customer_id": 3}
try:
    response = requests.post(url, json=data, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")

    if response.status_code == 200:
        result = response.json()
        print("✅ API call successful")
        print(f"Predicted Score: {result.get('predicted_score', 'N/A')}")
        print(f"Data Sufficiency: {result.get('data_sufficiency', 'N/A')}")
    else:
        print("❌ API call failed")
except Exception as e:
    print(f"Error: {e}")
