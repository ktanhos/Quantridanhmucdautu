import pandas as pd
import streamlit as st
from config import APP_NAME, DEFAULT_BENCHMARK, DEFAULT_TICKERS
from data_pipeline import load_market_dataset
from data_provider import configure_vnstock
from market_regime_ui import render_market_regime
from portfolio_risk_ui import render_portfolio_risk
from portfolio_optimization_ui import render_portfolio_optimization
from portfolio_recommendation_ui import render_recommendation
from portfolio_performance_ui import render_portfolio_performance
from portfolio_summary_ui import render_portfolio_summary
from policy import InvestmentPolicy, risk_label, risk_profile_description, validate_policy

st.set_page_config(page_title=APP_NAME, page_icon="📊", layout="wide", initial_sidebar_state="expanded")

if "policy" not in st.session_state:
    st.session_state["policy"] = None

st.markdown(
    """
    <style>
    .block-container{max-width:1480px;padding-top:2rem;padding-bottom:4rem}
    [data-testid="stHeader"]{background:transparent}
    h1{font-size:2.35rem!important;font-weight:750!important;letter-spacing:-.03em}
    h2{font-size:1.55rem!important;font-weight:720!important;margin-top:2.2rem!important;padding-left:.75rem;border-left:4px solid #4f8cff}
    h3{font-size:1.12rem!important;font-weight:680!important;margin-top:1.4rem!important}
    .hero{border:1px solid rgba(128,128,128,.24);border-radius:18px;padding:1.5rem 1.7rem;margin-bottom:1.2rem;background:linear-gradient(135deg,rgba(79,140,255,.10),rgba(128,128,128,.035))}
    .hero-title{font-size:1.9rem;font-weight:760;line-height:1.15;margin-bottom:.45rem}
    .hero-subtitle{color:#8f96a3;font-size:.94rem;line-height:1.55;max-width:900px}
    .hero-chip{display:inline-block;margin-top:.8rem;margin-right:.45rem;padding:.3rem .65rem;border-radius:999px;border:1px solid rgba(128,128,128,.25);font-size:.75rem;color:#aeb5c1;background:rgba(128,128,128,.06)}
    .section-note{color:#8f96a3;font-size:.88rem;line-height:1.55;margin-top:-.35rem;margin-bottom:1rem}
    .workflow-card{border:1px solid rgba(128,128,128,.22);border-radius:14px;padding:1rem;background:rgba(128,128,128,.035);margin-bottom:.8rem}
    .workflow-title{font-weight:700;margin-bottom:.35rem}
    .workflow-muted{color:#8f96a3;font-size:.78rem;line-height:1.45}
    [data-testid="stMetric"]{border:1px solid rgba(128,128,128,.20);border-radius:12px;padding:.8rem .9rem;background:rgba(128,128,128,.025);min-height:100px}
    [data-testid="stMetricLabel"]{font-size:.78rem}
    [data-testid="stMetricValue"]{font-size:1.55rem}
    [data-testid="stExpander"]{border:1px solid rgba(128,128,128,.20);border-radius:12px;overflow:hidden}
    [data-testid="stDataFrame"]{border:1px solid rgba(128,128,128,.16);border-radius:10px;overflow:hidden}
    div.stButton>button{border-radius:10px;font-weight:650;min-height:2.7rem}
    div[data-testid="stFormSubmitButton"]>button{border-radius:10px;font-weight:650}
    .small-note{color:#8f96a3;font-size:.76rem;line-height:1.5}
    .cost-card{border:1px solid rgba(128,128,128,.18);border-radius:12px;padding:.75rem;background:rgba(128,128,128,.025)}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
        <div class="hero-title">Quản trị danh mục đầu tư</div>
        <div class="hero-subtitle">Công cụ định hướng xây dựng danh mục cổ phiếu Việt Nam theo dữ liệu thị trường, trạng thái thị trường và hồ sơ nhà đầu tư. Người dùng đi từ mục tiêu đến phương án phân bổ thay vì phải tự nhập một danh mục có sẵn.</div>
        <span class="hero-chip">Dữ liệu thị trường Việt Nam</span>
        <span class="hero-chip">Phân tích rủi ro</span>
        <span class="hero-chip">Tối ưu hóa danh mục</span>
        <span class="hero-chip">So sánh với VNINDEX</span>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### Quy trình")
    steps = [
        ("1", "Kết nối dữ liệu", True),
        ("2", "Hồ sơ đầu tư", st.session_state.get("policy") is not None),
        ("3", "Lấy dữ liệu", "market_data" in st.session_state),
        ("4", "Kiểm tra dữ liệu", "market_data" in st.session_state),
        ("5", "Market Regime", "regime_result" in st.session_state),
        ("6", "Phân tích rủi ro", "market_data" in st.session_state),
        ("7", "Tối ưu hóa", "optimization_result" in st.session_state),
        ("8", "Đề xuất phân bổ", "recommendation_result" in st.session_state),
        ("9", "Hiệu quả lịch sử", "portfolio_performance" in st.session_state),
        ("11", "Tổng kết", "portfolio_performance" in st.session_state),
    ]
    for number, label, done in steps:
        mark = "Đã sẵn sàng" if done else "Chưa thực hiện"
        color = "#62d39b" if done else "#8f96a3"
        st.markdown(f'<div style="display:flex;gap:.6rem;align-items:center;margin:.38rem 0"><span style="width:25px;height:25px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;border:1px solid rgba(128,128,128,.25);font-size:.72rem">{number}</span><div><div style="font-size:.82rem;font-weight:600">{label}</div><div style="font-size:.68rem;color:{color}">{mark}</div></div></div>', unsafe_allow_html=True)
    st.divider()
    st.caption("Phiên bản hiện tại tập trung vào guiding xây dựng danh mục. Không đặt lệnh, không quản lý sổ lệnh và không yêu cầu nhập lịch sử giao dịch.")

with st.expander("Chi phí và giả định tham khảo", expanded=False):
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Phí giao dịch mua/bán", "0,10%")
    c2.metric("Thuế khi bán", "0,10%")
    c3.metric("Phí lưu ký", "0,27 đồng/cổ phiếu/tháng")
    c4.metric("Lãi suất Margin", "12%/năm")
    st.caption("Các thông số chỉ mang tính tham khảo. Ứng dụng không mô phỏng lịch sử giao dịch hoặc tính chi phí theo từng lệnh.")

st.header("Bước 1. Kết nối dữ liệu")
st.markdown('<div class="section-note">Nhập mã truy cập để ứng dụng lấy dữ liệu giá, khối lượng và VNINDEX phục vụ các bước phân tích phía sau.</div>', unsafe_allow_html=True)
api_key = st.text_input("Mã truy cập Vnstock", type="password", key="api_key")

st.header("Bước 2. Hồ sơ và nguồn vốn đầu tư")
st.markdown('<div class="section-note">Chỉ cần trả lời các câu hỏi cơ bản. Hệ thống tự chuyển câu trả lời thành các ràng buộc định lượng; người dùng không cần biết cách tính phương sai hay Sharpe Ratio.</div>', unsafe_allow_html=True)
goals = {
    "Bảo toàn vốn": "Ưu tiên hạn chế thua lỗ và biến động.",
    "Tăng trưởng ổn định": "Chấp nhận biến động vừa phải để tăng trưởng vốn.",
    "Tăng trưởng cao": "Chấp nhận biến động lớn hơn để tìm kiếm mức tăng trưởng cao hơn.",
}
investor_goal = st.radio("Mục tiêu chính", list(goals), horizontal=True, key="investor_goal")
st.caption(goals[investor_goal])

c1, c2 = st.columns(2)
with c1:
    investment_capital = st.number_input("Vốn đầu tư dự kiến (VNĐ)", min_value=0., value=100000000., step=10000000., format="%.0f", key="investment_capital_input")
with c2:
    target_return = st.number_input("Mục tiêu lợi nhuận mỗi năm (%)", 0., 100., 12., .5, format="%.1f", key="target_return", help="Đây là mức lợi nhuận bạn mong muốn đạt được, không phải dự báo chắc chắn. Mục tiêu càng cao có thể càng cần chấp nhận rủi ro hoặc mở rộng tập cổ phiếu.")
st.caption("Mục tiêu lợi nhuận là yêu cầu đầu vào để so sánh các phương án, không phải cam kết lợi nhuận.")

risk_options = {"Thận trọng": 25, "Cân bằng": 50, "Tăng trưởng": 75}
risk_profile = st.radio("Bạn chấp nhận mức biến động nào?", list(risk_options), horizontal=True, key="risk_profile", help="Hãy chọn mức gần với phản ứng thực tế của bạn khi danh mục giảm mạnh, không phải mức lợi nhuận bạn mong muốn.")
risk_score = risk_options[risk_profile]
st.info(risk_profile_description(risk_score))
st.caption("Bạn không cần tự chấm điểm rủi ro. Hệ thống dùng lựa chọn này để so sánh mức biến động của các phương án.")

with st.expander("Ràng buộc phân bổ", expanded=True):
    c1, c2 = st.columns(2)
    with c1:
        max_single_stock_weight = st.number_input("Giới hạn một cổ phiếu (%)", 1., 100., 20., 1., format="%.1f", key="max_stock", help="Tỷ trọng tối đa dành cho một mã. Ví dụ 20% nghĩa là không quá 20% vốn cổ phiếu được dành cho một mã.")
    with c2:
        max_sector_weight = st.number_input("Giới hạn một ngành (%)", 1., 100., 35., 1., format="%.1f", key="max_sector", help="Giới hạn tổng tỷ trọng các cổ phiếu cùng ngành. Phiên bản hiện tại chủ yếu lưu đây như một ràng buộc hồ sơ.")
    st.caption("Nếu chưa biết nên chọn gì, giữ mặc định 20% cho một cổ phiếu. Hệ thống sẽ tự kiểm tra tập cổ phiếu có đủ rộng để áp dụng giới hạn này hay không.")

with st.expander("Tùy chọn nâng cao", expanded=False):
    allow_short = False
    st.checkbox("Cho phép bán khống", value=False, disabled=True, help="Phiên bản hiện tại không hỗ trợ bán khống.", key="short_disabled")
    allow_leverage = st.checkbox("Cho phép vay Margin", value=False, help="Chỉ dùng để định hướng mức độ chấp nhận vốn vay.", key="allow_leverage")
    margin_rate = st.number_input("Lãi suất vay Margin (%/năm)", 9., 15., 12., .25, format="%.2f", disabled=not allow_leverage, key="margin_rate")
    defensive_asset = st.radio("Tài sản phòng thủ", ["Tiền mặt", "Tiền gửi ngắn hạn"], horizontal=True, key="defensive_asset")

benchmark = st.text_input("Benchmark", value=DEFAULT_BENCHMARK, key="benchmark_profile").strip().upper()

policy = InvestmentPolicy(
    investor_goal=investor_goal,
    target_return=target_return / 100,
    risk_tolerance=risk_score,
    risk_capacity=risk_score,
    investment_horizon_years=5,
    liquidity_need="Không đặt trong phiên bản hiện tại",
    benchmark=benchmark or DEFAULT_BENCHMARK,
    max_single_stock_weight=max_single_stock_weight / 100,
    max_sector_weight=max_sector_weight / 100,
    allow_short=allow_short,
    allow_leverage=allow_leverage,
    defensive_asset=defensive_asset,
    emergency_cash_percent=0.0,
)
errors = validate_policy(policy)
if errors:
    for e in errors:
        st.warning(e)
else:
    st.success(f"Hồ sơ hợp lệ. Mục tiêu {target_return:.1f}% mỗi năm. Mức chấp nhận biến động: {risk_label(risk_score)}.")

if st.button("LƯU HỒ SƠ ĐẦU TƯ", type="primary", use_container_width=True, disabled=bool(errors), key="save_policy"):
    st.session_state["policy"] = policy.to_dict()
    st.session_state["investment_capital"] = investment_capital
    st.session_state["saved_margin_rate"] = margin_rate / 100
    for key in ["optimization_result", "recommended_portfolio", "recommendation_result", "target_equity", "portfolio_performance"]:
        st.session_state.pop(key, None)
    if "market_data" in st.session_state:
        st.info("Đã giữ nguyên dữ liệu thị trường đã tải. Thay đổi hồ sơ chỉ làm tính lại các bước phía sau, không cần gọi lại dữ liệu.")
    st.success("Đã lưu hồ sơ và nguồn vốn. Các bước phía sau sẽ tính lại theo hồ sơ mới.")

st.divider()
st.header("Bước 3. Lấy dữ liệu")
st.markdown('<div class="section-note">Chọn tập cổ phiếu để hệ thống nghiên cứu. Đây là tập đầu vào để tìm phương án phân bổ, không phải danh mục bạn đang nắm giữ.</div>', unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    tickers_text = st.text_input("Tập cổ phiếu để hệ thống xem xét", value=", ".join(DEFAULT_TICKERS), key="tickers_input")
    start_date = st.date_input("Ngày bắt đầu", value=pd.Timestamp("2022-01-01").date(), key="start_date")
with col2:
    end_date = st.date_input("Ngày kết thúc", value=pd.Timestamp.today().date(), key="end_date")
    benchmark_data = st.text_input("Benchmark", value=benchmark or DEFAULT_BENCHMARK, key="benchmark_data").strip().upper()

if st.button("LẤY DỮ LIỆU", type="secondary", use_container_width=True, key="load_data"):
    if st.session_state.get("policy") is None:
        st.warning("Hãy lưu Hồ sơ đầu tư trước.")
        st.stop()
    tickers = list(dict.fromkeys([x.strip().upper() for x in tickers_text.split(",") if x.strip()]))
    if len(tickers) < 2:
        st.error("Cần ít nhất 2 mã cổ phiếu để so sánh và đa dạng hóa.")
        st.stop()
    if start_date >= end_date:
        st.error("Ngày bắt đầu phải trước ngày kết thúc.")
        st.stop()
    configure_vnstock(api_key)
    try:
        with st.spinner("Đang lấy dữ liệu danh mục và VNINDEX OHLCV..."):
            st.session_state["market_data"] = load_market_dataset(tickers, pd.Timestamp(start_date), pd.Timestamp(end_date), benchmark_data or DEFAULT_BENCHMARK)
        for key in ["optimization_result", "recommended_portfolio", "recommendation_result", "target_equity", "portfolio_performance"]:
            st.session_state.pop(key, None)
    except Exception as exc:
        st.error(f"{type(exc).__name__}: {exc}")
        st.stop()

if "market_data" in st.session_state:
    data = st.session_state["market_data"]
    st.header("Bước 4. Kiểm tra dữ liệu")
    st.markdown('<div class="section-note">Kiểm tra nhanh phạm vi dữ liệu, mức tăng giảm và độ phủ trước khi bước vào phân tích. Các thống kê này mô tả dữ liệu, không phải tín hiệu mua bán.</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Số mã xem xét", len(data["prices"].columns))
    c2.metric("Số phiên", len(data["prices"]))
    c3.metric("Ngày bắt đầu", pd.Timestamp(data["start_date"]).strftime("%d/%m/%Y"))
    c4.metric("Ngày kết thúc", pd.Timestamp(data["end_date"]).strftime("%d/%m/%Y"))
    quality = data["data_quality"].copy()
    pct_cols = ["Tăng/Giảm 1M", "Tăng/Giảm 6M", "Tăng/Giảm 12M", "Biến động Annualized", "Độ phủ dữ liệu"]
    for col in pct_cols:
        quality[col] = quality[col].map(lambda x: "N/A" if pd.isna(x) else f"{x:.2%}")
    quality["Giá hiện tại"] = quality["Giá hiện tại"].map(lambda x: "N/A" if pd.isna(x) else f"{x:,.0f}")
    quality["Khối lượng TB"] = quality["Khối lượng TB"].map(lambda x: "N/A" if pd.isna(x) else f"{x:,.0f}")
    quality["Số phiên có dữ liệu"] = quality["Số phiên có dữ liệu"].map(lambda x: f"{int(x):,}")
    quality["Số phiên thiếu"] = quality["Số phiên thiếu"].map(lambda x: f"{int(x):,}")
    quality = quality.rename(columns={"Giá hiện tại": "Giá hiện tại (VNĐ)", "Biến động Annualized": "Volatility Annualized", "Khối lượng TB": "Average Volume", "Số phiên có dữ liệu": "Số phiên dữ liệu", "Độ phủ dữ liệu": "Data Coverage"})
    st.subheader("Thống kê thị trường và chất lượng dữ liệu")
    st.dataframe(quality, use_container_width=True, hide_index=True)
    st.caption("1M khoảng 21 phiên, 6M khoảng 126 phiên và 12M khoảng 252 phiên. Volatility Annualized là độ biến động quy đổi về cơ sở một năm từ lợi suất ngày. Average Volume là khối lượng giao dịch bình quân mỗi phiên. Data Coverage là tỷ lệ phiên có dữ liệu hợp lệ.")

    st.divider()
    render_market_regime(data["benchmark_prices"], None, data["benchmark_ohlcv"]["volume"])
    st.caption("Market Regime được xác định từ VNINDEX OHLCV, độc lập với danh mục mục tiêu.")
    st.divider()
    render_portfolio_risk(data["returns"], data["benchmark_returns"])
    st.divider()
    render_portfolio_optimization(data["returns"], st.session_state.get("policy") or {}, data["benchmark_returns"])
    if "optimization_result" in st.session_state:
        render_recommendation(data["returns"], st.session_state["optimization_result"], st.session_state.get("regime_result"), st.session_state.get("policy") or {})
    if "target_equity" in st.session_state:
        render_portfolio_performance(data["returns"], data["benchmark_returns"], st.session_state["target_equity"])
    if "portfolio_performance" in st.session_state:
        target_equity_total = float(pd.Series(st.session_state.get("target_equity"), dtype=float).sum())
        st.divider()
        render_portfolio_summary(st.session_state.get("portfolio_performance"), st.session_state.get("regime_result"), None, target_equity_total)
