# Market-Making Simulator with Hawkes Order Flow

Event-driven simulator for studying **passive market making under adverse selection**.
Order flow is a bivariate **Hawkes process** (self/cross-exciting buys and sells) with
permanent price impact, so bursts of flow are informative and quoting into them loses
money. On top of it: **Avellaneda–Stoikov** inventory-aware quoting, and an
**intensity-aware extension** that widens the side most likely to be picked off.

Also included: `quantlab`, a bias-aware backtesting/validation toolkit (look-ahead-safe
engine, walk-forward, Deflated Sharpe) in the same repo.

## Why it's built this way
- **Common random numbers.** Order flow does not depend on our quotes, so each seed's
  path is generated once and every strategy trades the *same* path. Strategy
  comparisons use paired differences, which is far lower-variance than independent runs.
- **Validated against theory.** Tests check Hawkes mean intensity = mu/(1-n), overdispersed
  inter-arrivals (clustering), and that simulated fill rates match the analytic
  Poisson `mu * exp(-k*d)` when excitation and impact are switched off.
- **Adverse selection is measured, not assumed:** per-fill *markout* (mid 10s later vs
  fill price) is reported alongside P&L.
- **Held-out evaluation.** The one tuned parameter (`widen`) was chosen on seeds 0-299;
  the demo reports seeds 10000+.

## Running it locally (free, no cloud needed)
```bash
git clone https://github.com/skandra08/kalshi-edge-research && cd kalshi-edge-research
pip install -e ".[dev]"
pytest -q

# forward data: leave this running (laptop, Raspberry Pi, or a $5 VPS); it commits hourly
bash scripts/collect_forever.sh

# historical studies (API responses are cached under data/, so reruns are instant)
python -m digitaledge study --start 2026-09-15 --end 2026-10-05
```
Kalshi rate-limits public requests, so first-time pulls take a while; the cache makes them resumable.

## Run it
```bash
pip install -e ".[dev]"
pytest -q                        # 16 tests
python examples/run_mm_demo.py   # table + examples/mm_results.png
```

## Results (400 held-out 10-minute paths, units = ticks)
| Strategy | Mean P&L | P&L sd | Sharpe | Inventory sd | Fills | Markout/fill | Paired t vs A-S |
|---|---|---|---|---|---|---|---|
| Fixed spread (2 ticks) | 514.9 | 169.6 | 3.04 | 5.30 | 409 | 1.27 | +4.0 |
| Avellaneda-Stoikov | 483.2 | 55.1 | 8.77 | 1.51 | 371 | 1.30 | - |
| Hawkes-aware A-S | 511.8 | 56.4 | 9.07 | 1.37 | 308 | 1.66 | +25.2 |

- Inventory control cuts P&L volatility ~3x for similar P&L (fixed quotes just carry risk).
- Widening against excess flow intensity reduces adverse selection (markout +28%) and adds
  ~28 ticks/path over plain A-S, with fewer but better fills.
- A larger widening factor lowers adverse selection further but gives up too much volume
  (swept 0.5-4); the P&L-optimal setting is small.

## Limitations (what I'd say in an interview)
- Stylised flow: depth is exponential, impact is a constant permanent shift, no queue
  position, latency, fees/rebates, or multi-level book.
- Excitation is read exactly from the generator; a live system would estimate it from
  recent trades (an EWMA of signed flow), adding noise.
- Results show the mechanism, not a tradeable P&L figure.

## Layout
```
mmsim/       flow.py (Hawkes + impact), strategies.py, engine.py
quantlab/    backtesting + validation toolkit
tests/       16 tests   examples/   demos and plots
```

## Roadmap
- [ ] Fit Hawkes parameters to real L2/trade data (MLE) and estimate intensity online
- [ ] Queue-position model and latency
- [ ] Learn quoting with RL / dynamic programming and compare to A-S
