import time
from pathlib import Path

import numpy as np
import pandas as pd
from vnstock import Market, Fundamental, Reference, register_user

from config import CACHE_DIR, REQUEST_PAUSE


def configure_vnstock(api_key: str | None = None) -> dict:
    api_key = (api_key or "").strip()
    if not api_key:
        return {"authenticated": False, "message": "Đang dùng chế độ khách của Vnstock."}
    try:
        register_user(api_key=api_key)
        return {"authenticated": True, "message": "Đã xác thực API key Vnstock."}
    except Exception as exc:
        raise ValueError(f"API key Vnstock không hợp lệ hoặc đăng ký thất bại: {exc}") from exc


def pause_api() -> None:
    time.sleep(REQUEST_PAUSE)


def cache_path(kind: str, key: str) -> Path:
    safe = str(key).replace("/", "_").replace("\\", "_").replace(":", "_")
    return CACHE_DIR / f"{kind}_{safe}.csv"


def normalize_columns(df: pd.DataFrame | None) -> pd.DataFrame:
    if df is None:
        return pd.DataFrame()
    out = df.copy()
    out.columns = [
        str(c).strip().lower().replace(" ", "_").replace("-", "_")
        for c in out.columns
    ]
    return out


def safe_float(value):
    try:
        if pd.isna(value):
            return np.nan
        if isinstance(value, str):
            value = value.replace(",", "").replace("%", "").strip()
        return float(value)
    except Exception:
        return np.nan


def find_col(df: pd.DataFrame, candidates: list[str]):
    if df.empty:
        return None
    for candidate in candidates:
        if candidate in df.columns:
            return candidate
    return None


def get_price_data(tickers, start_date, end_date) -> pd.DataFrame:
    market = Market()
    output = {}

    for ticker in tickers:
        path = cache_path("price", f"{ticker}_{start_date}_{end_date}")
        if path.exists():
            try:
                cached = pd.read_csv(path, parse_dates=["Date"], index_col="Date")
                close = pd.to_numeric(cached["close"], errors="coerce").dropna()
                if len(close) > 100:
                    output[ticker] = close
                    continue
            except Exception:
                pass

        try:
            start_ts = pd.Timestamp(start_date)
            end_ts = pd.Timestamp(end_date)
            estimated_sessions = max(int((end_ts - start_ts).days * 0.72) + 50, 300)
            df = market.equity(ticker).ohlcv(end=end_date, interval="1D", count=estimated_sessions)
            df = normalize_columns(df)
            if df.empty or "close" not in df.columns:
                raise ValueError("API không trả về cột close")
            date_col = "time" if "time" in df.columns else "date"
            df[date_col] = pd.to_datetime(df[date_col])
            close = pd.to_numeric(df.set_index(date_col)["close"], errors="coerce").dropna().sort_index()
            close = close[(close.index >= start_ts) & (close.index <= end_ts)]
            if len(close) < 100:
                raise ValueError(f"Chỉ nhận được {len(close)} phiên")
            close.to_frame("close").rename_axis("Date").to_csv(path)
            output[ticker] = close
            pause_api()
        except Exception as exc:
            print(f"Lỗi lấy giá {ticker}: {exc}")

    prices = pd.DataFrame(output).sort_index()
    prices.index = pd.to_datetime(prices.index).normalize()
    prices.index.name = "Date"
    return prices


def get_benchmark_prices(benchmark: str, start_date, end_date) -> pd.Series:
    market = Market()
    start_ts = pd.Timestamp(start_date).normalize()
    end_ts = pd.Timestamp(end_date).normalize()
    pieces = []
    cursor = start_ts

    while cursor <= end_ts:
        chunk_end = min(cursor + pd.Timedelta(days=119), end_ts)
        path = cache_path("benchmark", f"{benchmark}_{cursor:%Y%m%d}_{chunk_end:%Y%m%d}")
        close_chunk = None

        if path.exists():
            try:
                cached = pd.read_csv(path, parse_dates=["Date"], index_col="Date")
                close_chunk = pd.to_numeric(cached["close"], errors="coerce").dropna()
            except Exception:
                close_chunk = None

        if close_chunk is None or close_chunk.empty:
            df = market.index(benchmark).ohlcv(
                start=cursor.strftime("%Y-%m-%d"),
                end=chunk_end.strftime("%Y-%m-%d"),
                interval="1D",
            )
            df = normalize_columns(df)
            if df.empty or "close" not in df.columns:
                raise ValueError(f"Không lấy được benchmark {benchmark}")
            date_col = "time" if "time" in df.columns else "date"
            df[date_col] = pd.to_datetime(df[date_col])
            close_chunk = pd.to_numeric(df.set_index(date_col)["close"], errors="coerce").dropna().sort_index()
            close_chunk.to_frame("close").rename_axis("Date").to_csv(path)
            pause_api()

        pieces.append(close_chunk)
        cursor = chunk_end + pd.Timedelta(days=1)

    close = pd.concat(pieces)
    close = close[~close.index.duplicated(keep="last")].sort_index()
    return close[(close.index >= start_ts) & (close.index <= end_ts)]


def get_company_table(tickers, prices=None) -> pd.DataFrame:
    ref = Reference()
    rows = []
    sectors = normalize_columns(ref.industry.sectors())
    sector_symbol = find_col(sectors, ["symbol", "ticker", "stock_code", "code"])
    sector_name = find_col(sectors, ["icb_name_vi", "icb_name", "industry_name_vi", "industry_name", "industry"])

    for ticker in tickers:
        path = cache_path("company", ticker)
        try:
            if path.exists():
                info = normalize_columns(pd.read_csv(path))
            else:
                info = normalize_columns(ref.company(ticker).info())
                info.to_csv(path, index=False)
                pause_api()

            industry = np.nan
            if sector_symbol and sector_name and not sectors.empty:
                match = sectors[sectors[sector_symbol].astype(str).str.upper() == ticker]
                if not match.empty:
                    industry = match.iloc[0][sector_name]

            shares = np.nan
            shares_col = find_col(info, ["issue_share", "shares_outstanding", "outstanding_shares", "listed_shares"])
            if shares_col:
                shares = safe_float(info.iloc[0][shares_col])

            market_cap = np.nan
            if prices is not None and ticker in prices.columns and pd.notna(shares):
                last_price = prices[ticker].dropna().iloc[-1]
                market_cap = float(last_price) * float(shares) * 1000

            rows.append({"Mã": ticker, "Ngành": industry, "Số CP lưu hành": shares, "Vốn hóa": market_cap})
        except Exception as exc:
            rows.append({"Mã": ticker, "Ngành": np.nan, "Số CP lưu hành": np.nan, "Vốn hóa": np.nan})
            print(f"Không lấy được thông tin {ticker}: {exc}")

    return pd.DataFrame(rows)


def get_income_data(tickers) -> pd.DataFrame:
    fun = Fundamental()
    rows = []

    for ticker in tickers:
        path = cache_path("income", ticker)
        try:
            if path.exists():
                income = normalize_columns(pd.read_csv(path))
            else:
                income = normalize_columns(fun.equity(ticker).income_statement(period="year", orient="report"))
                income.to_csv(path, index=False)
                pause_api()

            item_col = find_col(income, ["item", "item_name", "name", "indicator"])
            year_cols = sorted(
                [c for c in income.columns if str(c).isdigit() and len(str(c)) == 4],
                key=lambda x: int(str(x)), reverse=True
            )

            revenue = np.nan
            profit = np.nan
            revenue_year = None
            profit_year = None

            if item_col and year_cols:
                items = income[item_col].astype(str).str.lower()
                revenue_keywords = ["doanh thu thuan", "net revenue", "revenue", "tong thu nhap hoat dong"]
                profit_keywords = ["loi nhuan sau thue cua co dong cong ty me", "loi nhuan sau thue", "profit after tax", "net profit"]

                for key in revenue_keywords:
                    mask = items.str.contains(key, regex=False, na=False)
                    if mask.any():
                        row = income.loc[mask].iloc[0]
                        for year in year_cols:
                            value = safe_float(row[year])
                            if pd.notna(value):
                                revenue, revenue_year = value, str(year)
                                break
                    if pd.notna(revenue):
                        break

                for key in profit_keywords:
                    mask = items.str.contains(key, regex=False, na=False)
                    if mask.any():
                        row = income.loc[mask].iloc[0]
                        for year in year_cols:
                            value = safe_float(row[year])
                            if pd.notna(value):
                                profit, profit_year = value, str(year)
                                break
                    if pd.notna(profit):
                        break

            rows.append({"Mã": ticker, "Doanh thu gần nhất": revenue, "Năm doanh thu": revenue_year, "LNST gần nhất": profit, "Năm LNST": profit_year})
        except Exception as exc:
            rows.append({"Mã": ticker, "Doanh thu gần nhất": np.nan, "Năm doanh thu": None, "LNST gần nhất": np.nan, "Năm LNST": None})
            print(f"Không lấy được BCTC {ticker}: {exc}")

    return pd.DataFrame(rows)
