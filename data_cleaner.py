import numpy as np
import pandas as pd


def clean_price_data(prices: pd.DataFrame) -> pd.DataFrame:
    if prices is None or prices.empty:
        return pd.DataFrame()
    out = prices.copy()
    out.index = pd.to_datetime(out.index).normalize()
    out = out.sort_index()
    out = out.apply(pd.to_numeric, errors="coerce")
    out = out.replace([np.inf, -np.inf], np.nan)
    return out


def align_price_and_benchmark(prices: pd.DataFrame, benchmark: pd.Series):
    prices = clean_price_data(prices)
    benchmark = pd.to_numeric(benchmark, errors="coerce").dropna().copy()
    benchmark.index = pd.to_datetime(benchmark.index).normalize()
    benchmark = benchmark.sort_index()
    common = prices.index.intersection(benchmark.index).sort_values()
    if len(common) < 100:
        raise ValueError(f"Chỉ có {len(common)} phiên giao dịch chung, không đủ dữ liệu.")
    return prices.loc[common].dropna(how="any"), benchmark.loc[common]


def calculate_returns(prices: pd.DataFrame) -> pd.DataFrame:
    return prices.pct_change().replace([np.inf, -np.inf], np.nan).dropna(how="all")


def _period_return(series: pd.Series, sessions: int):
    s = pd.to_numeric(series, errors="coerce").dropna()
    if len(s) <= sessions:
        return np.nan
    return s.iloc[-1] / s.iloc[-sessions - 1] - 1


def statistical_data_report(prices: pd.DataFrame, returns: pd.DataFrame, volumes: pd.DataFrame | None = None) -> pd.DataFrame:
    rows = []
    total_sessions = len(prices.index)
    for ticker in prices.columns:
        price = pd.to_numeric(prices[ticker], errors="coerce")
        ret = pd.to_numeric(returns[ticker], errors="coerce") if ticker in returns.columns else pd.Series(dtype=float)
        vol = pd.to_numeric(volumes[ticker], errors="coerce") if volumes is not None and ticker in volumes.columns else pd.Series(dtype=float)
        valid_price = price.dropna()
        valid_ret = ret.dropna()
        annualized_volatility = valid_ret.std(ddof=1) * np.sqrt(252) if len(valid_ret) > 1 else np.nan
        avg_volume = vol.dropna().mean() if not vol.dropna().empty else np.nan
        rows.append({
            "Mã": ticker,
            "Giá hiện tại": valid_price.iloc[-1] if not valid_price.empty else np.nan,
            "Tăng/Giảm 1M": _period_return(price, 21),
            "Tăng/Giảm 6M": _period_return(price, 126),
            "Tăng/Giảm 12M": _period_return(price, 252),
            "Biến động Annualized": annualized_volatility,
            "Khối lượng TB": avg_volume,
            "Số phiên có dữ liệu": int(price.notna().sum()),
            "Số phiên thiếu": int(price.isna().sum()),
            "Độ phủ dữ liệu": price.notna().sum() / total_sessions if total_sessions else np.nan,
        })
    return pd.DataFrame(rows)


def basic_data_quality_report(prices: pd.DataFrame, returns: pd.DataFrame, volumes: pd.DataFrame | None = None) -> pd.DataFrame:
    return statistical_data_report(prices, returns, volumes)
