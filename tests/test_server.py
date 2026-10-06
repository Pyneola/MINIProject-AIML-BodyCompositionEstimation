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
