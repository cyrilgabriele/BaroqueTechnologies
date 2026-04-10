# Quant Research Platform Roadmap

## The Core Idea

Start by building a small quant research platform that later connects to Alpaca paper trading.

The order should be:

1. Data pipeline
2. Feature and hypothesis research
3. Backtesting
4. Portfolio and risk rules
5. Paper execution with Alpaca

This is the right sequence because execution is the easy part. Research discipline is the hard part.

## What to Start With

Start with daily U.S. equity data only.

### First Data

Use:

- daily OHLCV bars
- split/dividend-adjusted prices if possible
- a small universe of very liquid names

A good first universe:

- SPY
- QQQ
- then maybe 20-30 large liquid U.S. stocks

### Why This Data First

Because it is:

- clean
- easy to backtest
- directly useful for econometric modeling
- much less messy than news or politician data

## What Not to Start With

Do not start with:

- politician trading data
- news embeddings
- intraday trading
- options
- many alternative datasets at once

These are interesting, but they introduce too much noise too early.

## First Research Question

The first project should be something like:

**Can I predict next-day return or next-day volatility for a small universe of liquid stocks using lagged price/volume information?**

That is narrow, testable, and strongly connected to financial econometrics.

## Best First Strategy Types

Choose one of these to begin:

### Option A: Short-Term Mean Reversion

Example idea:

- after a large move, does the stock partially reverse the next day?

### Option B: Volatility Forecasting

Example idea:

- can rolling volatility or realized volatility features forecast tomorrow's volatility?

### Option C: Simple Momentum

Example idea:

- do recent winners continue to outperform over a short horizon?

Suggested ranking:

1. mean reversion
2. volatility forecasting
3. momentum
4. news/event models
5. politician/event models

## Exact Build Order

## Phase 1: Build the Boring Foundation

Build a clean system for:

- loading historical daily data into `data/`
- creating a clean panel dataset
- generating lagged features
- defining targets
- backtesting without look-ahead bias
- evaluating results

### Data in This Phase

Only:

- daily prices
- volume
- maybe market index data like SPY

### Features in This Phase

Start very simple:

- lagged returns
- rolling mean return
- rolling volatility
- rolling volume or abnormal volume
- overnight return
- intraday return
- distance from recent highs/lows

### Targets in This Phase

Use one of:

- next-day return
- next-day return sign
- next-day realized volatility

## Phase 2: Build One Real Econometric Strategy

Choose one hypothesis and test it properly.

Example:

**Hypothesis:** large negative moves in liquid stocks mean-revert over the next trading day.

Then build:

- a feature set
- a target
- a train/test split
- a walk-forward backtest
- transaction cost assumptions
- performance metrics

### Models Here

Keep models simple first:

- OLS
- logistic regression
- lasso/ridge
- maybe GARCH if doing volatility forecasting

The key is not fancy models. The key is clean testing.

## Phase 3: Add Portfolio Construction

Once the signal shows some promise, convert it into positions.

Define:

- how many names to hold
- position sizing
- max exposure
- turnover limit
- basic risk constraints

Examples:

- long top 5 signals
- long strongest reversion candidates
- volatility-targeted position sizing

This is where the system starts to resemble real asset management.

## Phase 4: Connect Alpaca Paper Trading

Only after backtesting works.

Then build:

- signal-to-order translation
- paper order execution
- position reconciliation
- daily logs
- PnL tracking

At this point Alpaca is just the execution layer.
It should not be where the research logic lives.

## When to Add News

Add news only after the price-based baseline works.

### First News Data to Use

Use structured news fields first, not embeddings.

Good first news features:

- number of articles today
- abnormal news volume
- recency of last article
- source count
- simple sentiment score if available
- category/topic tags

### Why Not Embeddings First

Because embeddings are powerful but dangerous early:

- harder to debug
- easier to overfit
- easy to accidentally leak future information
- distract from learning the research process

So:

1. structured news features first
2. embeddings later

## When to Add Politician Data

Only later, as a side research project.

Use politician data as an event-study dataset, not as the first trading strategy.

### Better Use of Politician Data

Ask:

- what happens after a disclosure becomes public?
- do buys and sells behave differently?
- is there any post-disclosure drift?
- does the effect depend on sector or market cap?

This makes it a clean research extension rather than a vague story-driven strategy.

## The Right System Architecture

The project should be organized around these building blocks:

- raw data
- processed data
- features
- hypotheses
- models
- backtests
- portfolio rules
- execution

Important principle:

**Research first, broker second.**

## What Data to Collect First

If the goal is the cleanest possible first setup, collect:

### Stage 1 Data

- daily OHLCV for SPY, QQQ, and 20-30 liquid U.S. stocks
- corporate action adjustments if available
- benchmark returns

### Stage 2 Data

- same daily price data, but longer history
- maybe sector ETFs for context
- maybe risk-free rate later if needed

### Stage 3 Data

- financial news headlines and timestamps
- article counts, tags, and sentiment-like features

### Stage 4 Data

- politician trade disclosures
- mapped to stock, disclosure date, transaction type, and reported size

## What the First Finished Project Should Look Like

A good first complete system would:

1. download daily stock data
2. store it in `data/raw/`
3. clean and align it into `data/processed/`
4. compute econometric features
5. define a next-day target
6. fit simple models
7. run walk-forward backtests
8. apply transaction costs
9. generate positions
10. send paper orders to Alpaca

That alone is already a serious and valuable project.

## In One Sentence

Start with a daily equity econometrics lab based on price and volume, get one simple strategy working end-to-end, then add news, and only later explore politician disclosures.

## Strongest Recommendation

If forced to pick one direction:

**Start with daily mean-reversion or volatility forecasting on 20-30 liquid U.S. stocks using only price and volume data.**

That is the best balance of:

- feasible
- rigorous
- educational
- relevant to the course
- extensible later into news and event strategies

## Possible Next Step

This can be turned into a concrete implementation roadmap for the repository, including:

- folder structure
- first datasets
- first hypothesis
- first features
- first backtest design
