# test_ner_pipeline.py
from fastapi.testclient import TestClient
from main import app
import pytest
from datetime import datetime

# Fixture to provide a TestClient instance with module scope
@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

# Test health endpoint
def test_health_check(client):
    response = client.get("/pii/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ["healthy", "not_ready"]
    assert "model_initialized" in data
    assert "timestamp" in data
    assert isinstance(datetime.fromisoformat(data["timestamp"]), datetime)

# Fixture to provide sample text with PII for testing
@pytest.fixture(params=[
    "Aiguo Wagner, phone 0666 335 6493, email aiguo_wagner2235@outlook.gov, LinkedIn @aiguo.wagner",
    "John Doe lives at 1234 Main St, phone 555-123-4567, email john.doe@gmail.com",
])
def pii_text(request):
    return request.param

# Fixture to provide empty or invalid text for edge cases
@pytest.fixture(params=["", "   "])
def invalid_text(request):
    return request.param

# Parameterized tests for detect endpoint with various PII inputs
@pytest.mark.parametrize("text", [
    "Aiguo Wagner, phone 0666 335 6493, email aiguo_wagner2235@outlook.gov, LinkedIn @aiguo.wagner",
    "Jane Smith, address 40404 Jeremy Brook, username @janesmith",
    "Contact me at 0777 444 9999 or email test.user@test.com",
])
def test_detect_pii(client, text):
    response = client.post("/pii/detect", json={"text": text})
    assert response.status_code == 200
    data = response.json()
    assert "text" in data
    assert "entities" in data
    entities = data["entities"]
    assert len(entities) > 0
    assert any(ent["entity_group"] in ["NAME_STUDENT", "PHONE_NUM", "EMAIL", "USERNAME", "STREET_ADDRESS"] for ent in entities)

# Parameterized tests for detect endpoint with invalid inputs
@pytest.mark.parametrize("text", ["", "   "])
def test_detect_invalid_input(client, text):
    response = client.post("/pii/detect", json={"text": text})
    assert response.status_code == 400
    assert response.json()["detail"] == "Input text cannot be empty"

# Parameterized tests for mask endpoint with various PII inputs
@pytest.mark.parametrize("text", [
    "Aiguo Wagner, phone 0666 335 6493, email aiguo_wagner2235@outlook.gov, LinkedIn @aiguo.wagner",
    "Jane Smith lives at 40404 Jeremy Brook, username @janesmith",
    "Call me at 0777 444 9999 or email test.user@test.com",
])
def test_mask_pii(client, text):
    response = client.post("/pii/mask", json={"text": text})
    assert response.status_code == 200
    data = response.json()
    assert "original_text" in data
    assert "masked_text" in data
    masked_text = data["masked_text"]
    assert "[NAME_STUDENT]" in masked_text or "[PHONE_NUM]" in masked_text or "[EMAIL]" in masked_text or "[USERNAME]" in masked_text or "[STREET_ADDRESS]" in masked_text

# Parameterized tests for mask endpoint with invalid inputs
@pytest.mark.parametrize("text", ["", "   "])
def test_mask_invalid_input(client, text):
    response = client.post("/pii/mask", json={"text": text})
    assert response.status_code == 400
    assert response.json()["detail"] == "Input text cannot be empty"

# Test detect endpoint with no PII (benign text)
@pytest.mark.parametrize("text", [
    "Hello, how are you today?",
    "The weather is nice on September 30, 2025.",
    "I like to read books.",
])
def test_detect_benign_text(client, text):
    response = client.post("/pii/detect", json={"text": text})
    assert response.status_code == 200
    data = response.json()
    assert "entities" in data
    assert len(data["entities"]) == 0

# Test mask endpoint with no PII (benign text)
@pytest.mark.parametrize("text", [
    "Hello, how are you today?",
    "The weather is nice on September 30, 2025.",
    "I like to read books.",
])
def test_mask_benign_text(client, text):
    response = client.post("/pii/mask", json={"text": text})
    assert response.status_code == 200
    data = response.json()
    assert data["original_text"] == data["masked_text"]

