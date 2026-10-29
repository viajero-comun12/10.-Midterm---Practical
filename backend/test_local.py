"""Automated integration tests for the URL Shortener API.
Can be executed locally with: python test_local.py
"""
import sys
import os
import uuid

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Force mock DB for local test run if AWS credentials are not present
os.environ["USE_MOCK_DB"] = "true"

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    print("\n--- 1. Testing Health Check Endpoint ---")
    response = client.get("/health")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    print("Health response:", data)
    assert data["status"] == "healthy"
    print("PASS: Health check OK")


def test_shorten_valid_url():
    print("\n--- 2. Testing URL Shortening (POST /shorten) ---")
    target_url = "https://www.example.com/articulos/arquitectura-cloud"
    response = client.post("/shorten", json={"original_url": target_url})
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    data = response.json()
    print("Shorten response:", data)

    assert "short_code" in data
    assert "original_url" in data
    assert "short_url" in data
    assert data["original_url"] == target_url

    # Verify UUID validity
    short_code = data["short_code"]
    val = uuid.UUID(short_code, version=4)
    assert str(val) == short_code
    print(f"PASS: Generated valid UUID v4: {short_code}")
    return short_code, target_url


def test_shorten_invalid_url():
    print("\n--- 3. Testing Validation on Invalid URL ---")
    response = client.post("/shorten", json={"original_url": "invalid-url-without-scheme"})
    assert response.status_code == 422, f"Expected 422 for invalid URL, got {response.status_code}"
    print("PASS: Rejected invalid URL as expected")


def test_url_info(short_code: str, expected_url: str):
    print(f"\n--- 4. Testing URL Info Query (GET /urls/{short_code}) ---")
    response = client.get(f"/urls/{short_code}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    print("Info response:", data)
    assert data["short_code"] == short_code
    assert data["original_url"] == expected_url
    assert "created_at" in data
    print("PASS: URL metadata retrieved successfully")


def test_redirect(short_code: str, expected_url: str):
    print(f"\n--- 5. Testing HTTP Redirection (GET /{short_code}) ---")
    # We do NOT follow redirects so we can inspect status code 307 and Location header
    response = client.get(f"/{short_code}", follow_redirects=False)
    assert response.status_code == 307, f"Expected 307 Temporary Redirect, got {response.status_code}"
    location = response.headers.get("location")
    print(f"Redirect status: {response.status_code}, Location: {location}")
    assert location == expected_url, f"Expected redirect to {expected_url}, got {location}"
    print("PASS: Backend correctly responds with 307 Temporary Redirect to original URL")


def test_not_found():
    print("\n--- 6. Testing 404 for Non-Existent UUID ---")
    fake_code = str(uuid.uuid4())
    resp_redirect = client.get(f"/{fake_code}", follow_redirects=False)
    assert resp_redirect.status_code == 404, f"Expected 404, got {resp_redirect.status_code}"

    resp_info = client.get(f"/urls/{fake_code}")
    assert resp_info.status_code == 404, f"Expected 404, got {resp_info.status_code}"
    print("PASS: 404 returned correctly for non-existent codes")


if __name__ == "__main__":
    print("=" * 60)
    print("RUNNING URL SHORTENER API TEST SUITE")
    print("=" * 60)
    try:
        test_health()
        code, original = test_shorten_valid_url()
        test_shorten_invalid_url()
        test_url_info(code, original)
        test_redirect(code, original)
        test_not_found()
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED SUCCESSFULLY! (6/6)")
        print("=" * 60)
    except AssertionError as e:
        print(f"\nTEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUNEXPECTED ERROR: {e}")
        sys.exit(1)
