"""Real-label dataset: NHANES 2017-18 adults 18-59 with measured DXA, body measures, diet, sleep, activity."""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed" / "nhanes_real_dxa.csv"

BASIC = ["RIAGENDR", "RIDAGEYR", "BMXWT", "BMXHT", "BMXBMI"]
CIRC = ["BMXWAIST", "BMXHIP", "BMXARMC", "BMXARML", "BMXLEG"]
LIFE = ["DR1TKCAL", "DR1TPROT", "SLD012", "PAQ605", "PAQ620", "PAQ635", "PAQ650", "PAQ665", "PAD680"]

FNIH_CUT = {1.0: 0.789, 2.0: 0.512}
HT2_CUT = {1.0: 7.0, 2.0: 5.5}


def build():
    demo = pd.read_sas(RAW / "DEMO_J.XPT")[["SEQN", "RIAGENDR", "RIDAGEYR"]]
    bmx = pd.read_sas(RAW / "BMX_J.XPT")[["SEQN", "BMXWT", "BMXHT", "BMXBMI"] + CIRC]
    dxx = pd.read_sas(RAW / "DXX_J.xpt")[["SEQN", "DXDTOFAT", "DXDTOLE", "DXDTOBMC", "DXDLALE", "DXDRALE", "DXDLLLE", "DXDRLLE"]]
    diet = pd.read_sas(RAW / "DR1TOT_J.XPT")
    diet = diet[diet.DR1DRSTZ == 1][["SEQN", "DR1TKCAL", "DR1TPROT"]]
    sleep = pd.read_sas(RAW / "SLQ_J.XPT")[["SEQN", "SLD012"]]
    pa = pd.read_sas(RAW / "PAQ_J.XPT")[["SEQN", "PAQ605", "PAQ620", "PAQ635", "PAQ650", "PAQ665", "PAD680"]]

    d = (demo.merge(bmx, on="SEQN").merge(dxx, on="SEQN").merge(diet, on="SEQN", how="left")
         .merge(sleep, on="SEQN", how="left").merge(pa, on="SEQN", how="left"))
    n_adults = int(((d.RIDAGEYR >= 18) & (d.RIDAGEYR <= 59)).sum())
    d = d[(d.RIDAGEYR >= 18) & (d.RIDAGEYR <= 59)].copy()

    d["ALM_KG"] = (d.DXDLALE + d.DXDRALE + d.DXDLLLE + d.DXDRLLE) / 1000
    d["FAT_KG"] = d.DXDTOFAT / 1000
    d["LEAN_KG"] = d.DXDTOLE / 1000
    d["FAT_PCT"] = d.DXDTOFAT / (d.DXDTOFAT + d.DXDTOLE + d.DXDTOBMC) * 100
    need = ["ALM_KG", "FAT_KG", "LEAN_KG", "FAT_PCT"] + BASIC + CIRC
    d = d.dropna(subset=need).copy()

    for c in ["PAQ605", "PAQ620", "PAQ635", "PAQ650", "PAQ665"]:
        d[c] = (d[c] == 1).astype(float)
    d["PAD680"] = d.PAD680.where(d.PAD680 < 9000)

    d["LOW_FNIH"] = (d.ALM_KG / d.BMXBMI < d.RIAGENDR.map(FNIH_CUT)).astype(int)
    d["LOW_HT2"] = (d.ALM_KG / (d.BMXHT / 100) ** 2 < d.RIAGENDR.map(HT2_CUT)).astype(int)
    cols = ["SEQN"] + BASIC + CIRC + LIFE + ["FAT_PCT", "FAT_KG", "LEAN_KG", "ALM_KG", "LOW_FNIH", "LOW_HT2"]
    return d[cols].reset_index(drop=True), n_adults


if __name__ == "__main__":
    df, n = build()
    df.to_csv(OUT, index=False)
    print(f"adults 18-59: {n} -> complete DXA + body measures: {len(df)}")
    print("LOW_FNIH", int(df.LOW_FNIH.sum()), "LOW_HT2", int(df.LOW_HT2.sum()))
