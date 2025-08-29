from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse, StreamingResponse, PlainTextResponse
from sqlalchemy.orm import Session
from datetime import date, datetime
import io, csv, os
import pandas as pd

from database import Base, engine, SessionLocal
from models import Vehicle, DPCRecord, RSPRecord, QualityDoc
from analysis import rsp_cumulative, last_working_day, defect_comparison

app = FastAPI(title="QICS Python Backend", version="1.0.0")

# --------------- DB init ---------------
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --------------- Health ---------------
@app.get("/api/health")
def health():
    return {"ok": True}

# --------------- VIN docs search ---------------
@app.get("/api/dms/search")
def search_docs(vin: str, db: Session = Depends(get_db)):
    v = db.query(Vehicle).filter_by(vin=vin).first()
    docs = []
    if v:
        for d in v.docs:
            docs.append({"title": d.title, "type": d.type, "url": f"/docs/{d.path}"})
    return {"docs": docs}

# --------------- Serve docs (dev only) ---------------
@app.get("/docs/{path:path}")
def get_doc(path: str):
    full = os.path.join("data/docs", path)
    if not os.path.exists(full): raise HTTPException(404, "File not found")
    import mimetypes
    mt, _ = mimetypes.guess_type(full)
    return StreamingResponse(open(full, "rb"), media_type=mt or "application/octet-stream")

# --------------- Upload a doc ---------------
@app.post("/api/dms/upload")
async def upload_doc(vin: str = Form(...), title: str = Form(...), dtype: str = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db)):
    v = db.query(Vehicle).filter_by(vin=vin).first()
    if not v:
        v = Vehicle(vin=vin, model="UNKNOWN")
        db.add(v); db.commit(); db.refresh(v)
    # save file
    safe_name = f"{vin}_{int(datetime.utcnow().timestamp())}_{file.filename}".replace("/", "_")
    dest_dir = "data/docs"
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, safe_name)
    with open(dest_path, "wb") as f:
        f.write(await file.read())
    doc = QualityDoc(vehicle_id=v.id, title=title, type=dtype, path=safe_name, uploaded_at=datetime.utcnow())
    db.add(doc); db.commit()
    return {"ok": True, "path": safe_name}

# --------------- DPC CSV endpoint (to match front-end demo) ---------------
@app.get("/api/dpc-data", response_class=PlainTextResponse)
def dpc_data_csv(db: Session = Depends(get_db)):
    rows = db.query(DPCRecord).order_by(DPCRecord.date.desc()).all()
    output = io.StringIO()
    w = csv.writer(output)
    w.writerow(["VIN","Model","DPC Target (%)","DPC Actual (%)"])
    for r in rows:
        w.writerow([r.vin, r.model, f"{r.dpc_target}", f"{r.dpc_actual}"])
    return output.getvalue()

# --------------- DPC monitoring (JSON, date range) ---------------
@app.get("/api/dpc-monitoring")
def dpc_monitoring(from_: str, to: str, db: Session = Depends(get_db)):
    try:
        start = pd.to_datetime(from_).date()
        end = pd.to_datetime(to).date()
    except Exception:
        raise HTTPException(400, "Invalid dates")
    q = db.query(DPCRecord).filter(DPCRecord.date>=start, DPCRecord.date<=end).all()
    return {"data": [{
        "vin": r.vin, "model": r.model, "dpc_target": r.dpc_target, "dpc_actual": r.dpc_actual, "date": r.date.isoformat()
    } for r in q]}

# --------------- RSP cumulative ---------------
@app.get("/api/rsp")
def rsp(from_: str, to: str, db: Session = Depends(get_db)):
    start = pd.to_datetime(from_).date()
    end = pd.to_datetime(to).date()
    df = pd.read_sql(db.query(RSPRecord).statement, db.bind)
    if df.empty:
        return {"summary": {"days":0, "cum_target":0, "cum_actual":0, "achievement_pct":0.0}, "rows":[]}
    df['date'] = pd.to_datetime(df['date'])
    res = rsp_cumulative(df, start, end)
    return {"summary": {k: res[k] for k in ['days','cum_target','cum_actual','achievement_pct']}, "rows": res['rows']}

# --------------- Defect comparison helper ---------------
@app.post("/api/defects/compare")
def compare(payload: dict):
    ref = pd.to_datetime(payload.get("referenceDate")).date()
    holidays = set(payload.get("holidays", []))
    last_day = last_working_day(ref, holidays)
    rows = defect_comparison(payload.get("today", {}), payload.get("previous", {}))
    return {"referenceDate": ref.isoformat(), "lastWorkingDay": last_day.isoformat(), "rows": rows}

# --------------- CSV ingest for DPC ---------------
@app.post("/api/dpc/import")
async def dpc_import(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    import io as _io
    df = pd.read_csv(_io.BytesIO(content))
    required = {"VIN","Model","Date","DPC Target (%)","DPC Actual (%)"}
    if not required.issubset(df.columns):
        raise HTTPException(400, f"CSV must include columns: {sorted(required)}")
    df['Date'] = pd.to_datetime(df['Date']).dt.date
    for _, row in df.iterrows():
        db.add(DPCRecord(vin=row['VIN'], model=row['Model'], date=row['Date'],
                         dpc_target=float(row['DPC Target (%)']), dpc_actual=float(row['DPC Actual (%)'])))
    db.commit()
    return {"ok": True, "rows": int(df.shape[0])}
