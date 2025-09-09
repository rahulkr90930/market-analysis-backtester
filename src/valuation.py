# src/valuation.py
import numpy as np

def dcf_simple(current_cashflow, growth_rate, discount_rate, years=5, terminal_growth=0.02):
    """
    Very simple DCF: project cashflow growing at growth_rate for 'years', then terminal value with perpetual growth.
    current_cashflow: float (last-year free cash flow proxy)
    returns npv value
    """
    cashflows = []
    for i in range(1, years+1):
        cashflows.append(current_cashflow * ((1+growth_rate)**i))
    # terminal value at year N
    terminal = cashflows[-1] * (1+terminal_growth) / (discount_rate - terminal_growth) if discount_rate > terminal_growth else cashflows[-1]
    cashflows.append(terminal)
    discount_factors = [(1+discount_rate)**i for i in range(1, years+2)]
    npv = sum(cf/df for cf,df in zip(cashflows, discount_factors))
    return npv

def comparables_pe(current_eps, peer_pe):
    """
    Estimate price from peer P/E
    """
    return current_eps * peer_pe

def parse_peer_pes(peer_pes_text):
    """
    Parse mapping like "AAPL:25,MSFT:30"
    """
    peer_map = {}
    if not peer_pes_text:
        return peer_map
    try:
        for item in str(peer_pes_text).split(","):
            if ":" in item:
                t,pe = item.split(":")
                t = t.strip().upper()
                if t:
                    peer_map[t] = float(pe)
    except Exception:
        pass
    return peer_map

def score_valuations(tickers, latest_prices, discount_rate=0.08, terminal_growth=0.02, proj_years=5, peer_pes_text=""):
    """
    Build a simple score: lower = better (more undervalued).
    For each ticker:
      - use a naive free cash flow proxy = price / 20 (i.e., FCF yield 5%) OR fallback constant
      - compute dcf implied value and comparables estimate
      - score = (market_price - avg_estimate) / market_price  (lower negative = undervalued)
    Returns dict ticker -> (score, dcf_value, comparable_est)
    """
    peer_map = parse_peer_pes(peer_pes_text)

    out = {}
    for t in tickers:
        price = latest_prices.get(t)
        if price is None or (isinstance(price, float) and np.isnan(price)):
            continue
        # naive proxies (replace with real financials for production)
        proxy_fcf = price / 20.0  # 5% FCF yield proxy
        dcf_val = dcf_simple(proxy_fcf, growth_rate=0.05, discount_rate=discount_rate, years=proj_years, terminal_growth=terminal_growth)

        current_eps = price / 20.0  # placeholder EPS proxy
        peer_pe = peer_map.get(t, np.nan)
        comparable_est = current_eps * peer_pe if (peer_pe is not None and not np.isnan(peer_pe)) else np.nan

        # average estimate (ignore nans)
        estimates = [v for v in [dcf_val, comparable_est] if (v is not None and not (isinstance(v, float) and np.isnan(v)))]
        avg_est = np.mean(estimates) if estimates else dcf_val
        # score: market price - avg_est (negative => undervalued). Normalize by price.
        score = (price - avg_est) / price if price else np.nan
        out[t] = (float(score) if score is not None else np.nan, float(dcf_val), (float(comparable_est) if comparable_est==comparable_est else np.nan))
    return out
