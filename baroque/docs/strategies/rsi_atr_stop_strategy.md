# RSI Re-Entry With ATR Stop Loss

## Core Idea

There is no universally best stop loss for an RSI below 30 buy / RSI near 70 sell strategy. The most practical starting point is usually volatility-based, not a fixed percentage stop.

For this setup, use the following starting rule:

**Buy only after RSI crosses back above 30, then set the initial stop loss at:**

```text
Stop = Entry Price - 1.5 to 2.0 x ATR(14)
```

For very volatile assets such as crypto or small-cap stocks, test `2.0` to `3.0 x ATR(14)` instead.

## What ATR Means

ATR stands for Average True Range. It measures how much an asset typically moves over a lookback window, using the largest of:

- Current high minus current low
- Current high minus previous close
- Current low minus previous close

`ATR(14)` means the average true range over the last `14` periods. On a daily chart, that is roughly the average daily price movement over the last `14` trading days. A higher ATR means the asset is currently more volatile, so the stop needs more room.

## Why ATR-Based Stops

RSI below 30 means the asset is traditionally considered oversold, while RSI above 70 is traditionally considered overbought. However, strong trends can keep RSI overbought or oversold for extended periods, so buying just because RSI is below 30 is dangerous.

An ATR-based stop adjusts to the asset's current volatility instead of relying on an arbitrary fixed percentage. This matters because a fixed `5%` stop can be too tight for crypto and too wide for a low-volatility stock.

References:

- [Fidelity: Relative Strength Index](https://www.fidelity.com/learning-center/trading-investing/technical-analysis/technical-indicator-guide/RSI)
- [StockCharts ChartSchool: ATR Trailing Stops](https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/atr-trailing-stops)

## Rule Set

| Rule | Practical setting |
| --- | ---: |
| Entry | RSI falls below 30, then crosses back above 30 |
| Initial stop | Entry - 1.5 to 2.0 x ATR(14) |
| Extra confirmation | Stop should also be below the recent swing low if possible |
| Max risk per trade | 0.5% to 1% of account equity |
| Exit | RSI near 70, or trailing stop once trade moves in profit |
| Skip trade if | Stop distance is too wide or reward/risk is below 1.5:1 |

## Example

Assume:

- Entry price: `100`
- ATR(14): `3`
- Stop multiple: `2 x ATR`

```text
100 - 2(3) = 94
```

The stop loss would be `94`, which is a `6%` downside stop.

## Position Sizing

The stronger version of the stop rule is:

**Stop below the recent swing low, with at least 1.5 to 2.0 ATR of room.**

Then size the position so that, if the stop hits, the trade loses only the predefined risk amount.

Example:

- Account equity: `10,000`
- Risk per trade: `1%`
- Maximum loss: `100`
- Entry price: `100`
- Stop price: `94`
- Risk per unit: `6`

```text
100 / 6 = 16.6
```

So the position should be about `16` units, not more.

## Backtest Parameters

Do not use a fixed `5%` stop across all assets. Use ATR, then backtest the following stop distances on the exact asset and timeframe:

- `1.5 x ATR(14)`
- `2.0 x ATR(14)`
- `2.5 x ATR(14)`

For crypto or other highly volatile assets, also test:

- `3.0 x ATR(14)`
