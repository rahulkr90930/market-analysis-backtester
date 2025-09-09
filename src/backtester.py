# src/backtester.py
import pandas as pd
import numpy as np

class Backtester:
    def __init__(self, price_df: pd.DataFrame):
        """
        price_df: DataFrame indexed by date, columns are tickers, values are adj close prices.
        """
        self.prices = price_df.sort_index().ffill().dropna(axis=1, how='all')
        self.dates = self.prices.index

    def run_strategy(self, valuation_scores: dict, top_n=5, rebalance="M", risk_free_annual=0.04):
        """
        valuation_scores: dict ticker -> (score, dcf_val, comparable_est)
        strategy: at each rebalance date choose top_n tickers with lowest score, equal weight, long-only.
        rebalance: "M" monthly or "Q" quarterly
        risk_free_annual: annual risk-free rate for Sharpe calculation (e.g., 0.04 = 4%)
        """
        price = self.prices
        returns = price.pct_change().fillna(0)
        # build selection series at each period
        rebal_dates = pd.Series(1, index=price.resample(rebalance).first().index)
        rebal_dates = list(rebal_dates.index)

        # compute score series
        scores = {t: valuation_scores.get(t, (np.nan, None, None))[0] for t in price.columns}
        # At each rebal date pick top N by score ascending (lowest = most undervalued)
        holdings_map = {}
        for d in rebal_dates:
            # choose by available tickers at that date (non-NaN)
            # the 'd' might not be an exact trading date; get nearest prior index
            if d not in price.index:
                # get index location of closest date <= d
                prior_idx = price.index.get_indexer([d], method="pad")
                if prior_idx[0] == -1:
                    continue
                d_eff = price.index[prior_idx[0]]
            else:
                d_eff = d
            avail = price.loc[d_eff].dropna().index.tolist()
            # rank avail by score
            ranked = sorted([a for a in avail if a in scores and not pd.isna(scores[a])], key=lambda x: scores.get(x, np.nan))
            selected = ranked[:top_n]
            holdings_map[d_eff] = selected

        # forward fill holdings
        holdings_series = pd.Series(index=price.index, dtype=object)
        current = []
        last_reb_date = None
        for dt in price.index:
            # if dt is a rebalance date (or next market day) update current
            valid_reb = [r for r in holdings_map.keys() if r <= dt]
            if valid_reb:
                last_reb_date = max(valid_reb)
                current = holdings_map.get(last_reb_date, current)
            holdings_series.loc[dt] = current

        # compute portfolio and benchmark returns
        port_ret = []
        bench_ret = returns.mean(axis=1)  # equal weight benchmark across all available tickers
        for dt in price.index:
            sel = holdings_series.loc[dt]
            if not sel:
                port_ret.append(0.0)
            else:
                # equally weight selected; ignore missing for date
                day_ret = returns.loc[dt, sel].mean()
                port_ret.append(day_ret)

        port_ret = pd.Series(port_ret, index=price.index).fillna(0)
        cum_port = (1+port_ret).cumprod()
        cum_bench = (1+bench_ret).cumprod()

        # stats
        ann_factor = 252
        ann_return = (cum_port.iloc[-1])**(ann_factor/len(cum_port)) - 1 if len(cum_port)>0 else np.nan
        ann_vol = port_ret.std()*np.sqrt(ann_factor)
        # Sharpe vs risk-free
        if port_ret.std() > 0:
            sharpe = (port_ret.mean()*ann_factor - risk_free_annual) / (port_ret.std()*np.sqrt(ann_factor))
        else:
            sharpe = np.nan

        rolling_max = cum_port.cummax()
        drawdown = (cum_port - rolling_max) / rolling_max
        max_dd = drawdown.min()

        bench_rm = cum_bench.cummax()
        bench_dd = (cum_bench - bench_rm) / bench_rm

        df = pd.DataFrame({
            "portfolio_return": port_ret,
            "benchmark_return": bench_ret,
            "cum_portfolio": cum_port,
            "cum_benchmark": cum_bench,
            "holdings": holdings_series,
            "portfolio_drawdown": drawdown,
            "benchmark_drawdown": bench_dd
        })

        stats = {
            "annual_return": float(ann_return) if pd.notna(ann_return) else None,
            "annual_vol": float(ann_vol) if pd.notna(ann_vol) else None,
            "sharpe": float(sharpe) if pd.notna(sharpe) else None,
            "max_drawdown": float(max_dd) if pd.notna(max_dd) else None,
            "final_cum_return": float(cum_port.iloc[-1]) if len(cum_port)>0 else None
        }
        return df, stats
