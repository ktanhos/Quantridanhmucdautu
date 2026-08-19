import pandas as pd

from data_cleaner import align_price_and_benchmark, basic_data_quality_report, calculate_returns
from data_provider import get_benchmark_prices, get_company_table, get_income_data, get_price_data, get_volume_data


def load_market_dataset(tickers, start_date, end_date, benchmark="VNINDEX"):
    prices = get_price_data(tickers, start_date, end_date)
    if prices.empty:
        raise ValueError("Không lấy được dữ liệu giá cổ phiếu.")

    volumes = get_volume_data(tickers, start_date, end_date)
    benchmark_prices = get_benchmark_prices(benchmark, start_date, end_date)
    prices, benchmark_prices = align_price_and_benchmark(prices, benchmark_prices)
    volumes = volumes.reindex(prices.index)

    returns = calculate_returns(prices)
    benchmark_returns = benchmark_prices.pct_change().replace([pd.NA], pd.NA).dropna()
    quality = basic_data_quality_report(prices, returns)
    company = get_company_table(tickers, prices=prices)
    income = get_income_data(tickers)
    company_table = company.merge(income, on="Mã", how="left")

    return {
        "prices": prices,
        "volumes": volumes,
        "returns": returns,
        "benchmark_prices": benchmark_prices,
        "benchmark_returns": benchmark_returns,
        "data_quality": quality,
        "company_table": company_table,
        "start_date": prices.index[0],
        "end_date": prices.index[-1],
        "benchmark": benchmark,
    }
