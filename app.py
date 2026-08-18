import pandas as pd
import streamlit as st

from config import APP_NAME, DEFAULT_BENCHMARK, DEFAULT_TICKERS
from data_pipeline import load_market_dataset
from data_provider import configure_vnstock

st.set_page_config(page_title=APP_NAME, page_icon="📊", layout="wide")
st.title(APP_NAME)
st.caption("Nền tảng dữ liệu và quản trị danh mục cổ phiếu Việt Nam")

st.subheader("1. KẾT NỐI DỮ LIỆU")
api_key = st.text_input("API key Vnstock", type="password", placeholder="Nhập API key của bạn")

col1, col2 = st.columns(2)
with col1:
    tickers_text = st.text_input("Danh sách mã cổ phiếu", value=", ".join(DEFAULT_TICKERS))
    start_date = st.date_input("Từ ngày", value=pd.Timestamp("2022-01-01").date())
with col2:
    end_date = st.date_input("Đến ngày", value=pd.Timestamp.today().date())
    benchmark = st.text_input("Benchmark", value=DEFAULT_BENCHMARK)

run = st.button("LẤY DỮ LIỆU", type="primary", use_container_width=True)

if run:
    tickers = list(dict.fromkeys([x.strip().upper() for x in tickers_text.split(",") if x.strip()]))
    if len(tickers) < 2:
        st.error("Cần ít nhất 2 mã cổ phiếu.")
        st.stop()
    if start_date >= end_date:
        st.error("Ngày bắt đầu phải trước ngày kết thúc.")
        st.stop()

    auth = configure_vnstock(api_key)
    st.info(auth["message"])

    try:
        with st.spinner("Đang lấy dữ liệu giá, benchmark và dữ liệu doanh nghiệp..."):
            data = load_market_dataset(
                tickers=tickers,
                start_date=pd.Timestamp(start_date),
                end_date=pd.Timestamp(end_date),
                benchmark=benchmark.strip().upper(),
            )
        st.session_state["market_data"] = data
    except Exception as exc:
        st.error(f"{type(exc).__name__}: {exc}")
        st.stop()

if "market_data" in st.session_state:
    data = st.session_state["market_data"]

    st.subheader("2. TỔNG QUAN DỮ LIỆU")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Số mã", len(data["prices"].columns))
    c2.metric("Số phiên", len(data["prices"]))
    c3.metric("Ngày bắt đầu", pd.Timestamp(data["start_date"]).strftime("%d/%m/%Y"))
    c4.metric("Ngày kết thúc", pd.Timestamp(data["end_date"]).strftime("%d/%m/%Y"))

    st.subheader("3. KIỂM TRA CHẤT LƯỢNG DỮ LIỆU")
    st.dataframe(data["data_quality"], use_container_width=True, hide_index=True)

    st.subheader("4. DỮ LIỆU GIÁ")
    st.dataframe(data["prices"].tail(20), use_container_width=True)

    st.subheader("5. DỮ LIỆU LỢI SUẤT")
    st.dataframe(data["returns"].tail(20), use_container_width=True)

    st.subheader("6. BENCHMARK")
    benchmark_table = pd.DataFrame({
        "Ngày": data["benchmark_prices"].index,
        data["benchmark"]: data["benchmark_prices"].values,
        "Lợi suất": data["benchmark_returns"].reindex(data["benchmark_prices"].index),
    }).dropna(how="all")
    st.dataframe(benchmark_table.tail(20), use_container_width=True, hide_index=True)

    st.subheader("7. THÔNG TIN DOANH NGHIỆP")
    st.dataframe(data["company_table"], use_container_width=True, hide_index=True)

    st.success("Lớp dữ liệu nền đã sẵn sàng. Bước tiếp theo là xây dựng IPS, Risk Engine và Portfolio Construction.")
