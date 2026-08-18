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


def basic_data_quality_report(prices: pd.DataFrame, returns: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for ticker in prices.columns:
        price = pd.to_numeric(prices[ticker], errors="coerce")
        ret = pd.to_numeric(returns[ticker], errors="coerce") if ticker in returns.columns else pd.Series(dtype=float)
        rows.append({
            "Mã": ticker,
            "Số phiên giá": int(price.notna().sum()),
            "Thiếu giá": int(price.isna().sum()),
            "Số lợi suất": int(ret.notna().sum()),
            "Lợi suất âm": int((ret < 0).sum()),
            "Lợi suất dương": int((ret > 0).sum()),
        })
    return pd.DataFrame(rows)
