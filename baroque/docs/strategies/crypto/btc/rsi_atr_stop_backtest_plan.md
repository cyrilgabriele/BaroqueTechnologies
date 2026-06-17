# BTC RSI/ATR Baseline Backtest Plan

## Summary

Implement a fixed-rule baseline backtest before any optimization. The backtest consumes the existing BTC RSI/ATR Strategy Feature Panel, excludes the incomplete `2026-06-16` candle, reserves the last two complete years as untouched final test data, and persists the mechanics in this strategy documentation.

Data split:

- Development Period: `2017-08-17` through `2024-06-15`
- Final Holdout Period: `2024-06-16` through `2026-06-15`
- Excluded: `2026-06-16`

## Key Changes

- Extend `baroque/src/config/strategies/crypto/btc/rsi_atr_stop_strategy.yaml` with backtest settings:
  - initial capital: `3000 USDT`
  - long-only, one position at a time
  - all-in equity sizing
  - zero costs for v1 baseline
  - entry and exit timing rules
  - split dates and excluded incomplete date
  - artifact output paths under `data/processed/backtests`
- Add reusable backtest logic in source code and call it from the RSI BTC notebook.
- Persist generated outputs:
  - trade ledger
  - daily equity curve
  - summary metrics
- Add glossary terms to `baroque/CONTEXT.md` without implementation details:
  - Backtest
  - Trade Ledger
  - Equity Curve
  - Final Holdout Period

## Backtest Mechanics

Signal timing:

- `buy_signal` is observed after close on day `T`.
- Entry executes at open on day `T+1`.
- `RSI(14) >= 70` exit signal is observed after close on day `T`.
- RSI exit executes at open on day `T+1`.

Entry:

- Long-only.
- Enter only when `buy_signal == True`.
- Ignore new buy signals while already in a position.
- Skip the signal if there is no next-day open.
- Skip the trade if the next-day entry open is already at or below the signal row's `initial_stop_price`.

Stops:

- Use `initial_stop_price` from the signal row.
- After entry, if `open <= stop`, exit at open.
- Otherwise, if `low <= stop`, exit at stop.
- If stop and RSI exit are both possible on the same daily bar, stop wins.

Position and accounting:

- Start with `3000 USDT`.
- Invest full current equity on each accepted trade.
- Use no leverage, no shorting, and no pyramiding.
- Allow fractional BTC.
- Use zero fees and zero slippage for the v1 baseline.
- Force-close any open trade at the evaluated period's final close with `exit_reason = end_of_period`.

## Outputs And Metrics

Trade ledger columns should include:

- signal date
- entry date
- entry price
- BTC quantity
- entry equity
- initial stop price
- exit date
- exit price
- exit reason
- holding days
- PnL in USDT
- return percentage
- ending equity

The equity curve should track daily account value using close prices while in position and cash value while flat.

Summary metrics for v1:

- number of trades
- win rate
- total return
- max drawdown
- average trade return
- best trade
- worst trade
- average holding days
- stop-hit rate

## Optimization Plan

Do not optimize in the v1 implementation.

After the baseline is trusted, add small-grid optimization only inside the Development Period. Use walk-forward validation inside `2017-08-17` through `2024-06-15`, then touch the Final Holdout Period only once after the optimization method and selected parameters are fixed.

Optimize primarily for return, but only among candidates passing drawdown and trade-count sanity constraints.

Initial future optimization parameters:

- feature parameters:
  - `rsi_window`
  - `atr_window`
  - `oversold_threshold`
  - `stop_multiple`
- backtest and exit parameters:
  - RSI profit-exit threshold
  - potentially max holding period later
  - eventually costs and slippage, after the zero-cost baseline

## Test Plan

Unit-test trade mechanics with small synthetic panels:

- normal buy then RSI exit
- normal buy then stop hit
- skip entry when next open is below stop
- open position gaps below stop and exits at open
- stop wins when stop and RSI exit happen on the same bar
- ignore buy signals while already in position
- force-close open trade at period end

Validate generated artifacts:

- no rows after `2026-06-15`
- no Final Holdout rows used during future optimization
- trade ledger equity links correctly from one trade to the next
- equity curve starts at `3000 USDT`
- summary metrics match trade ledger totals

## Assumptions

- The generated `2026-06-16` row is excluded because the day is incomplete.
- Zero-cost v1 is a diagnostic baseline, not realistic performance.
- All-in sizing is intentionally simple for v1, even though ATR stop distance does not cap account-level risk.
- The notebook remains the interactive research surface; reusable mechanics live in source code.
