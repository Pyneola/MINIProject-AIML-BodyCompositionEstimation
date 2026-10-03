"""Real-label dataset: NHANES 2017-18 adults 18-59 with measured DXA, body measures, diet, sleep, activity."""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"

BASIC = ["RIAGENDR", "RIDAGEYR", "BMXWT", "BMXHT", "BMXBMI"]
CIRC = ["BMXWAIST", "BMXHIP", "BMXARMC", "BMXARML", "BMXLEG"]



def build():
    demo = pd.read_sas(RAW / "DEMO_J.XPT")[["SEQN", "RIAGENDR", "RIDAGEYR"]]
    bmx = pd.read_sas(RAW / "BMX_J.XPT")[["SEQN", "BMXWT", "BMXHT", "BMXBMI"] + CIRC]
    dxx = pd.read_sas(RAW / "DXX_J.xpt")[["SEQN", "DXDTOFAT", "DXDTOLE", "DXDTOBMC", "DXDLALE", "DXDRALE", "DXDLLLE", "DXDRLLE"]]

    d = demo.merge(bmx, on="SEQN").merge(dxx, on="SEQN")
    n_adults = int(((d.RIDAGEYR >= 18) & (d.RIDAGEYR <= 59)).sum())
    d = d[(d.RIDAGEYR >= 18) & (d.RIDAGEYR <= 59)].copy()

    d["ALM_KG"] = (d.DXDLALE + d.DXDRALE + d.DXDLLLE + d.DXDRLLE) / 1000
    d["FAT_KG"] = d.DXDTOFAT / 1000
    d["LEAN_KG"] = d.DXDTOLE / 1000
    d["FAT_PCT"] = d.DXDTOFAT / (d.DXDTOFAT + d.DXDTOLE + d.DXDTOBMC) * 100
    need = ["ALM_KG", "FAT_KG", "LEAN_KG", "FAT_PCT"] + BASIC + CIRC
    d = d.dropna(subset=need).copy()

    cols = ["SEQN"] + BASIC + CIRC + ["FAT_PCT", "FAT_KG", "LEAN_KG", "ALM_KG"]
    return d[cols].reset_index(drop=True), n_adults

