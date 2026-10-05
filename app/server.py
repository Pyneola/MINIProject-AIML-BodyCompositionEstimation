import os

import joblib
from fastapi import FastAPI

app = FastAPI(
    title="Body Composition Estimator API",
    description="Estimates Fat % (XGBoost), Lean mass and ALM (Ridge) from body measurements, and screens for low muscle mass (Logistic Regression)."
)

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "../models"))

_state = {}


def load():
    if not _state:
        path = os.path.join(MODELS_DIR, "model_bundle.joblib")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Model file not found in {MODELS_DIR}. Run notebooks/02_modeling.ipynb.")
        _state["bundle"] = joblib.load(path)
    return _state


@app.get("/health")
def server_health():
    try:
        load()
        models_saved, error_msg = True, None
    except Exception as e:
        models_saved, error_msg = False, str(e)
    return {
        "status": "healthy",
        "models_status": "loaded" if models_saved else "missing",
        "error": error_msg,
        "paths": {"models": MODELS_DIR},
    }
