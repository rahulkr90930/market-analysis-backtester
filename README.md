# market-analysis-backtester (Python)

A compact, extendable backtesting project that identifies undervalued stocks using simple valuation methods (DCF + comparables) and simulates a long-only trading strategy. 

## What this project does
- Loads historical price data from **yfinance** or a **CSV** you select manually.
- Computes simple DCF and comparables-based valuations (naive proxies included).
- Ranks tickers by valuation score (lower = more undervalued).
- Simulates a long-only, equal-weight strategy that rebalances monthly/quarterly.
- Computes performance metrics: cumulative return, annualized return, annual volatility, Sharpe ratio, max drawdown.
- Visualizes portfolio vs benchmark and drawdowns.
- Modular structure so you can replace valuation models, signal generation, and execution rules.

## Tech stack
- Python 3.8+
- pandas, numpy
- matplotlib
- yfinance (data)
- Streamlit (interactive app)
- Jupyter Notebook for step-through analysis
- ipywidgets (optional) for Notebook UI

## Folder structure
```
value-backtester/
├─ app.py
├─ src/
│  ├─ __init__.py
│  ├─ backtester.py
│  └─ valuation.py
├─ analysis_notebook.ipynb
├─ requirements.txt
├─ .gitignore
└─ README.md
```
> **Note:** Keep your CSV **outside** this folder if you want to manually select it in the Notebook. Streamlit app supports CSV upload from your machine.

## Key features
- Multiple data inputs: yfinance API or CSV (manual selection).
- Simple DCF implementation (extendable).
- Comparables P/E estimation (user-provided peers).
- Rebalancing framework (monthly/quarterly).
- Performance analytics: Sharpe ratio, drawdown analysis.
- Visualizations: cumulative returns and drawdown plots.
- Extendable structure for rapid prototyping of new finance/data projects.

## How to run
1. Create a virtualenv and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Run Streamlit:**
   ```bash
   streamlit run app.py
   ```
   - Choose `yfinance` or upload your `CSV` (`Date,Ticker,Adj Close`).

3. **Run the Notebook:**
   - Open `analysis_notebook.ipynb` in Jupyter/VS Code.
   - Use the widgets to select **CSV outside the project folder** or fetch from yfinance.
   - Run the pipeline cell to see stats and charts.


- Add portfolio optimization (risk parity, mean-variance).

## Notes / Warnings
- Valuation implementations here are intentionally simple **proxies** for demonstration and education. Replace with real financial inputs for production use.
- Backtest simplifications (no transaction costs, no slippage, equal-weight allocation) — adjust in `src/backtester.py`.

