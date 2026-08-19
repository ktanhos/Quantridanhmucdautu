from __future__ import annotations
import numpy as np
import pandas as pd

try:
    from scipy.optimize import minimize
except ImportError:
    minimize = None


def _annual_stats(returns):
    r = returns.apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna(how="all")
    return r, r.mean() * 252, r.cov() * 252


def _feasible_bounds(n, max_weight):
    max_weight = float(max_weight)
    if max_weight <= 0:
        raise ValueError("Giới hạn tỷ trọng phải lớn hơn 0.")
    if n * max_weight < 1 - 1e-10:
        raise ValueError(f"Không thể phân bổ đủ 100% với {n} mã và giới hạn {max_weight:.0%}/mã.")
    return [(0.0, max_weight)] * n


def _initial_weights(n, max_weight):
    base = np.ones(n) / n
    if np.max(base) <= max_weight + 1e-12:
        return base
    w = np.zeros(n)
    remaining = 1.0
    for i in range(n):
        value = min(max_weight, remaining)
        w[i] = value
        remaining -= value
        if remaining <= 1e-12:
            break
    return w / w.sum()


def _project_weights(w, max_weight):
    w = np.maximum(np.asarray(w, dtype=float), 0.0)
    n = len(w)
    _feasible_bounds(n, max_weight)
    if w.sum() <= 0:
        return _initial_weights(n, max_weight)
    w = w / w.sum()
    result = np.zeros(n)
    active = np.ones(n, dtype=bool)
    remaining = 1.0
    for _ in range(n + 1):
        idx = np.where(active)[0]
        if len(idx) == 0:
            break
        base = w[idx]
        proposal = base / base.sum() * remaining if base.sum() > 0 else np.ones(len(idx)) * remaining / len(idx)
        over = proposal > max_weight + 1e-12
        if not over.any():
            result[idx] = proposal
            remaining = 0.0
            break
        capped = idx[over]
        result[capped] = max_weight
        active[capped] = False
        remaining -= max_weight * len(capped)
    if remaining > 1e-8:
        idx = np.where(active)[0]
        if len(idx) == 0:
            raise ValueError("Không thể phân bổ đủ 100% với giới hạn hiện tại.")
        result[idx] += remaining / len(idx)
    return result / result.sum()


def _metrics(w, mu, cov, rf=0.04):
    ret = float(w @ mu)
    vol = float(np.sqrt(max(w @ cov @ w, 0.0)))
    sh = (ret - rf) / vol if vol > 0 else np.nan
    return ret, vol, sh


def _solve_slsqp(objective, x0, bounds, constraints, fallback):
    if minimize is None:
        return fallback
    try:
        result = minimize(objective, x0=x0, method="SLSQP", bounds=bounds, constraints=constraints, options={"maxiter": 1000, "ftol": 1e-10})
        if result.success and np.isfinite(result.fun):
            w = np.asarray(result.x, dtype=float)
            if abs(w.sum() - 1.0) < 1e-6:
                return w / w.sum()
    except Exception:
        pass
    return fallback


def optimize_portfolios(returns, max_weight=0.10, risk_free_rate=0.04, target_return=None):
    r, mu, cov = _annual_stats(returns)
    n = len(mu)
    names = list(mu.index)
    if n < 2:
        raise ValueError("Cần ít nhất 2 cổ phiếu để tối ưu hóa danh mục.")
    requested_max_weight = float(max_weight)
    constraint_feasible = n * requested_max_weight >= 1 - 1e-10
    effective_max_weight = requested_max_weight
    if not constraint_feasible:
        raise ValueError(f"Không thể xây dựng danh mục 100% cổ phiếu với {n} mã và giới hạn {requested_max_weight:.0%}/mã. Cần ít nhất {int(np.ceil(1 / requested_max_weight))} mã.")

    bounds = _feasible_bounds(n, effective_max_weight)
    x0 = _initial_weights(n, effective_max_weight)
    equality = {"type": "eq", "fun": lambda w: np.sum(w) - 1.0}
    constraints = [equality]
    cov_values = cov.values
    mu_values = mu.values

    w_mv_fallback = _project_weights(np.linalg.pinv(cov_values + np.eye(n) * 1e-8) @ np.ones(n), effective_max_weight)
    w_mv = _solve_slsqp(lambda w: float(w @ cov_values @ w), x0, bounds, constraints, w_mv_fallback)

    order = np.argsort(mu_values)[::-1]
    w_max = np.zeros(n)
    remaining = 1.0
    for idx in order:
        allocation = min(effective_max_weight, remaining)
        w_max[idx] = allocation
        remaining -= allocation
        if remaining <= 1e-12:
            break
    w_max = w_max / w_max.sum()

    def neg_sharpe(w):
        ret, vol, _ = _metrics(w, mu_values, cov_values, risk_free_rate)
        return -(ret - risk_free_rate) / vol if vol > 1e-12 else 1e6

    w_opt = _solve_slsqp(neg_sharpe, x0, bounds, constraints, w_mv.copy())
    target_feasible = False
    target_value = None if target_return is None else float(target_return)
    if target_value is not None:
        target_constraint = {"type": "ineq", "fun": lambda w, target=target_value: float(w @ mu_values - target)}
        w_target = _solve_slsqp(lambda w: float(w @ cov_values @ w), x0, bounds, [equality, target_constraint], w_mv)
        if float(w_target @ mu_values) >= target_value - 1e-6:
            w_opt = w_target
            target_feasible = True

    portfolios = [("Phân bổ tham chiếu", np.ones(n) / n), ("Minimum Variance", w_mv), ("Optimal Risky", w_opt), ("Maximum Return", w_max)]
    rows = []
    for label, w in portfolios:
        ret, vol, sh = _metrics(w, mu_values, cov_values, risk_free_rate)
        rows.append({"Danh mục": label, "Lợi suất ước tính": ret, "Độ biến động ước tính": vol, "Sharpe Ratio ước tính": sh})

    return {
        "returns": r,
        "expected_returns": mu,
        "covariance": cov,
        "summary": pd.DataFrame(rows).set_index("Danh mục"),
        "weights": pd.DataFrame({label: w for label, w in portfolios}, index=names),
        "requested_max_weight": requested_max_weight,
        "effective_max_weight": effective_max_weight,
        "universe_size": n,
        "constraint_feasible": constraint_feasible,
        "required_assets": int(np.ceil(1 / requested_max_weight)),
        "target_feasible": target_feasible,
        "target_return": target_value,
        "risk_free_rate": float(risk_free_rate),
    }
