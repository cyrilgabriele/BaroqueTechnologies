# AFML — Chapter 2: Financial Data Structures  
## What you will implement (practical, code-first checklist)

**Goal of Chapter 2**  
Turn raw market data into **ML-ready observations (“bars”)** by sampling the market in a way that reflects **information arrival**, not clock time.

This chapter answers one core question:

> *How should I sample financial data so that my ML model is not trained on distorted, noisy observations?*

---

## 2.3 Bars (MAIN DELIVERABLE)

You will implement **two families of bars**.

---

### A) Standard Bars (Section 2.3.1)

These sample the market by *activity*, not time.

You will implement:

1. **Time Bars**  
   - Fixed clock time (1-min, 5-min, daily)  
   - Baseline only — known to be statistically weak

2. **Tick Bars**  
   - One bar every *N trades*  
   - Requires trade-by-trade data (ticks)

3. **Volume Bars**  
   - One bar every *N shares/contracts traded*  
   - Can be built from intraday OHLCV

4. **Dollar Bars**  
   - One bar every *N dollars traded*  
   - Dollar value ≈ `price × volume`

**Why this matters**  
Markets do not process information at a constant rate.  
Sampling by activity produces returns closer to IID-like behavior, which is critical for ML.

> With Alpha Vantage:
> - You **can** build Volume Bars and Dollar Bars  
> - You **cannot** build true Tick Bars (no trade prints)

---

### B) Information-Driven Bars (Section 2.3.2)

These sample **when information arrives**, not when volume thresholds are hit.

You will later implement (when tick data is available):

- Tick Imbalance Bars (TIB)
- Volume Imbalance Bars (VIB)
- Dollar Imbalance Bars (DIB)
- Tick Runs Bars
- Volume Runs Bars
- Dollar Runs Bars

**Core idea (example: Tick Imbalance Bars)**

1. Assign a sign to each tick using the tick rule  
2. Accumulate imbalance  
   \[
   \theta_T = \sum b_t
   \]
3. Trigger a bar when imbalance exceeds an expected threshold:
   \[
   |\theta_T| \ge E_0[T] \cdot |2P(b_t=1) - 1|
   \]

These bars adapt dynamically to changing market conditions.

---

## 2.4 Dealing with Multi-Product Series

Portfolios often involve:
- Multiple assets
- Futures rolls
- Instrument substitutions

You will learn and (later) implement:

1. **ETF Trick**  
   - Represent a basket or rolling futures position as a synthetic ETF  
   - Allows portfolio-level modeling without expiration artifacts

2. **PCA Weights**  
   - Use PCA to derive hedge or basket weights

3. **Single-Future Roll Adjustment**  
   - Track roll gaps
   - Adjust price series for continuity
   - Use raw prices for execution, adjusted prices for PnL

---

## 2.5 Sampling Features

After bars exist, you must decide **which bars become rows in your dataset**.

### A) Sampling for Reduction (2.5.1)
- Simple down-sampling
- Reduces size but may discard informative events

### B) Event-Based Sampling (2.5.2)
- Sample only when something *happens*
- Example: **CUSUM filter**
  - Detects structural moves
  - Produces event timestamps for labeling (Chapter 3)

This is the bridge between **bars** and **labeling**.

---

## What YOU will implement first (Alpha Vantage compatible)

### Step 1 — Load intraday OHLCV
- 1-min or 5-min data

### Step 2 — Build activity-based bars
- Volume Bars
- Dollar Bars

### Step 3 — Compare against time bars
- Number of bars per day
- Return autocorrelation
- Return distribution stability

### Step 4 — Implement event sampling
- CUSUM filter on returns
- Generate event timestamps

---

## What comes later (requires tick data)
- Tick bars
- Imbalance bars
- Runs bars

These are *not* blocked conceptually — only by data availability.

---

## End of Chapter 2
If implemented correctly, you now have:

- ML-ready sampling
- Reduced microstructure noise
- A clean foundation for **labeling (Chapter 3)**

Next step: **Triple-Barrier labeling on event-sampled bars**.
