# QICS Python Backend + Data Analysis (Pandas, SQL, Power BI)

This converts your QICS demo into a Python FastAPI backend with Pandas/Numpy analysis and SQL storage. It mirrors the front-end APIs and is ready to connect with Power BI.

## Endpoints
- `GET /api/dms/search?vin=VIN` – Returns VIN quality docs.
- `POST /api/dms/upload` – Upload a doc (multipart).
- `GET /api/dpc-data` – DPC data as CSV.
- `GET /api/dpc-monitoring?from=YYYY-MM-DD&to=YYYY-MM-DD` – DPC JSON.
- `GET /api/rsp?from=YYYY-MM-DD&to=YYYY-MM-DD` – RSP cumulative.
- `POST /api/defects/compare` – Compare defects with last working day.
- `POST /api/dpc/import` – Import DPC CSV.

## Run
```
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt

python -m app.seeds
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000/docs for Swagger UI.

## Switch DB for Power BI
Use MySQL/PostgreSQL for DirectQuery:
```
set DATABASE_URL=mysql+pymysql://user:pass@localhost:3306/qics   # Windows
export DATABASE_URL=mysql+pymysql://user:pass@localhost:3306/qics # Linux/Mac
```
Create DB first. Re-run `python -m app.seeds`.

## Power BI
### A) Direct DB (recommended)
- Get Data → MySQL (or PostgreSQL) → DirectQuery → select `dpc_records`, `rsp_records`, `vehicles`, `quality_docs`.

### B) Web (API)
- DPC CSV: `http://localhost:8000/api/dpc-data`
- RSP JSON: `http://localhost:8000/api/rsp?from=2025-08-01&to=2025-08-25`

**Power Query for DPC CSV**
```m
let
  Source = Csv.Document(Web.Contents("http://localhost:8000/api/dpc-data"), [Delimiter=",", Columns=4, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
  AsTable = Table.FromRows(Source, {"VIN","Model","DPC Target (%)","DPC Actual (%)"}),
  Types = Table.TransformColumnTypes(AsTable, {{"DPC Target (%)", type number}, {"DPC Actual (%)", type number}})
in
  Types
```

**Power Query for RSP JSON**
```m
let
  Source = Json.Document(Web.Contents("http://localhost:8000/api/rsp?from=2025-08-01&to=2025-08-25")),
  Rows = Source[rows],
  Table = Table.FromRecords(Rows),
  Types = Table.TransformColumnTypes(Table, {{"target", type number}, {"actual", type number}, {"date", type date}})
in
  Types
```

## CSV Import
```
python scripts/load_dpc_csv.py data/sample_dpc.csv
```
"# qics" 
"# qics" 
