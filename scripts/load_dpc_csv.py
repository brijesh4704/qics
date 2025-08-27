import sys, pandas as pd
from sqlalchemy import create_engine

def main(csv_path, db_url='sqlite:///./qics.db'):
    df = pd.read_csv(csv_path)
    required = {'VIN','Model','Date','DPC Target (%)','DPC Actual (%)'}
    if not required.issubset(df.columns):
        raise SystemExit(f"CSV must include columns: {sorted(required)}")
    df['Date'] = pd.to_datetime(df['Date']).dt.date
    engine = create_engine(db_url, future=True)
    df.rename(columns={'Date':'date', 'DPC Target (%)':'dpc_target', 'DPC Actual (%)':'dpc_actual', 'VIN':'vin', 'Model':'model'}, inplace=True)
    df.to_sql('dpc_records', engine, if_exists='append', index=False)
    print(f"Loaded {len(df)} rows into dpc_records")

if __name__ == '__main__':
    main(sys.argv[1])
