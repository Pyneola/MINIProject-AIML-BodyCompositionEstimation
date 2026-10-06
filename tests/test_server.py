import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from fastapi.testclient import TestClient
from server import app

client = TestClient(app)

VALID_PAYLOAD = {
    "RIAGENDR": 1.0,
    "RIDAGEYR": 30,
    "BMXWT": 75,
    "BMXHT": 172,
    "BMXWAIST": 88,
    "BMXHIP": 100,
    "BMXARMC": 31,
    "BMXARML": 37,
    "BMXLEG": 39,
}


def test_health_reports_models_loaded():
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "healthy"
    assert body["models_status"] == "loaded"


def test_predict_valid_input_returns_estimates():
    resp = client.post("/predict", json=VALID_PAYLOAD)
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["source"] == "AI_MODEL"
    assert 5 < body["fatPct"] < 60
    assert 20 < body["leanKg"] < 90
    assert 5 < body["almKg"] < 45
    assert 5 < body["trunkKg"] < 60
    assert 0 <= body["screen"]["LOW_HT2"]["probability"] <= 1
