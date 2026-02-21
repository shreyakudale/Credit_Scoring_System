import requests
import json

# Test the credit score predictor
url = "http://localhost:5000/api/predict"

# Test with customer_id 1
data = {"customer_id": 1}
response = requests.post(url, json=data)

if response.status_code == 200:
    result = response.json()
    print("Prediction result:")
    print(json.dumps(result, indent=2))

    # Validate structure
    required_keys = ["predicted_score", "risk_level", "data_sufficiency", "explanations", "improvement_tips"]
    if all(key in result for key in required_keys):
        print("✅ JSON structure is correct")
    else:
        print("❌ JSON structure is incorrect")

    # Check data sufficiency
    if result["data_sufficiency"]:
        print(f"Score: {result['predicted_score']}, Risk: {result['risk_level']}")
        print(f"Top factors: {len(result['explanations'])}")
        print(f"Tips: {len(result['improvement_tips'])}")
    else:
        print("Insufficient data as expected")
else:
    print(f"Error: {response.status_code}, {response.text}")
