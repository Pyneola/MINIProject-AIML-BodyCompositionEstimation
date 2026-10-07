import os

import joblib
import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

app = FastAPI(
    title="Body Composition Estimator API",
    description="Estimates Fat % (XGBoost), Lean mass and ALM (Ridge) from body measurements, and screens for low muscle mass (Logistic Regression)."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:8000"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
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


# bounds are the min and max in the training data, outside them the estimate is unreliable
class EstimateRequest(BaseModel):
    RIAGENDR: float = Field(..., ge=1.0, le=2.0, description="Sex: 1 = Male, 2 = Female")
    RIDAGEYR: float = Field(..., ge=18.0, le=59.0, description="Age (18 to 59 years)")
    BMXWT: float = Field(..., ge=36.0, le=177.0, description="Weight (36 to 177 kg)")
    BMXHT: float = Field(..., ge=138.0, le=191.0, description="Height (138 to 191 cm)")
    BMXWAIST: float = Field(..., ge=56.0, le=155.0, description="Waist circumference (56 to 155 cm)")
    BMXHIP: float = Field(..., ge=77.0, le=169.0, description="Hip circumference (77 to 169 cm)")
    BMXARMC: float = Field(..., ge=20.0, le=53.0, description="Arm circumference (20 to 53 cm)")
    BMXARML: float = Field(..., ge=29.0, le=46.0, description="Upper arm length (29 to 46 cm)")
    BMXLEG: float = Field(..., ge=26.0, le=50.0, description="Upper leg length (26 to 50 cm)")


@app.post("/predict")
def estimate(payload: EstimateRequest):
    try:
        st = load()
    except Exception as e:
        return {"success": False, "error": str(e)}
    bundle = st["bundle"]
    d = payload.model_dump()
    d["BMXBMI"] = d["BMXWT"] / (d["BMXHT"] / 100) ** 2
    df = pd.DataFrame([[d[f] for f in bundle["features"]]], columns=bundle["features"])
    est = {t: float(m.predict(df)[0]) for t, m in bundle["regressors"].items()}
    ridge = {t: float(m.predict(df)[0]) for t, m in bundle["ridge"].items()}

    alm = est["ALM_KG"]
    almi = alm / (d["BMXHT"] / 100) ** 2
    alm_bmi = alm / d["BMXBMI"]
    screen = {}
    for lab in ("LOW_HT2", "LOW_FNIH"):
        p = float(bundle["classifiers"][lab].predict_proba(df)[0, 1])
        screen[lab] = {"probability": float(p),
                       "refer_sens90": bool(p >= bundle["thresholds"][lab]["0.9"]),
                       "refer_sens80": bool(p >= bundle["thresholds"][lab]["0.8"])}
    return {
        "success": True,
        "source": "AI_MODEL",
        "bmi": d["BMXBMI"],
        "fatPct": est["FAT_PCT"], "leanKg": est["LEAN_KG"], "almKg": est["ALM_KG"], "trunkKg": est["TRUNK_KG"],
        "almi": almi, "almPerBmi": alm_bmi,
        "ridge": {"fatPct": ridge["FAT_PCT"], "leanKg": ridge["LEAN_KG"], "almKg": ridge["ALM_KG"], "trunkKg": ridge["TRUNK_KG"]},
        "testMae": {"fatPct": bundle["test_mae"]["FAT_PCT"], "leanKg": bundle["test_mae"]["LEAN_KG"], "almKg": bundle["test_mae"]["ALM_KG"], "trunkKg": bundle["test_mae"]["TRUNK_KG"]},
        "screen": screen,
    }


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


# mounted last so the API routes match first
app.mount("/", StaticFiles(directory=CURRENT_DIR, html=True), name="frontend")
