# Technical Analysis Helper

A Python service that classifies **market regime** (trend up / trend down / range) for ETH-USDT perpetual swaps using multi-timeframe technical features from OKX, MongoDB persistence, XGBoost, and Redis alerting.

Orchestration (cron, alerts, ops) can be externalized with **n8n**; see [`docs/n8n_integration_migration.md`](docs/n8n_integration_migration.md).

## Features

- Pull OKX candlesticks for **15m / 1H / 4H / 1D** into MongoDB
- Continuity checks across timeframes (gap detection)
- Feature merge with rolling normalization (168 × 1H window)
- Rule-based regime labels + XGBoost 3-class regime model
- One-shot training pipeline: `pull → continuity → merge → label → train`
- Live prediction with Redis: **current regime SET** + **ZSET sliding window**; **Stream XADD only on trend reversal**

## Market regimes

| Value | Label | Typical strategy hint |
|------:|-------|------------------------|
| 1 | `TREND_UP` | Trend-following long |
| 2 | `TREND_DOWN` | Trend-following short / defensive |
| 3 | `RANGE` | Grid / mean-reversion style |

Labels are produced by a rule engine (`RegimeLabeler`) from features such as ADX, DI, EMA crosses, and ATR ratios. The model learns to approximate that structure for live inference.

## Architecture (high level)

```
OKX API → MongoDB (candlesticks / features)
                ↓
     FeatureMerge + RegimeLabeler + RegimeTrainer
                ↓
     GET /regime/3-predict
                ↓
     Redis: SET current · ZADD zwin · XADD only on UP↔DOWN reversal
```

Production (`PRODUCTION_MODE=true`) keeps prediction available and disables training/pull endpoints.

---

## Prerequisites

- Python 3.10+ (3.13 used in local venv)
- MongoDB
- Redis
- Optional: Docker / Docker Compose; Node 20+ if running n8n locally

## Quick start (local)

```bash
git clone <repository-url>
cd technial_analysis_helper

python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
./venv/bin/python -m pip install -r requirements.txt

cp .env.example .env
# Edit MongoDB / Redis / schedule settings as needed

# Start MongoDB and Redis, then:
cd src
../venv/bin/python main.py --host 127.0.0.1 --port 8000
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

API docs: `http://127.0.0.1:8000/docs`

---

## Configuration

Copy `.env.example` to `.env`. Important variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `MONGODB_URI` | `mongodb://localhost:27017` | MongoDB connection |
| `REDIS_HOST` / `REDIS_PORT` / `REDIS_DB` | `localhost` / `6379` / `1` | Redis |
| `REDIS_REGIME_STREAM` | `regime_signals` | Stream used for **reversal alerts only** |
| `REDIS_REGIME_WINDOW_HOURS` | `48` | Sliding window length for `zwin` |
| `REDIS_REGIME_REVERSAL_CONFIRM` | `2` | Consecutive directional hits to confirm reversal |
| `REDIS_REGIME_MIN_CONFIDENCE` | `0.65` | Min confidence for directional points in the window |
| `PRODUCTION_MODE` | `false` | When `true`, pull / pipeline / train / continuity / label return 403 |
| `SCHEDULE_ENABLED` | `false` | In-process regime scheduler (prefer n8n in production) |
| `REGIME_MODEL_SAVE_PATH` | `models/regime_model.json` | Regime model artifacts |

---

## HTTP API (current)

All regime routes are under `/regime`. The legacy `/fetch/*` price-signal API has been removed.

| Method | Path | Production | Description |
|--------|------|------------|-------------|
| GET | `/health` | yes | Liveness |
| GET | `/regime/0-stats` | yes | Feature / label coverage + candlestick counts per bar |
| GET | `/regime/3-predict` | yes | Live regime prediction + Redis update |
| GET | `/regime/explain-rules` | yes | Rule-engine explanation (no ML) |
| GET | `/regime/pull-history` | no | Pull one bar’s history from OKX |
| GET | `/regime/check-continuity` | no | Continuity check for 15m/1H/4H/1D |
| GET | `/regime/pipeline` | no | End-to-end train pipeline |
| GET | `/regime/1-label` | no | Apply regime labels to features |
| GET | `/regime/2-train` | no | Train regime model |

### Recommended training flow

**One shot (preferred):**

```bash
curl -s 'http://127.0.0.1:8000/regime/pipeline?inst_id=ETH-USDT-SWAP&max_records_1h=2400&strict_continuity=true' | python -m json.tool
```

**Manual steps:**

```bash
# Optional: pull per timeframe (or let pipeline pull)
curl 'http://127.0.0.1:8000/regime/pull-history?bar=1H&max_records=2400'

curl 'http://127.0.0.1:8000/regime/check-continuity?inst_id=ETH-USDT-SWAP'

# Merge + label + train are inside /regime/pipeline;
# stepwise label/train after features exist:
curl 'http://127.0.0.1:8000/regime/1-label?only_fix_none=true'
curl 'http://127.0.0.1:8000/regime/2-train?limit=10000&test_ratio=0.2'
```

### Live prediction

```bash
curl -s 'http://127.0.0.1:8000/regime/3-predict?from_local=true' | python -m json.tool
```

Use `from_local=false` to build features from the OKX API instead of MongoDB.

Example response (shape):

```json
{
  "type": "regime",
  "regime": 3,
  "regime_label": "RANGE",
  "recommended_strategy": "grid",
  "confidence": 0.58,
  "probabilities": { "1": 0.2, "2": 0.22, "3": 0.58 },
  "price": 1880.0,
  "inst_id": "ETH-USDT-SWAP",
  "redis": {
    "updated_current": true,
    "window_size": 12,
    "reversal_detected": false,
    "reversal_alerted": false,
    "stream_id": null,
    "reversal": null
  }
}
```

---

## Redis: current regime and `zwin` sliding window

`/regime/3-predict` no longer XADDs every prediction. Broadcasting “current trend” on every tick is noisy for downstream consumers. Instead:

1. **Always** `SET` the latest regime snapshot  
2. **Always** append into a time-bounded ZSET window (`zwin`)  
3. **Only** `XADD` to `regime_signals` when an **UP ↔ DOWN** reversal is confirmed  

### Keys

| Key | Type | Purpose |
|-----|------|---------|
| `regime:current:{inst_id}` | String (JSON) | Latest regime snapshot |
| `regime:zwin:{inst_id}` | ZSET | Sliding time window of recent regimes |
| `regime:last_reversal:{inst_id}` | String | Dedup id for the last alerted reversal streak |
| `regime_signals` (stream) | Stream | Reversal alerts only (`type=regime_reversal`) |

### How `zwin` time-windowing works

`regime:zwin:{inst_id}` is a Redis **sorted set**. The prediction candle **timestamp (ms)** is the **score**; the **member** is a compact JSON payload (`regime`, `confidence`, `price`, …).

On each `/regime/3-predict`:

| Step | Redis action | Meaning |
|------|----------------|---------|
| Dedup | `ZRANGEBYSCORE key ts ts` → `ZREM` | Keep at most one point per timestamp |
| Write | `ZADD key {member: ts}` | Insert / refresh this candle’s regime |
| Trim | `ZREMRANGEBYSCORE key -inf (ts − window_ms)` | Drop points older than the window |

Window length:

```text
window_ms = REDIS_REGIME_WINDOW_HOURS × 3600 × 1000
cutoff    = current_timestamp − window_ms
```

Default **48 hours**: only points in `[now − 48h, now]` remain.

```
timeline ──●──●──●──●──●──●──●──► current ts
           │←—— 48h window ——→│
           ▲ older scores removed by ZREMRANGEBYSCORE
```

This is a **wall-clock** window, not a fixed “last K samples” window. If predictions run less often, fewer members remain; if you backfill densely, more members remain inside the same hours.

### How reversal is decided (inside the window)

After trimming:

1. `ZRANGE 0 -1` loads all members (time-ordered by score)  
2. Keep only **TREND_UP / TREND_DOWN** with `confidence ≥ REDIS_REGIME_MIN_CONFIDENCE` (RANGE and low-confidence points are ignored for direction)  
3. Require the **latest streak** of the same direction to be at least `REDIS_REGIME_REVERSAL_CONFIRM` (default 2)  
4. If the directional point **before that streak** is the **opposite** UP/DOWN → treat as reversal → **XADD** once per streak (deduped via `regime:last_reversal:*`)

Example directional sequence (RANGE already filtered out):

```text
… UP, UP, DOWN, DOWN
         ↑prev  ↑streak (confirm=2)  →  alert UP → DOWN
```

Inspect locally:

```bash
redis-cli -n 1 GET 'regime:current:ETH-USDT-SWAP'
redis-cli -n 1 ZRANGE 'regime:zwin:ETH-USDT-SWAP' 0 -1 WITHSCORES
redis-cli -n 1 XREVRANGE regime_signals + - COUNT 5
```

---

## Docker

Prefer compose files in the repo (`docker-compose.mac.yml`, `docker-compose.centos.yml`, `docker-compose.all-service.yml`) depending on host.

```bash
# Example (CentOS / production-style)
docker compose -f docker-compose.centos.yml up -d --build
docker compose -f docker-compose.centos.yml logs --tail 200 -f api
```

Place regime model files under `models/`:

```text
models/regime_model.json
models/regime_model_scaler.pkl
models/regime_model_features.json
```

With `PRODUCTION_MODE=true`, use a separate training instance (`PRODUCTION_MODE=false`) for `/regime/pipeline` and pull/label/train.

More ops detail: [`DEPLOYMENT.md`](DEPLOYMENT.md) (some sections may still mention legacy `/fetch` paths; prefer this README for the current API).

---

## Project structure (abbreviated)

```text
├── src/
│   ├── api/
│   │   ├── api_base.py              # FastAPI app
│   │   ├── api_regime.py            # Regime HTTP API
│   │   └── api_config.py
│   ├── collect/                     # OKX fetch, Mongo handlers, continuity
│   ├── feature/                     # Per-bar feature creators + FeatureMerge
│   ├── regime/                      # Labeler, types, RegimePipeline
│   ├── models/                      # regime_trainer (+ legacy xgboost trainers)
│   ├── schedule/                    # Optional in-process schedulers
│   ├── stream/                      # Redis current / zwin / stream alerts
│   └── utils/                       # Indicator calculators, notifiers
├── models/                          # Saved model artifacts
├── tests/
├── docs/
│   └── n8n_integration_migration.md
├── requirements.txt
├── .env.example
└── README.md
```

---

## Tests

```bash
# Indicator / collector tests
./venv/bin/python -m pytest tests/calculator -q
./venv/bin/python -m pytest tests/collector -q

# Regime pipeline / Redis reversal logic
./venv/bin/python -m pytest tests/regime -q
./venv/bin/python -m pytest tests/redis/test_regime_reversal_publish.py -q
```

---

## n8n (optional)

Use n8n for cron-driven calls to `/regime/3-predict`, health checks, and training pipelines against a non-production API. Requires **Node.js ≥ 20** (`File` global). Detailed workflows: [`docs/n8n_integration_migration.md`](docs/n8n_integration_migration.md).

---

## Troubleshooting

| Issue | What to check |
|-------|----------------|
| `Failed to extract features` (`from_local=true`) | Mongo candlesticks exist and are recent; continuity OK; API restarted after feature-merge sort fix |
| `Regime model not found` | Run `/regime/pipeline` or `/regime/2-train`; ensure files under `models/` |
| Training endpoints 403 | `PRODUCTION_MODE=true` — use a training instance |
| No Stream messages | Expected unless UP↔DOWN reversal confirmed; check `redis.reversal_*` in predict response and `zwin` contents |
| n8n `File is not defined` / `command start not found` | Upgrade Node to 20+ or 22 and reinstall n8n |

---

## License

MIT — see [LICENSE](LICENSE).
