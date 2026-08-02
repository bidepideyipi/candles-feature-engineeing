# PRD: Technical Analysis Helper — Dual-Track Market Regime

**Version:** 2.1  
**Status:** Draft for implementation  
**Language:** English  
**Instrument (default):** `ETH-USDT-SWAP`  
**Primary bar for samples:** `1H`

---

## 1. Product overview

### 1.1 Problem

Traders need two different answers at the same time:

1. **What is the market structure right now?** (for positioning / strategy selection)  
2. **What structure is likely over the next ~48 hours?** (for whether the current thesis continues or flips)

A single model that only copies present-tense rules does not answer (2). A rule engine alone cannot forecast (2).

### 1.2 Product goal

Ship a **dual-track regime system**:

| Track | Role | Answers |
|-------|------|---------|
| **Rules** (`RegimeLabeler`) | Explain the **present** | Current structure: `TREND_UP` / `TREND_DOWN` / `RANGE` |
| **Model** (XGBoost) | Explain the **future** | Structure **48 hours ahead** (still three classes) |

Rules and model run **in parallel**. Downstream consumers may use either or both (e.g. “now = RANGE, 48h outlook = TREND_UP”).

### 1.3 Non-goals (v2)

- Price-move 5-class / 7-class prediction APIs (legacy `/fetch/5-predict` removed)
- Replacing the rule engine with the model for “what is now”
- Guaranteeing profitable trades; the product emits structure signals, not order execution

---

## 2. Core concepts

### 2.1 Regime classes (shared vocabulary)

Both tracks use the same three labels:

| ID | Name | Meaning (structure) | Typical strategy hint |
|----|------|---------------------|------------------------|
| 1 | `TREND_UP` | Bullish trend structure | Trend-following long bias |
| 2 | `TREND_DOWN` | Bearish trend structure | Trend-following short / defensive |
| 3 | `RANGE` | Range / chop structure | Grid / mean-reversion bias |

### 2.2 Time anchors

- **Sample time `T`:** timestamp of a **1H** feature row (one decision per completed 1H candle).  
- **Horizon `H`:** **48 hours** = **48 × 1H bars** after `T`.  
- **Present regime `R_now(T)`:** rule label at `T`.  
- **Future regime `R_48h(T)`:** rule label at `T + 48h` (see §4.2). This is the **model training target**.

### 2.3 Continue vs change (derived, not a fourth class)

“Continue or change” is **not** a separate classification head in v2.

```
continue  :=  R_48h(T) == R_now(T)
change    :=  R_48h(T) != R_now(T)
```

The model still outputs one of `{1,2,3}` for **future structure**. Clients compare model output to `R_now` to interpret continuation vs transition.

---

## 3. Dual-track design

### 3.1 Track A — Rules (present)

**Purpose:** Deterministic explanation of **current** multi-timeframe structure.

**Input:** Feature vector at `T` (especially 4H regime-related fields).  

**Output:** `R_now(T) ∈ {1,2,3}` plus human-readable explanation (`/regime/explain-rules`).

**Current rule logic (normative for v2 present track):**

1. **Force RANGE** if any hold:  
   - `adx_4h < 18`, or  
   - `atr_ratio_4h_1h < 2.0` (cross-TF: `ATR(4H)/ATR(1H)`; below √4 scale → 1H noise dominates), or  
   - `|trend_continuation_4h| < 0.15` and `adx_4h < 20`
2. Else build **bullish** / **bearish** flags from 4H DI, EMA cross, trend continuation, EMA12/26, MACD histogram (same logic as `RegimeLabeler` today).
3. If `adx_4h ≥ 20` and bullish → `TREND_UP`; if `adx_4h ≥ 20` and bearish → `TREND_DOWN`; else → `RANGE`.

Rules describe **structure at `T`**, not future returns.

### 3.2 Track B — Model (future 48h)

**Purpose:** Learn `P(R_48h | features_at_T)` so the system can speak about the **next 48 hours**.

**Input:** Features known at `T` only (no leakage from `T+1 … T+48`).  

**Target:** `R_48h(T)` as defined in §4.2.  

**Output:** Predicted class + probabilities for `{TREND_UP, TREND_DOWN, RANGE}` at horizon 48h, plus confidence.

**Why train at all:** The target is **forward-looking** and is **not** identical to `R_now`. Accuracy can be meaningfully below “copy the rules,” which is expected and desirable.

### 3.3 Parallel runtime contract

On each prediction cycle (scheduler / n8n / API):

1. Build features at latest `T`.  
2. **Rules:** compute `R_now` + explanation.  
3. **Model:** predict `R_48h_hat`.  
4. Optionally derive `continue/change = (R_48h_hat == R_now)`.  
5. Persist / publish (Redis current keys, streams, alerts) per §7.

Neither track blocks the other: if the model file is missing, rules still work; if rules fail, model inference may still run when features exist.

---

## 4. Labeling specification (model target)

### 4.1 Present label (rules)

- Field: `regime_now` on the **1H** feature document at `T`  
- Generator: `RegimeLabeler.classify(features_at_T)`  
- Semantics: **present structure only**  
- Do **not** store `regime_label` on features (removed; API may still return string names like `"TREND_UP"` under `present.regime_label` for display only)

### 4.2 Future label (model; new definition)

**Primary definition (v2):**

```
R_48h(T) = RegimeLabeler.classify(features_at_(T + 48 hours))
```

Requirements:

- Feature row must exist at `T + 48 × 3_600_000 ms` (aligned 1H bar).  
- Same rule engine as present (no separate future rule set).  
- Samples without a complete feature row at `T+48h` are **not** used for training (right-censored).

**Interpretation:**

- Predicts the **structure snapshot 48 hours later**, not the path’s every intermediate bar.  
- “Will the trend continue?” ≈ whether `R_48h` equals `R_now`.  
- “Will it change direction?” ≈ whether `R_48h` differs (including transitions into/out of `RANGE`).

**Optional secondary label (out of scope for MVP training head):** majority vote of `R_now` over `(T, T+48h]` — may be added later if path-stability matters more than endpoint structure.

### 4.3 Class balance and horizon choice

- Horizon fixed at **48h** for v2 (product requirement).  
- Expect class imbalance and regime persistence (many continues). Report per-class metrics and continue/change accuracy separately (§6).

---

## 5. System architecture

### 5.1 Modules

1. **Collect** — OKX candlesticks for `15m` / `1H` / `4H` / `1D` → MongoDB  
2. **Continuity** — gap checks before training  
3. **Feature merge** — multi-TF indicators + rolling 1H normalization (window 168) onto 1H rows  
4. **Present labeling** — rules → `regime_now`  
5. **Future labeling** — shift/join → `regime_48h`  
6. **Train** — time-series split XGBoost on `regime_48h`  
7. **Serve** — FastAPI `/regime/*`  
8. **Redis** — current snapshots + sliding window + reversal / outlook alerts  
9. **Orchestration** — optional n8n cron (see `docs/n8n_integration_migration.md`)

### 5.2 Data stores

**Candlesticks**

```javascript
{
  "inst_id": "ETH-USDT-SWAP",
  "bar": "1H",           // also 15m, 4H, 1D
  "timestamp": Number,   // ms
  "open": Number,
  "high": Number,
  "low": Number,
  "close": Number,
  "volume": Number
}
```

**Features (1H row; dual labels)**

```javascript
{
  "inst_id": "ETH-USDT-SWAP",
  "bar": "1H",
  "timestamp": Number,
  "price": Number,
  // multi-timeframe technical fields ...
  "regime_now": Number,      // 1|2|3  — rules at T (present)
  "regime_48h": Number,      // 1|2|3  — rules at T+48h (model target; null if unknown)
  // do not store regime_label (removed)
}
```

Unique index: `(inst_id, timestamp, bar)`.

### 5.3 HTTP API (target surface)

| Method | Path | Role |
|--------|------|------|
| GET | `/health` | Liveness |
| GET | `/regime/0-stats` | Counts + label coverage (`regime_now` / `regime_48h`) |
| GET | `/regime/pull-history` | Pull OKX history |
| GET | `/regime/check-continuity` | Continuity report |
| GET | `/regime/merge-features` | Candlesticks → 1H feature rows |
| GET | `/regime/pipeline` | Pull → continuity → merge → dual label → train |
| GET | `/regime/1-label` | (Re)build present + future labels |
| GET | `/regime/2-train` | Train model on `regime_48h` |
| GET | `/regime/3-predict` | Parallel: rules (now) + model (48h outlook) |
| GET | `/regime/explain-rules` | Present-tense rule breakdown only |

`PRODUCTION_MODE` does **not** 403 these endpoints; it may still affect OKX proxy behavior.

### 5.4 Predict response shape (target)

```json
{
  "inst_id": "ETH-USDT-SWAP",
  "timestamp": 0,
  "price": 0,
  "present": {
    "regime": 3,
    "regime_label": "RANGE",
    "source": "rules",
    "recommended_strategy": "grid",
    "explanation_ref": "/regime/explain-rules"
  },
  "transition": {
    "source": "model",
    "horizon_hours": 12,
    "prediction": "CHANGE",
    "p_continue": 0.25,
    "p_change": 0.75,
    "threshold": 0.66,
    "model_gate_passed": true,
    "alert_eligible": true
  },
  "derived": {
    "continues": false,
    "changes": true,
    "p_continue": 0.25,
    "p_change": 0.75
  },
  "redis": {}
}
```

### 5.5 Feature merge (`GET /regime/merge-features`)

**Role:** Turn Mongo **candlesticks** (`15m` / `1H` / `4H` / `1D`) into one **1H-timestamped** feature document. This is the only step that materializes technical indicators used by rules, training, and predict.

**Code path:** `FeatureMerge.loop` → `_process_and_cache` → `_common_process` → `Feature{1H,15m,4H,1D}Creator` → `feature_handler.save_features` (batch).

#### 5.5.1 Algorithm (correctness checklist)

| Step | Behavior | Verdict |
|------|----------|---------|
| Cursor | Start at latest 1H `timestamp + 1h`, walk **backward** via `before` | OK — historical backfill |
| Fetch | 1H uses `ROLLING_NORM_WINDOW` (default **168**); other bars use `FEATURE_CANDLE_WINDOW` (default **48**) | OK — MACD/EMA need ~48 bars; norm needs ~1 week of 1H |
| Order | `_fetch_candles` reverses DB desc → **time ascending** | OK (fixed earlier for predict path) |
| Align | Last 15m hour == last 1H hour; last 1D date == last 1H date; last 4H covers last 1H (`ts_4h ≤ ts_1h < ts_4h+4h`) | OK — drops misaligned bars |
| Continuity | Within the 48-bar window, exact step (15m/1H/4H/1D) | OK — fails closed on gaps |
| Normalize | Rolling z-score of 1H close/volume over last 168 bars → applied to price, volume, EMAs, Bollinger bands | OK — scale-invariant vs ETH absolute price |
| Emit | One `Feature` row keyed by last **1H** timestamp; labels not written here | OK — label is `/regime/1-label` |

**ATR ratios (cross-timeframe):**  
`atr_ratio_4h_1h = ATR(4H) / ATR(1H)` and `atr_ratio_1h_15m = ATR(1H) / ATR(15m)` via `ATRRatioCalculator.calculate_cross_timeframe_ratio`. Present rules force RANGE when `atr_ratio_4h_1h < 2.0` (geometric √4≈2 floor). Same-TF short/long ATR₁₂/ATR₂₄ remains available on the calculator as `calculate()` but is **not** written to these feature fields.

#### 5.5.2 Indicators produced (by timeframe)

**Shared convention**

- Sample row time `T` = last completed **1H** candle timestamp.  
- Higher/lower TF indicators are those of the **aligned** last bar of that TF at `T` (no future candles).  
- EMA / Bollinger prices are stored as **z-scores** vs the 1H rolling close mean/std (except raw ATR/RSI/ADX/MACD histogram scales as implemented).

##### 1H (decision bar)

| Field | Indicator | What it means for “explain the feature” |
|-------|-----------|----------------------------------------|
| `close_1h_normalized` | Z-score close | Where price sits vs ~1w local mean; extreme → stretched move |
| `volume_1h_normalized` | Z-score volume | Participation vs local norm; spike → conviction / stop cascade risk |
| `rsi_14_1h` | RSI(14) | Momentum / overbought–oversold on decision bar |
| `macd_line_1h`, `macd_signal_1h`, `macd_histogram_1h` | MACD(12,26,9) | Trend impulse; hist>0 favors bulls |
| `atr_1h` | ATR | Absolute volatility on 1H |
| `adx_1h`, `plus_di_1h`, `minus_di_1h` | ADX / DI | Short-horizon trend strength and direction |
| `ema_12_1h`, `ema_26_1h`, `ema_48_1h` | EMA (z-scored) | Local trend stack on 1H |
| `ema_cross_1h_12_26`, `ema_cross_1h_26_48` | Sign(fast−slow) | +1/−1/0 crossover state |
| `atr_ratio_1h_15m` | **Cross-TF** `ATR(1H)/ATR(15m)` | Micro vs decision-bar vol scale |
| `rsi_divergence_1h` | RSI divergence flag | Price vs RSI disagreement (exhaustion hint) |
| `upper/lower_shadow_ratio_1h`, `shadow_imbalance_1h`, `body_ratio_1h` | Pinbar geometry | Rejection / indecision candle anatomy |
| `hour_cos`, `hour_sin`, `day_of_week` | Cyclical time | Session seasonality without raw timestamp leakage |
| `price` | Raw close | Display / alerts only (excluded from model inputs) |

##### 15m (microstructure / noise filter)

| Field | Indicator | Explain meaning |
|-------|-----------|-----------------|
| `rsi_14_15m` | RSI(14) | Faster momentum; often leads 1H RSI |
| `macd_*_15m` | MACD | Short impulse confirmation / conflict with higher TF |
| `atr_15m` | ATR | Micro volatility |
| `stoch_k_15m`, `stoch_d_15m` | Stochastic | Short-term OB/OS; chop detector |
| `volume_impulse_15m` | Volume impulse | Sudden volume burst vs recent baseline |

##### 4H (primary **present-regime** structure — used by `RegimeLabeler`)

| Field | Indicator | Explain meaning |
|-------|-----------|-----------------|
| `adx_4h` | ADX | **Core:** trend strength; low → RANGE |
| `plus_di_4h`, `minus_di_4h` | +DI / −DI | Directional dominance for UP vs DOWN |
| `trend_continuation_4h` | Custom continuation score ∈ ~[−1,1] | Signed streak strength; near 0 → chop |
| `ema_12/26/48_4h` | EMA (z-scored) | Medium-term stack |
| `ema_cross_4h_12_26`, `ema_cross_4h_26_48` | Cross signs | Bull/bear alignment for rules |
| `macd_*_4h` | MACD | Momentum agreement with DI/EMA |
| `atr_4h` | ATR | Medium-horizon volatility |
| `atr_ratio_4h_1h` | **Cross-TF** `ATR(4H)/ATR(1H)` | **Core rule:** <2.0 → force RANGE (1H noise dominates) |
| `rsi_14_4h`, `rsi_divergence_4h` | RSI / divergence | Medium momentum / exhaustion |
| `*_shadow_*_4h`, `body_ratio_4h` | Pinbar | Swing rejection context |

##### 1D (macro context)

| Field | Indicator | Explain meaning |
|-------|-----------|-----------------|
| `rsi_14_1d` | RSI(14) | Daily momentum bias |
| `atr_1d` | ATR | Macro volatility regime |
| `bollinger_upper/lower_1d` | BB(20) z-scored | Band location in normalized space |
| `bollinger_position_1d` | Position in band [0,1] | Near 0/1 → band extremes (mean-reversion vs breakout context) |
| `macd_line_1d`, `macd_signal_1d` | MACD | Daily trend impulse |
| Pinbar ratios `_1d` | Daily candle shape | Higher-TF rejection |

#### 5.5.3 How indicators feed “explain” vs model

**`/regime/explain-rules` (present track)** uses only the **4H rule subset**:

```
adx_4h, plus_di_4h, minus_di_4h, trend_continuation_4h,
ema_cross_4h_12_26, atr_ratio_4h_1h, macd_histogram_4h,
ema_12_4h, ema_26_4h
```

Interpretation for clients:

1. **RANGE forced** — weak ADX, low cross-TF `atr_ratio_4h_1h` (<2), or weak continuation → “structure is chop; prefer grid / mean-reversion.”  
2. **TREND_UP / TREND_DOWN** — ADX≥20 plus DI + EMA/MACD agreement → “directional structure; prefer trend bias.”  
3. Other TF fields are **not** in the rule narrative today but still matter for **model outlook** (they can disagree with present rules → `derived.changes`).

**Model (`REGIME_FEATURE_COLUMNS`)** uses a broader multi-TF subset plus persisted
lag/delta, threshold-margin, regime-age, and switching features. The same fields
are produced for historical merge and live inference; no prediction-time constant
substitution is allowed. Full list lives in `src/models/regime_trainer.py`.

- 4H block ≈ “will this structure persist?”  
- 1H/15m ≈ “is there early stress / confirmation under the hood?”  
- 1D Bollinger/RSI/ATR ≈ “macro stretch vs room to run.”

**Transition-only dynamic fields:** `price_return_{1h,4h,12h}`,
`adx_4h_delta_{3h,6h,12h}`, DI-spread delta, MACD-histogram delta,
EMA-gap delta, ATR-ratio/RSI/Bollinger deltas, ADX/ATR threshold margins,
`regime_age_1h`, `regime_switches_24h`, and `rule_conflict_score`. They explain
whether the current rule structure is strengthening, weakening, near a boundary,
or repeatedly switching.

#### 5.5.4 Operational requirements

- Enough history: ≥ ~168 closed 1H bars and ≥ 48 bars per other TF before merge succeeds.  
- Run **after** pull + continuity; **before** `/regime/1-label`.  
- Idempotent upsert on `(inst_id, timestamp, bar)`; re-merge refreshes indicators but does not invent labels.

---

## 6. Machine learning specification

### 6.1 Features

Use indicators known at `T` from §5.5; training columns =
`REGIME_FEATURE_COLUMNS`, including persisted return/delta features generated
identically by offline merge and online prediction.

**Leakage ban:** no columns computed from candles strictly after `T`.

### 6.2 Split & training

- Sort by `timestamp` ascending.  
- Drop rows with missing confirmed transition labels or mismatched horizon metadata.  
- Binary target: `confirmed_change` (future different regime persists for at least
  `REGIME_CHANGE_CONFIRM_BARS`; default 2). Keep endpoint change only as a diagnostic.
- Use expanding walk-forward validation with a `horizon_hours` purge before each
  validation fold, then one untouched chronological holdout.
- Compare unweighted vs balanced XGBoost by validation PR-AUC.
- Fit Platt calibration on out-of-fold predictions; select a **global fallback
  threshold** plus **per-`present` regime thresholds** on validation only.
  Each regime must also pass the untouched holdout gate before
  `transition.alert_eligible` can be true for that subgroup.
- Report accuracy, ROC-AUC, PR-AUC, Brier score, CHANGE precision/recall/F1,
  alert rate, confusion matrix, and metrics grouped by present regime.

```
confirmed_change = any(
  regime_future != regime_now for N consecutive 1H rows within horizon
)
```

### 6.3 Success criteria (v2)

| Metric | Target | Notes |
|--------|--------|-------|
| Present rules vs manual spot checks | Deterministic match to §3.1 | No ML |
| Holdout accuracy vs always-CONTINUE | Must beat baseline | Primary deployment gate |
| CHANGE precision | > configured floor (default 0.50) | Avoid excessive false alerts |
| PR-AUC | Must exceed holdout change prevalence | Must add ranking information |
| Probability calibration | Monitor Brier score | `p_change` must be interpretable |
| Leakage audit | Zero future features | Required gate |

**Training knobs (env / API):**

- `REGIME_HORIZON_HOURS` (default 48) — forward label offset; Mongo field remains `regime_48h`. Relabel with `only_fix_none=false` after changing.  
- `REGIME_CLASS_WEIGHT` = `balanced` \| `none` — sample weights on train rows (`N/(K·n_c)`).  
- `REGIME_CHANGE_CONFIRM_BARS` (default 2) — persistence required for a true change.  
- `REGIME_CV_SPLITS` (default 3) — purged walk-forward folds.  
- `REGIME_MIN_CHANGE_PRECISION` (default 0.50) — alert deployment floor.
- `REGIME_HOLDOUT_START_TS` (optional ms timestamp) — pins the untouched holdout
  so 6h/8h/12h experiments are compared on the same market period.

**v2.2 model target (shipped):** binary **continue/change**  
`change := (regime_fwd != regime_now)`. Primary gate: `beats_always_continue`. Predict exposes `transition.p_change` + rules `present`.

If the model cannot beat “predict now forever,” shipping rules-only present + persistence outlook is acceptable until features/horizon improve.

---

## 7. Redis & alerting (aligned with dual track)

### 7.1 Keys (conceptual)

| Key | Content |
|-----|---------|
| `regime:current:{inst_id}` | Latest rules present + calibrated transition risk |
| `regime:zwin:{inst_id}` | ZSET sliding window (score = timestamp) for sequence logic |
| Stream `regime_signals` | Alerts only (not every tick) |

### 7.2 Alert philosophy

Do **not** XADD every present regime tick. Prefer alerts when actionable, for example:

- Calibrated `transition.p_change` exceeds the validation-selected threshold and
  the model passed all untouched holdout gates, and/or  
- Confirmed **UP ↔ DOWN** transitions in the sliding window (existing zwin idea), optionally gated by outlook agreement.

Exact alert policy may evolve; PRD requires separation of **state keys** vs **alert stream**.

### 7.3 zwin time window (reference)

- Score = prediction timestamp (ms).  
- Member = JSON snapshot (present + outlook fields as needed).  
- Trim with `ZREMRANGEBYSCORE` using `REDIS_REGIME_WINDOW_HOURS` (default 48h wall-clock window for history retention — independent of the **label horizon**, though both are 48h by product choice).

---

## 8. Pipelines & orchestration

### 8.1 Offline / training pipeline

```
pull (15m/1H/4H/1D)
  → continuity check
  → merge features (1H rows)
  → label present (rules @ T)
  → label confirmed changes inside configured horizon
  → purged walk-forward train + calibration + threshold selection
  → untouched holdout gate report
```

n8n reference workflow: parallel pulls → Merge (Combine / Position / 4 inputs) → continuity → **`/regime/merge-features`** → label → train (`docs/n8n_regime_pipeline_steps.png`).

### 8.2 Online / prediction loop

```
features @ T
  → rules → present
  → model + calibrator → p_change
  → threshold + holdout gate → transition alert eligibility
  → SET Redis current
  → ZADD zwin + conditional stream alert
```

---

## 9. Implementation requirements (v2 deltas)

Relative to the current codebase:

1. Keep **`regime_now`** as present rules; derive confirmed-change labels from the
   future rule path and its stored horizon metadata.  
2. Keep / expose **present rules** on predict + `explain-rules`.  
3. Extend label job to write both `regime_now` and `regime_48h`.  
4. Update `/regime/3-predict` response to dual-track schema (§5.4).  
5. Update evaluation to purged walk-forward, calibration, threshold sweep, and
   untouched holdout gates.  
6. Refresh README / n8n docs after API freeze.

---

## 10. Risks & mitigations

| Risk | Mitigation |
|------|------------|
| Label noise (rules imperfect at T+48h) | Same rules for now/future; document limitation |
| Persistence dominance | Explicit baseline comparison (§6.3) |
| Leakage | Feature time audit; only use data ≤ T |
| Right-censoring near latest candles | Exclude unlabeled future rows from train |
| Confusing “48h window” (zwin vs label) | Document: label horizon vs Redis retention are separate knobs |
| Cross-TF ATR threshold drift | Re-merge features + re-label after changing `ATR_RATIO_RANGE_MAX`; monitor RANGE share |

---

## 11. Future enhancements

- Multi-horizon confirmed-change models  
- Path-majority future label  
- Backtest harness: strategy switches when outlook disagrees with present  
- Calibration of probabilities for alert thresholds  

---

## 12. Summary

**Rules explain the present. The model explains the next 48 hours — still as one of three regimes.**  
Training is justified only because the label is **forward** (`R_48h`), not because it should reproduce `explain-rules`. Continuation vs change is derived by comparing the two tracks.

---

*End of PRD v2.0*
