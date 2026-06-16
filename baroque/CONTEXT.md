# Baroque

Baroque is the bounded context for building a quant research platform from historical market data through research, backtesting, portfolio/risk rules, and later paper execution.

## Language

**Baroque**:
The quant research platform bounded context in this repository.
_Avoid_: AFML, generic finance workspace

**Raw Bar**:
A provider-ingested OHLC or OHLCV market data record before Baroque validates and normalizes it for research.
_Avoid_: Bar, raw row, provider row

**Cleaned Panel**:
A validated, normalized, strategy-neutral market data dataset used as the base for research.
_Avoid_: Feature panel, signal dataset

**Strategy Feature Panel**:
A strategy-specific dataset derived from a **Cleaned Panel** by adding the indicators and helper columns needed by one strategy.
_Avoid_: Cleaned panel, shared feature set

## Relationships

- **Baroque** may use AFML concepts as reference material, but AFML is not part of the **Baroque** bounded context.
- A **Raw Bar** may have provider-specific fields until it is cleaned.
- A **Cleaned Panel** is shared data engineering output and must stay strategy-neutral.
- A **Strategy Feature Panel** belongs to one strategy and may add indicators such as RSI, ATR, signals, and initial stop prices.

## Example dialogue

> **Dev:** "Should the AFML chapter scaffolds define the platform language?"
> **Domain expert:** "No. **Baroque** defines the product context; AFML is reference material until a concept is deliberately brought into Baroque."
>
> **Dev:** "Can Binance BTC data and Alpaca ETF data both produce **Raw Bars** if their columns differ?"
> **Domain expert:** "Yes. They are **Raw Bars** until Baroque validates and normalizes them for research."
>
> **Dev:** "Should RSI and ATR be added to the **Cleaned Panel**?"
> **Domain expert:** "No. The **Cleaned Panel** stays strategy-neutral; RSI and ATR belong in the RSI/ATR **Strategy Feature Panel**."

## Flagged ambiguities

- The repository contains both `afml/` and `baroque/`; resolved: **Baroque** is the first bounded context to document and implement.
- "bar" was used for both provider-ingested records and cleaned research records; resolved: provider-ingested records are **Raw Bars**.
- "cleaned panel" was previously discussed as a possible shared feature base; resolved: a **Cleaned Panel** contains validated market data only, while strategy-specific indicators belong in a **Strategy Feature Panel**.
