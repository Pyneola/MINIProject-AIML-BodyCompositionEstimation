# ประมาณเปอร์เซ็นต์ไขมันและมวลกล้ามเนื้อของร่างกายจากค่าวัดร่างกาย ด้วย Machine Learning

โมเดลรับเพศ อายุ น้ำหนัก ส่วนสูง และเส้นรอบวงของร่างกาย (10 ค่า) แล้วประมาณเปอร์เซ็นต์ไขมันและมวลกล้ามเนื้อให้ใกล้เคียงผลสแกน DXA โดยไม่ต้องสแกน ใช้ข้อมูลสแกน DXA จริงของผู้ใหญ่ 2,310 คนจาก NHANES 2017-18 และต่อยอดเป็นการคัดกรองผู้ที่มีมวลกล้ามเนื้อต่ำ

## ผลหลัก (Test set 462 คน)

| ค่าที่ประมาณ | Model | R² | MAE ก่อน train → หลัง train |
|---|---|---|---|
| ไขมัน (%) | XGBoost | 0.84 | 7.20 → 2.75 จุด (สูตร Deurenberg 4.61) |
| มวลกล้ามเนื้อทั้งตัว | Ridge | 0.95 | 10.49 → 2.24 กก. |
| มวลกล้ามเนื้อแขน+ขา (ALM) | Ridge | 0.93 | 5.26 → 1.34 กก. |
| มวลกล้ามเนื้อลำตัว | Ridge | 0.93 | 5.10 → 1.29 กก. |

คัดกรองผู้ที่มีมวลกล้ามเนื้อต่ำด้วย Logistic Regression (เกณฑ์ ALM/ส่วนสูง²) แนะนำตรวจซ้ำ 18% ของคน Recall 91% Precision 51% F1 0.66

## โครงสร้าง

| ส่วน | ที่อยู่ |
|---|---|
| สำรวจข้อมูลและปัญหา DXA ขาด | `notebooks/01_nhanes_exploration.ipynb` |
| เปรียบเทียบ algorithm วัดผล และเลือก model | `notebooks/02_modeling.ipynb` |
| สร้างชุดข้อมูล | `src/real_label.py` |
| เว็บแอปสาธิต (FastAPI) และการทดสอบ | `app/`, `tests/` |
| model ที่สอนเสร็จ และตัวเลขผล | `models/` |
| ข้อมูลดิบ NHANES | `data/raw/` |

## วิธีรัน

```
pip install -r requirements.txt
python src/real_label.py          # สร้าง data/processed/nhanes_real_dxa.csv
# รัน notebooks/02_modeling.ipynb  # เปรียบเทียบ train วัดผล บันทึกลง models/
python -m pytest                  # ทดสอบ API
cd app && uvicorn server:app      # เดโม http://127.0.0.1:8000
```

ทดสอบด้วย Python 3.12

## ข้อมูล

NHANES 2017-2018 (CDC / NCHS, https://www.cdc.gov/nchs/nhanes/) ใช้ไฟล์ DEMO_J, BMX_J, DXX_J, DR1TOT_J, SLQ_J, PAQ_J ที่อยู่ใน `data/raw/`

