import pandas as pd
import numpy as np
from datetime import date, timedelta

def rsp_cumulative(df: pd.DataFrame, start: date, end: date) -> dict:
    # Calculate cumulative RSP between dates (inclusive).
    # Input df has columns ['date','target','actual'] with date dtype.
    mask = (df['date']>=pd.to_datetime(start)) & (df['date']<=pd.to_datetime(end))
    subset = df.loc[mask].copy()
    subset['date_str'] = subset['date'].dt.strftime('%Y-%m-%d')
    cum_target = float(subset['target'].sum())
    cum_actual = float(subset['actual'].sum())
    achievement = 0.0 if cum_target == 0 else round(cum_actual/cum_target*100, 2)
    rows = subset[['date_str','target','actual']].rename(columns={'date_str':'date'})
    return {
        'days': int(subset.shape[0]),
        'cum_target': cum_target,
        'cum_actual': cum_actual,
        'achievement_pct': achievement,
        'rows': rows.to_dict(orient='records')
    }

def last_working_day(ref: date, holidays: set[str] | None = None) -> date:
    holidays = holidays or set()
    d = ref - timedelta(days=1)
    while True:
        if d.weekday() < 5 and d.strftime('%Y-%m-%d') not in holidays:
            return d
        d = d - timedelta(days=1)

def defect_comparison(defects_today: dict[str,int], defects_prev: dict[str,int]) -> list[dict]:
    keys = sorted(set(defects_today) | set(defects_prev))
    rows = []
    for k in keys:
        a = int(defects_prev.get(k, 0))
        b = int(defects_today.get(k, 0))
        rows.append({'defect': k, 'prev': a, 'today': b, 'diff': b - a})
    return rows
