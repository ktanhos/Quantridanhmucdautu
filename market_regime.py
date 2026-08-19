from __future__ import annotations

from dataclasses import dataclass
import numpy as np
import pandas as pd


@dataclass
class RegimeResult:
    score: float
    regime: str
    confidence: str
    equity_min: float
    equity_max: float
    components: pd.DataFrame
    indicators: dict


def _series(df: pd.DataFrame, col: str) -> pd.Series:
    s = pd.to_numeric(df[col], errors="coerce").dropna().astype(float)
    return s.sort_index()


def _score_linear(value: float, low: float, high: float) -> float:
    if not np.isfinite(value):
        return 50.0
    return float(np.clip((value - low) / (high - low) * 100.0, 0.0, 100.0))


def _score_ratio(value: float, neutral: float, strong: float) -> float:
    if not np.isfinite(value):
        return 50.0
    if strong > neutral:
        return float(np.clip((value - neutral) / (strong - neutral) * 50.0 + 50.0, 0.0, 100.0))
    return float(np.clip(100.0 - (value - strong) / (neutral - strong) * 50.0, 0.0, 100.0))


def _trend_score(index: pd.Series) -> tuple[float, dict]:
    ma50 = index.rolling(50).mean()
    ma200 = index.rolling(200).mean()
    r50 = index.iloc[-1] / ma50.iloc[-1] if len(ma50.dropna()) else np.nan
    r200 = index.iloc[-1] / ma200.iloc[-1] if len(ma200.dropna()) else np.nan
    slope = ma50.iloc[-1] / ma50.iloc[-21] - 1 if len(ma50.dropna()) >= 21 else np.nan
    s1 = _score_ratio(r50, 0.98, 1.04)
    s2 = _score_ratio(r200, 0.98, 1.06)
    s3 = _score_linear(slope, -0.05, 0.05)
    return 0.4 * s1 + 0.4 * s2 + 0.2 * s3, {
        "VNINDEX / MA50": r50,
        "VNINDEX / MA200": r200,
        "MA50 21D change": slope,
    }


def _breadth_score(stock_prices: pd.DataFrame) -> tuple[float, dict]:
    if stock_prices is None or stock_prices.empty:
        return 50.0, {}
    above50 = []
    above200 = []
    mom60 = []
    for col in stock_prices.columns:
        s = pd.to_numeric(stock_prices[col], errors="coerce").dropna()
        if len(s) >= 50:
            above50.append(float(s.iloc[-1] > s.rolling(50).mean().iloc[-1]))
        if len(s) >= 200:
            above200.append(float(s.iloc[-1] > s.rolling(200).mean().iloc[-1]))
        if len(s) > 60:
            mom60.append(float(s.iloc[-1] / s.iloc[-61] - 1))
    p50 = np.mean(above50) * 100 if above50 else np.nan
    p200 = np.mean(above200) * 100 if above200 else np.nan
    breadth = np.nanmean([p50, p200]) if np.isfinite(p50) or np.isfinite(p200) else 50.0
    return float(breadth), {"% stocks above MA50": p50, "% stocks above MA200": p200, "Stocks analyzed": stock_prices.shape[1]}


def calculate_market_regime(index_prices: pd.Series, stock_prices: pd.DataFrame | None = None) -> RegimeResult:
    index = pd.to_numeric(index_prices, errors="coerce").dropna().sort_index()
    if len(index) < 60:
        raise ValueError("Cần tối thiểu 60 phiên dữ liệu VNINDEX để xác định Market Regime.")

    trend_score, trend = _trend_score(index)
    breadth_score, breadth = _breadth_score(stock_prices)

    ret20 = index.iloc[-1] / index.iloc[-21] - 1 if len(index) > 20 else np.nan
    ret60 = index.iloc[-1] / index.iloc[-61] - 1 if len(index) > 60 else np.nan
    ret120 = index.iloc[-1] / index.iloc[-121] - 1 if len(index) > 120 else np.nan
    momentum_score = float(np.nanmean([
        _score_linear(ret20, -0.10, 0.10),
        _score_linear(ret60, -0.20, 0.20),
        _score_linear(ret120, -0.30, 0.30),
    ]))

    daily = index.pct_change().dropna()
    vol20 = daily.tail(20).std() * np.sqrt(252) if len(daily) >= 20 else np.nan
    vol60 = daily.tail(60).std() * np.sqrt(252) if len(daily) >= 60 else np.nan
    vol_score = _score_linear(vol20, 0.45, 0.10)
    peak = index.cummax()
    drawdown = index.iloc[-1] / peak.iloc[-1] - 1
    drawdown_score = _score_linear(drawdown, -0.30, 0.0)
    risk_score = 0.7 * vol_score + 0.3 * drawdown_score

    liquidity_score = 50.0
    liquidity_ratio = np.nan
    if stock_prices is not None and not stock_prices.empty:
        # Price-only data cannot measure market turnover. Keep this component neutral
        # rather than inventing a liquidity signal.
        liquidity_score = 50.0

    weights = {"Trend": 0.30, "Breadth": 0.25, "Momentum": 0.20, "Volatility & Drawdown": 0.15, "Liquidity": 0.10}
    scores = {"Trend": trend_score, "Breadth": breadth_score, "Momentum": momentum_score, "Volatility & Drawdown": risk_score, "Liquidity": liquidity_score}
    score = sum(scores[k] * weights[k] for k in weights)

    if score >= 80:
        regime, equity = "Tích cực mạnh", (0.90, 1.00)
    elif score >= 65:
        regime, equity = "Tích cực", (0.70, 0.90)
    elif score >= 45:
        regime, equity = "Trung tính", (0.50, 0.70)
    elif score >= 25:
        regime, equity = "Phòng thủ", (0.20, 0.50)
    else:
        regime, equity = "Rủi ro cao", (0.00, 0.20)

    dispersion = np.std(list(scores.values()))
    confidence = "Cao" if dispersion < 10 else "Trung bình" if dispersion < 20 else "Thấp"
    components = pd.DataFrame({
        "Nhóm chỉ báo": list(weights),
        "Điểm": [scores[k] for k in weights],
        "Trọng số": [weights[k] for k in weights],
        "Đóng góp": [scores[k] * weights[k] for k in weights],
    })
    indicators = {**trend, **breadth, "Return 20D": ret20, "Return 60D": ret60, "Return 120D": ret120, "Volatility 20D": vol20, "Volatility 60D": vol60, "Current Drawdown": drawdown, "Liquidity 20D / 60D": liquidity_ratio}
    return RegimeResult(score, regime, confidence, equity[0], equity[1], components, indicators)
