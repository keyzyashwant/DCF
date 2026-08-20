# DCF Valuation Engine — Indian Equities

An automated Discounted Cash Flow (DCF) valuation pipeline for NSE/BSE-listed companies. It pulls financial statements via `yfinance`, computes fundamental ratios and a CAPM-based WACC, runs a two-stage DCF model, persists results to SQLite, and generates a bull/bear investment narrative using an LLM (Groq / Llama 3.3).

Built as part of an ongoing portfolio of quantitative finance + AI engineering projects focused on Indian equity markets.

---

## Overview

Given a ticker (e.g. `TCS.NS`), the pipeline:

1. **Collects** raw financial statements (P&L, balance sheet, cash flow, key info) from Yahoo Finance.
2. **Computes** profitability, leverage, operating, and valuation ratios.
3. **Derives** DCF inputs — CAPM cost of equity, after-tax cost of debt, and WACC.
4. **Runs a two-stage DCF**: an initial high-growth phase fading into a terminal growth phase, discounted at WACC, with a Gordon Growth terminal value.
5. **Cross-checks** the valuation using two independent FCF methodologies — reported FCF (from yfinance) vs. calculated FCF (Operating Cash Flow − CapEx).
6. **Persists** every run (ratios + DCF summary, timestamped) to a local SQLite database.
7. **Synthesizes** the stored ratios and valuation output into a bull case / bear case narrative via an LLM.

---

## Architecture

```
                     ┌─────────────────────┐
                     │   FinancialCollector │  ← yfinance (P&L, BS, CF, Info)
                     └──────────┬───────────┘
                                │
              ┌─────────────────┼─────────────────┐
              ▼                 ▼                 ▼
     FundamentalRatios   DCFParameters      (shared source data)
     (Profitability,     (CAPM → WACC,
      Leverage,           input validation)
      Operating,
      Valuation)                │
              │                 ▼
              │                DCF
              │        (2-stage FCF projection,
              │         discounting, terminal value,
              │         calculated vs. reported bands)
              │                 │
              └────────┬────────┘
                        ▼
                 DataBaseManager (SQLite)
                        │
                        ▼
                  GROQAnalyst (Llama 3.3)
                        │
                        ▼
              Bull Case / Bear Case narrative
```

---

## Methodology

**Cost of Equity (CAPM)**
```
Ke = Risk-Free Rate + Beta × Equity Risk Premium
```

**Cost of Debt**
```
Kd = (Interest Expense / Total Debt) × (1 − Effective Tax Rate)
```

**WACC**
```
WACC = (We × Ke) + (Wd × Kd)
```
weighted by book-value equity and debt from the balance sheet.

**Two-Stage FCF Projection**
- Phase 1 (first half of the forecast horizon): grows FCF at the user-supplied *initial* growth rate.
- Phase 2 (second half): fades growth to the user-supplied *final* growth rate.
- Each year's FCF is discounted back at WACC.

**Terminal Value**
```
TV = FCF_final × (1 + Terminal Growth) / (WACC − Terminal Growth)
```
discounted back to present value at WACC over the full forecast horizon.

**Dual FCF Basis** — the model computes intrinsic value two ways and reports both:
- *Reported*: yfinance's own "Free Cash Flow" line, averaged over the last two fiscal years.
- *Calculated*: Operating Cash Flow − |Capital Expenditure|, averaged over the last two fiscal years.

**Margin of Safety** — the point estimate intrinsic value is bracketed into a lower/upper band using a user-supplied margin of safety (e.g. ±10%).

---

## Tech Stack

| Layer | Tool |
|---|---|
| Market data | `yfinance` |
| Data wrangling | `pandas`, `numpy` |
| Persistence | `sqlite3` |
| LLM synthesis | `groq` (Llama 3.3 70B) |
| Language | Python 3.10+ |

---

## Project Structure

```
.
├── analyst.py             # Entry point — orchestrates the full pipeline
├── dataCollector.py        # FinancialCollector — yfinance wrapper
├── fundamentalRatios.py   # FundamentalRatios — profitability/leverage/operating/valuation ratios
├── parametersForDCF.py    # DCFParameters — CAPM/WACC + input validation
├── DCF.py                  # DCF — two-stage FCF projection & valuation
├── DBManager.py           # DataBaseManager — SQLite persistence layer
├── LLMAnalyst.py           # GROQAnalyst — LLM narrative generation
└── requirements.txt
```

---

## Setup

```bash
git clone <repo-url>
cd dcf-valuation-engine
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Environment variables** — create a `.env` file (or export directly):

```
GROQ_API_KEY=your_groq_api_key_here
```

Get a free API key at [console.groq.com](https://console.groq.com).

---

## Usage

```python
from analyst import analyse

dcf_params = {
    'growth_rate_i'       : 10,   # initial-phase growth rate (%)
    'growth_rate_f'       : 7,    # final-phase (fade) growth rate (%)
    'no_of_years'         : 10,   # forecast horizon (must be > 5)
    'terminal_growth_rate': 5,    # perpetuity growth rate (%), must be < WACC
    'risk_free_rate'      : 7,    # for CAPM (%)
    'erp'                 : 6,    # equity risk premium (%)
    'margin_of_safety'    : 10,   # ± band around intrinsic value (%)
}

result = analyse("TCS.NS", dcf_params, api_key="your_groq_api_key")
print(result)
```

Or run directly:

```bash
python analyst.py
```

**Input constraints** (enforced by `DCFParameters`):
- `no_of_years` must be greater than 5.
- `terminal_growth_rate`, `risk_free_rate`, `growth_rate_i`, `growth_rate_f`, `erp` must each be in `[0, 15)`.
- `margin_of_safety` must be in `(5, 12)`.
- `terminal_growth_rate` must be strictly less than the computed WACC.

---

## Database Schema

**`ratios`**

| Column | Type | Description |
|---|---|---|
| ticker | TEXT | e.g. `TCS.NS` |
| category | TEXT | `profitability` / `leverage` / `operating` / `valuation` |
| metric | TEXT | Ratio name |
| value | REAL | Computed value |
| timestamp | TEXT | ISO 8601 run timestamp |

**`dcf_summary`**

| Column | Type | Description |
|---|---|---|
| ticker | TEXT | e.g. `TCS.NS` |
| metric | TEXT | `Intrinsic Price` / `Lower Band` / `Upper Band` |
| value | REAL | Computed value (₹ per share) |
| timestamp | TEXT | ISO 8601 run timestamp |

Each `analyse()` call writes a new timestamped snapshot rather than overwriting prior runs, so historical valuations for a ticker accumulate over time.

---

## Sample Output

```
BULLISH VIEW:
[LLM-generated case for buying, grounded in the stored ratios and DCF bands]

BEARISH VIEW:
[LLM-generated case for caution, grounded in the stored ratios and DCF bands]
```

---

## Known Limitations

- Relies entirely on `yfinance`'s statement schema, which varies by sector and can change without notice — no schema-validation fallback yet.
- Financial data is fetched independently by each stage of the pipeline rather than cached/shared, resulting in redundant external calls per run.
- WACC weights use book-value equity rather than market-value equity.
- No automated test suite yet — valuations are not currently regression-tested against known-good figures.
- Single-ticker, synchronous execution — not yet designed for batch runs across an index (e.g. Nifty 50).


## Disclaimer

This tool is for educational and research purposes only. It does not constitute investment advice. DCF valuations are highly sensitive to input assumptions (growth rates, WACC, terminal growth) — always sanity-check outputs against your own independent analysis before making investment decisions.