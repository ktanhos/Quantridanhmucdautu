import pandas as pd
from data_cleaner import align_price_and_benchmark, basic_data_quality_report, calculate_returns
from data_provider import get_benchmark_ohlcv, get_company_table, get_income_data, get_market_universe_ohlcv, get_market_universe_volume, get_price_data, get_volume_data

def load_market_dataset(tickers,start_date,end_date,benchmark='VNINDEX'):
    prices=get_price_data(tickers,start_date,end_date)
    if prices.empty: raise ValueError('Không lấy được dữ liệu giá cổ phiếu.')
    volumes=get_volume_data(tickers,start_date,end_date)
    benchmark_ohlcv=get_benchmark_ohlcv(benchmark,start_date,end_date)
    benchmark_prices=benchmark_ohlcv['close'].dropna()
    prices,benchmark_prices=align_price_and_benchmark(prices,benchmark_prices)
    volumes=volumes.reindex(prices.index)
    returns=calculate_returns(prices)
    benchmark_returns=benchmark_prices.pct_change().dropna()
    quality=basic_data_quality_report(prices,returns)
    company=get_company_table(tickers,prices=prices); income=get_income_data(tickers); company_table=company.merge(income,on='Mã',how='left')
    # Market Regime dùng dữ liệu thị trường độc lập với danh mục người dùng.
    market_universe_prices=get_market_universe_ohlcv(start_date,end_date)
    market_universe_volumes=get_market_universe_volume(start_date,end_date)
    return {'prices':prices,'volumes':volumes,'returns':returns,'benchmark_prices':benchmark_prices,'benchmark_ohlcv':benchmark_ohlcv,'benchmark_returns':benchmark_returns,'data_quality':quality,'company_table':company_table,'market_universe_prices':market_universe_prices,'market_universe_volumes':market_universe_volumes,'start_date':prices.index[0],'end_date':prices.index[-1],'benchmark':benchmark}
