from __future__ import annotations
import numpy as np
import pandas as pd


def _clean_returns(returns):
    out = returns.apply(pd.to_numeric, errors="coerce")
    return out.replace([np.inf, -np.inf], np.nan).dropna(how="all")


def portfolio_returns(returns, weights):
    r = _clean_returns(returns)
    w = pd.Series(weights, dtype=float).reindex(r.columns).fillna(0.0)
    if w.abs().sum() == 0:
        raise ValueError("Danh mục chưa có tỷ trọng hợp lệ.")
    w = w / w.sum()
    return r.dropna(how="any").mul(w, axis=1).sum(axis=1).dropna()


def max_drawdown(series):
    wealth = (1 + series).cumprod()
    return float((wealth / wealth.cummax() - 1).min())


def downside_deviation(series, target=0.0):
    r = pd.to_numeric(series, errors="coerce").dropna()
    downside = np.minimum(r - target, 0.0)
    return float(np.sqrt(np.mean(downside ** 2) * 252))


def calculate_portfolio_risk(returns, weights, benchmark_returns=None, risk_free_rate=0.04):
    r = _clean_returns(returns)
    w = pd.Series(weights, dtype=float).reindex(r.columns).fillna(0.0)
    if w.sum() == 0:
        raise ValueError("Tổng tỷ trọng danh mục bằng 0.")
    w = w / w.sum()
    pr = portfolio_returns(r, w)
    if len(pr) < 2:
        raise ValueError("Chưa đủ dữ liệu lịch sử để tính các chỉ tiêu danh mục.")

    rf = float(risk_free_rate)
    daily_rf = (1.0 + rf) ** (1 / 252) - 1 if rf > -1 else rf / 252
    annual_arithmetic_return = float(pr.mean() * 252)
    annual_geometric_return = float((1 + pr).prod() ** (252 / len(pr)) - 1)
    annual_vol = float(pr.std(ddof=1) * np.sqrt(252))
    sharpe = (annual_arithmetic_return - rf) / annual_vol if annual_vol > 0 else np.nan
    downside = downside_deviation(pr, target=daily_rf)
    sortino = (annual_arithmetic_return - rf) / downside if downside > 0 else np.nan
    mdd = max_drawdown(pr)
    calmar = (annual_geometric_return - rf) / abs(mdd) if mdd < 0 else np.nan

    var95 = float(pr.quantile(0.05))
    tail = pr[pr <= var95]
    cvar95 = float(tail.mean()) if len(tail) else var95

    beta = tracking_error = information_ratio = benchmark_annual_return = active_return = np.nan
    jensen_alpha = treynor = r_squared = active_t_stat = m2 = np.nan

    if benchmark_returns is not None:
        b = pd.to_numeric(benchmark_returns, errors="coerce").rename("benchmark")
        j = pd.concat([pr.rename("portfolio"), b], axis=1).dropna()
        if len(j) >= 20 and j["benchmark"].var(ddof=1) > 0:
            p = j["portfolio"]
            bm = j["benchmark"]
            beta = float(p.cov(bm) / bm.var(ddof=1))
            r_squared = float(p.corr(bm) ** 2)
            active = p - bm
            tracking_error = float(active.std(ddof=1) * np.sqrt(252))
            information_ratio = float(active.mean() * 252 / tracking_error) if tracking_error > 0 else np.nan
            portfolio_ann = float((1 + p).prod() ** (252 / len(j)) - 1)
            benchmark_annual_return = float((1 + bm).prod() ** (252 / len(j)) - 1)
            active_return = portfolio_ann - benchmark_annual_return
            jensen_alpha = float((p.mean() - daily_rf) * 252 - beta * (bm.mean() - daily_rf) * 252)
            treynor = (annual_arithmetic_return - rf) / beta if np.isfinite(beta) and beta > 0 else np.nan
            active_t_stat = float(active.mean() / (active.std(ddof=1) / np.sqrt(len(active)))) if active.std(ddof=1) > 0 else np.nan
            benchmark_vol = float(bm.std(ddof=1) * np.sqrt(252))
            m2 = float(rf + sharpe * benchmark_vol) if np.isfinite(sharpe) else np.nan

    covariance = r.cov() * 252
    marginal = covariance.dot(w)
    variance = float(w.dot(covariance).dot(w))
    risk_contribution = w * marginal / variance if variance > 0 else pd.Series(np.nan, index=w.index)
    hhi = float((w[w != 0] ** 2).sum())
    effective_positions = 1 / hhi if hhi > 0 else np.nan

    return {
        "portfolio_returns": pr,
        "weights": w,
        "annual_return": annual_geometric_return,
        "annual_arithmetic_return": annual_arithmetic_return,
        "annual_volatility": annual_vol,
        "sharpe": sharpe,
        "sortino": sortino,
        "max_drawdown": mdd,
        "calmar": calmar,
        "var_95_daily": var95,
        "cvar_95_daily": cvar95,
        "beta": beta,
        "tracking_error": tracking_error,
        "information_ratio": information_ratio,
        "benchmark_annual_return": benchmark_annual_return,
        "active_return": active_return,
        "jensen_alpha": jensen_alpha,
        "treynor": treynor,
        "r_squared": r_squared,
        "active_t_stat": active_t_stat,
        "m2": m2,
        "risk_contribution": risk_contribution,
        "correlation": r.corr(),
        "concentration_hhi": hhi,
        "effective_positions": effective_positions,
        "risk_free_rate": rf,
        "observations": len(pr),
    }
