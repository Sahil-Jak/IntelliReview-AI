import requests
import time
import json
import sys

URL = "http://127.0.0.1:8000/review-code"

payload = {
    "code": """def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

print(add(5, 3))
print(subtract(10, 4))""",
    "language": "Python"
}


def test_review_api():
    """Test the /review-code endpoint."""
    print("=" * 50)
    print("IntelliReview API Test")
    print("=" * 50)
    print(f"\nTarget: {URL}")
    print("Sending request...\n")

    try:
        start_time = time.time()
        response = requests.post(URL, json=payload, timeout=30)
        elapsed = round(time.time() - start_time, 2)

        print(f"Status Code: {response.status_code}")
        print(f"Response Time: {elapsed} seconds\n")

        if response.status_code != 200:
            print(f"ERROR: Expected 200, got {response.status_code}")
            print(f"Response: {response.text}")
            sys.exit(1)

        data = response.json()
        print("Response JSON:\n")
        print(json.dumps(data, indent=4))

        # Validate response structure (multi-dimensional scores)
        required_keys = [
            "readability", "performance", "maintainability",
            "security", "best_practices", "overall_score",
            "issues", "ai_explanation", "fixed_code"
        ]
        missing = [k for k in required_keys if k not in data]
        if missing:
            print(f"\nWARNING: Missing keys in response: {missing}")
        else:
            print("\n✅ All required fields present!")

        # Check overall score
        score = data.get("overall_score", 0)
        if isinstance(score, (int, float)) and 0 <= score <= 10:
            print(f"✅ Overall score: {score}/10")
        else:
            print(f"⚠️  Overall score: {score} (unexpected value)")

        # Show dimension scores
        dims = ["readability", "performance", "maintainability", "security", "best_practices"]
        print("\n📊 Dimension Scores:")
        for d in dims:
            val = data.get(d, "N/A")
            print(f"   {d:20s} → {val}/10")

        # Token usage
        tokens = data.get("token_usage")
        if tokens:
            print(f"\n🔢 Token usage: {tokens}")

    except requests.ConnectionError:
        print("ERROR: Cannot connect to server. Is it running?")
        print("Start it with: uvicorn main:app --reload")
        sys.exit(1)
    except requests.Timeout:
        print("ERROR: Request timed out after 30 seconds.")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    test_review_api()