"""Breadth screen: which recurring Kalshi series are priced least efficiently?

Stage 1 (this module's `list_series_markets`): settled markets per series.
Stage 2 (`candles_at_leads`): quotes at fixed lead times before close.
Stage 3 (`evaluate`): fee-aware P&L of simple rules, day-clustered inference, FDR-corrected."""
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import pandas as pd
from .http import get_json
from .sources.kalshi import BASE

FREQS = ("daily", "weekly", "hourly")
KEEP = ["series", "ticker", "event_ticker", "open_time", "close_time", "result", "volume", "strike_type",
        "floor_strike", "cap_strike", "last_price_dollars", "yes_sub_title"]


def candidate_series(catalog_csv="data/series_catalog.csv", exclude_categories=("Sports",)):
    s = pd.read_csv(catalog_csv)
    s = s[s["frequency"].isin(FREQS) & ~s["category"].isin(exclude_categories)]
    return s[["ticker", "title", "category", "frequency", "fee_type", "fee_multiplier"]].reset_index(drop=True)


def list_series_markets(series, max_pages=2):
    """Most recent settled markets for a series (up to max_pages x 1000), live then historical."""
    rows = []
    for path in ("markets", "historical/markets"):
        cur = None
        for _ in range(max_pages):
            p = {"series_ticker": series, "limit": 1000}
            if path == "markets":
                p["status"] = "settled"
            if cur:
                p["cursor"] = cur
            try:
                d = get_json(f"{BASE}/{path}", p)
            except Exception:
                break
            rows += [dict(m, series=series) for m in d.get("markets", [])]
            cur = d.get("cursor")
            if not cur or not d.get("markets"):
                break
        if len(rows) >= 300:      # enough history; skip the historical endpoint
            break
    if not rows:
        return pd.DataFrame(columns=KEEP)
    df = pd.DataFrame(rows).drop_duplicates("ticker")
    df = df[df["result"].isin(["yes", "no"])].copy()
    df["volume"] = pd.to_numeric(df.get("volume_fp", df.get("volume")), errors="coerce")
    for c in KEEP:
        if c not in df:
            df[c] = np.nan
    return df[KEEP]


def list_all(series_list, workers=3):
    with ThreadPoolExecutor(workers) as ex:
        parts = list(ex.map(list_series_markets, series_list))
    return pd.concat([p for p in parts if len(p)], ignore_index=True)


def rank_series(markets, catalog, min_volume=20):
    m = markets.copy()
    m["liquid"] = m["volume"] >= min_volume
    g = m.groupby("series").agg(n=("ticker", "size"), n_liquid=("liquid", "sum"), total_volume=("volume", "sum"),
                                median_volume=("volume", "median"), yes_rate=("result", lambda r: (r == "yes").mean()),
                                first=("close_time", "min"), last=("close_time", "max"))
    return g.join(catalog.set_index("ticker")[["title", "category", "frequency", "fee_multiplier"]]).sort_values(
        "n_liquid", ascending=False)
