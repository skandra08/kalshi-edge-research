# kalshi-edge-research

Quantitative research on **prediction-market pricing**: where Kalshi's prices are efficient,
where they are not, and whether any gap survives fees. Everything is tested on real settled
outcomes with event-clustered inference and walk-forward (never in-sample) evaluation.

## Projects

### 1. `digitaledge`: pricing BTC "above $X" contracts off options and vol models
Kalshi's hourly Bitcoin contracts are digital options. This project prices them from first
principles and scores the result against the market on settled outcomes.
- **Vol models (walk-forward):** HAR-RV with intraday seasonality, EWMA, Deribit DVOL; Gaussian,
  Student-t and empirical tails.
- **Microstructure details:** Kalshi settles on a 60-second average of the index, which shortens
  the effective variance horizon by 2/3 minute; this is modelled explicitly.
- **Options surface:** SVI smile fit to Deribit's live chain; skew-aware digital price
  `N(d2) - vega * d(sigma)/dK`, checked against finite-difference `-dC/dK` and a butterfly
  no-arbitrage test.
- **Inference:** Brier/log-loss with paired cluster-bootstrap by event (strikes in one hour share
  a single outcome, so contracts are not independent).
- **Trading test:** fee-aware backtest (`ceil(0.07 * P * (1-P))` taker fee) with the edge threshold
  chosen on an earlier period and evaluated on a later one; static-arbitrage scan of strike ladders.
- **Forward test:** a collector logs live quotes, the options smile and model prices; settlement
  is joined later, so the options-surface model is evaluated strictly out of sample.

### 2. Recurring markets: is there an edge in "bet NO on rain, every time"?
Kalshi lists a daily "will it rain in <city>?" market for ~20 US cities (YES if measured
precipitation is strictly above 0 in). `recurring.py` / `rain_study.py` test:
- the naive always-NO rule, by lead time, price bucket and city, net of fees;
- calibration by price (favorite-longshot bias, documented for Kalshi by
  [Whelan 2025](https://www.karlwhelan.com/Papers/Kalshi.pdf));
- a walk-forward forecast model built from *as-of* archived weather forecasts (Open-Meteo
  previous-runs, so no hindsight) against the market price.

### 3. `mmsim`: market making under adverse selection
Hawkes-process order flow with price impact, Avellaneda-Stoikov quoting, and an intensity-aware
extension, evaluated on common random numbers. Validated against analytic fill rates.

### 4. `quantlab`: bias-aware backtesting toolkit
Look-ahead-safe engine, walk-forward validation, Probabilistic/Deflated Sharpe.

## Status
Results sections are filled in as each study completes; null results are reported as null.
Forward data accumulates in `data_live/`.

## Run it
```bash
git clone https://github.com/skandra08/kalshi-edge-research && cd kalshi-edge-research
pip install -e ".[dev]"
pytest -q                                   # 30 tests
python -m digitaledge study --start 2026-09-15 --end 2026-10-05
bash scripts/collect_forever.sh             # local forward-data collector
python -m digitaledge.live                  # one live snapshot vs the options surface
```
Public API responses are cached under `data/`, so reruns are fast and resumable (Kalshi
rate-limits, so first pulls are slow).

## Layout
```
digitaledge/  data sources, vol models, digital pricing, SVI, scoring, backtest, rain study, collector
mmsim/        Hawkes market-making simulator
quantlab/     backtesting toolkit
tests/        30 tests, all offline (synthetic data with known ground truth)
scripts/      local collector loop
data_live/    forward snapshots (gzip CSV)
```
