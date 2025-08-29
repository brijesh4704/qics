from app.database import Base, engine, SessionLocal
from app.models import Vehicle, DPCRecord, RSPRecord, QualityDoc
from datetime import date, timedelta, datetime
import random, os, shutil

def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    vins = [("1HGCM82633A123456","City"), ("2HGFB2F5XEH123789","Amaze")]
    for vin, model in vins:
        if not db.query(Vehicle).filter_by(vin=vin).first():
            db.add(Vehicle(vin=vin, model=model))
    db.commit()

    today = date.today()
    start = today - timedelta(days=29)
    for i in range(30):
        d = start + timedelta(days=i)
        tgt = random.randint(95,98)
        act = tgt - random.randint(0,3)
        db.add(RSPRecord(date=d, target=tgt, actual=act))
    db.commit()

    for vin, model in vins:
        for i in range(30):
            d = start + timedelta(days=i)
            tgt = random.randint(92,97)
            act = tgt - random.uniform(0,5)
            db.add(DPCRecord(vin=vin, model=model, date=d, dpc_target=tgt, dpc_actual=round(act,1)))
    db.commit()

    os.makedirs("data/docs", exist_ok=True)
    for vin, model in vins:
        for name in ["cvic_inspection.pdf","doublecheck.jpg","portreturn.pdf"]:
            src = os.path.join("data/docs", name)
            if not os.path.exists(src):
                with open(src, "wb") as f: f.write(b"Placeholder")
            rel = f"{vin}_{name}"
            dst = os.path.join("data/docs", rel)
            if not os.path.exists(dst): shutil.copy(src, dst)
            from sqlalchemy import select
            v = db.execute(select(Vehicle).where(Vehicle.vin==vin)).scalar_one()
            db.add(QualityDoc(vehicle_id=v.id, title=name.split('.')[0].replace('_',' ').title(), type=("PDF" if name.endswith(".pdf") else "Image"), path=rel, uploaded_at=datetime.utcnow()))
    db.commit()
    db.close()
    print("Seeded database.")

if __name__ == "__main__":
    run()
