# app.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf
from datetime import datetime
from src.backtester import Backtester
from src.valuation import score_valuations

st.set_page_config(layout="wide", page_title="Value Backtester")

st.title("Value-based Backtester")
st.markdown("Upload CSV or fetch historical data via yfinance. The app runs a simple undervalued-stock strategy and shows performance vs market.")

# --- Data input
st.sidebar.header("Data input")
data_source = st.sidebar.selectbox("Data source", ["yfinance", "csv"])
tickers_input = st.sidebar.text_input("Tickers (comma separated)", value="AAPL,MSFT,AMD")
start = st.sidebar.date_input("Start date", value=pd.to_datetime("2018-01-01"))
end = st.sidebar.date_input("End date", value=pd.to_datetime(datetime.today().date()))
rebal_freq = st.sidebar.selectbox("Rebalance frequency", ["Monthly", "Quarterly"])
top_n = st.sidebar.number_input("Top N undervalued to buy", min_value=1, max_value=20, value=5)

uploaded_file = None
if data_source == "csv":
    uploaded_file = st.sidebar.file_uploader(
        "Upload price CSV (Date,Ticker,Adj Close/Close/Price)",
        type=["csv"]
    )

# --- Load data
@st.cache_data
def load_yfinance(tickers, start, end):
    tickers = [t.strip().upper() for t in tickers.split(",") if t.strip() != ""]
    data = {}
    for t in tickers:
        df = yf.download(t, start=start, end=end, progress=False)
        if df.empty:
            continue

        # Handle both single-level and multi-level column cases
        if isinstance(df.columns, pd.MultiIndex):
            if ("Adj Close", t) in df.columns:
                series = df[("Adj Close", t)]
            elif ("Close", t) in df.columns:
                series = df[("Close", t)]
            elif ("Price", "Close") in df.columns:  # new yfinance format
                series = df[("Price", "Close")]
            else:
                continue
        else:
            if "Adj Close" in df.columns:
                series = df["Adj Close"]
            elif "Close" in df.columns:
                series = df["Close"]
            elif "Price" in df.columns:
                series = df["Price"]
            else:
                continue

        data[t] = series.rename(t)

    if not data:
        return pd.DataFrame()

    price_df = pd.concat(data.values(), axis=1)
    price_df.index = pd.to_datetime(price_df.index)
    return price_df


def load_csv(uploaded_file):
    raw = pd.read_csv(uploaded_file, parse_dates=["Date"])
    cols = raw.columns.str.lower()

    # normalize column naming
    if "adj close" in cols:
        value_col = raw.columns[cols == "adj close"][0]
    elif "close" in cols:
        value_col = raw.columns[cols == "close"][0]
    elif "price" in cols:
        value_col = raw.columns[cols == "price"][0]
    else:
        st.error("CSV must contain one of: Adj Close, Close, or Price")
        return pd.DataFrame()

    pivot = raw.pivot(index="Date", columns="Ticker", values=value_col)
    return pivot.sort_index()


# --- Select data source
if data_source == "yfinance":
    price_df = load_yfinance(tickers_input, start, end)
else:
    if uploaded_file is not None:
        price_df = load_csv(uploaded_file)
    else:
        st.warning("Upload CSV to proceed.")
        st.stop()

if price_df.empty:
    st.error("No price data found. Check tickers / CSV format.")
    st.stop()

st.write("Price data sample")
st.dataframe(price_df.tail(5))

# --- Valuation inputs
st.sidebar.header("Valuation settings (simple)")
risk_free = st.sidebar.number_input("Risk-free rate (annual %)", value=4.0, help="Used for Sharpe ratio")
discount_rate = st.sidebar.number_input("Discount rate (annual %)", value=8.0)
terminal_growth = st.sidebar.number_input("Terminal growth rate %", value=2.0)
projection_years = st.sidebar.number_input("Projection years", min_value=1, max_value=10, value=5)

# --- Comparables mapping
st.sidebar.header("Comparables / manual")
peer_pes = st.sidebar.text_area("Peer P/E map (format: TICKER:PE, comma)", "AAPL:25,MSFT:30,AMD:40")

# --- Valuation scoring
st.write("Running simple valuation scoring (demo) ...")
valuation_scores = score_valuations(
    price_df.columns.tolist(),
    price_df.iloc[-1].to_dict(),
    discount_rate / 100,
    terminal_growth / 100,
    int(projection_years),
    peer_pes
)

st.write(
    pd.DataFrame(valuation_scores)
    .T.rename(columns={0: "score", 1: "dcf_value", 2: "comparables_pe_est"})
    .sort_values("score")
    .head()
)

# --- Backtest
st.write("Running backtest...")
freq = "M" if rebal_freq == "Monthly" else "Q"
bt = Backtester(price_df)
portfolio, stats = bt.run_strategy(
    valuation_scores,
    top_n=top_n,
    rebalance=freq,
    risk_free_annual=risk_free / 100.0
)
st.write("Backtest stats")
st.json(stats)

# --- Plots
st.subheader("Performance vs equal-weight market")
fig, ax = plt.subplots(figsize=(10, 5))
portfolio['cum_portfolio'].plot(ax=ax, label="Strategy")
portfolio['cum_benchmark'].plot(ax=ax, label="Benchmark (equal weight)")
ax.legend()
ax.set_title("Cumulative returns")
st.pyplot(fig)

st.subheader("Drawdown (Strategy)")
fig2, ax2 = plt.subplots(figsize=(10, 3))
portfolio['portfolio_drawdown'].plot(ax=ax2)
ax2.set_title("Portfolio drawdown")
st.pyplot(fig2)

st.subheader("Holdings over time (sample)")
st.dataframe(portfolio[['holdings']].tail(10))
