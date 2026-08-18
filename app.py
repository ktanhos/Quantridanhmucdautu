import pandas as pd
import streamlit as st

from config import APP_NAME, DEFAULT_BENCHMARK, DEFAULT_TICKERS
from data_pipeline import load_market_dataset
from data_provider import configure_vnstock
from policy import InvestmentPolicy, risk_label, validate_policy

st.set_page_config(page_title=APP_NAME, page_icon="📊", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
.block-container {max-width: 1250px; padding-top: 2rem;}
.help-text {color:#6b7280; font-size:0.92rem;}
</style>
""", unsafe_allow_html=True)

st.title("Quản trị danh mục đầu tư")
st.caption("Danh mục cổ phiếu Việt Nam và tài sản phòng thủ. Hệ thống hướng dẫn từng bước, không yêu cầu người dùng phải biết thuật ngữ tài chính.")

if "policy" not in st.session_state:
    st.session_state["policy"] = None

st.header("Bước 1. Kết nối dữ liệu")
st.caption("Trước tiên, hệ thống cần dữ liệu thị trường. Bạn chỉ cần cung cấp mã truy cập Vnstock nếu nguồn dữ liệu yêu cầu.")
with st.expander("Mã truy cập Vnstock là gì?", expanded=False):
    st.write("Đây là mã truy cập dữ liệu của Vnstock. Mã được nhập dưới dạng mật khẩu và chỉ được dùng trong phiên chạy hiện tại.")
api_key = st.text_input("Mã truy cập Vnstock", type="password", placeholder="Dán mã truy cập tại đây nếu bạn có")

st.header("Bước 2. Hồ sơ đầu tư")
st.caption("Bạn không cần biết thuật ngữ tài chính. Hãy trả lời các câu hỏi bên dưới theo tình hình thực tế. Hệ thống sẽ chuyển câu trả lời thành các quy tắc quản lý danh mục.")

with st.container(border=True):
    st.subheader("2.1. Bạn muốn khoản đầu tư này đạt điều gì?")
    goal_options = {
        "Bảo toàn vốn": "Ưu tiên hạn chế thua lỗ hơn là tìm kiếm lợi nhuận cao.",
        "Tăng trưởng ổn định": "Chấp nhận biến động vừa phải để tìm kiếm tăng trưởng dài hạn.",
        "Tăng trưởng cao": "Chấp nhận biến động lớn hơn để tìm kiếm lợi nhuận cao hơn.",
    }
    investor_goal = st.radio("Mục tiêu chính", list(goal_options), horizontal=True, help="Chọn mục tiêu gần nhất với mong muốn thực tế của bạn.")
    st.caption(goal_options[investor_goal])
    target_return = st.number_input("Lợi nhuận mục tiêu mỗi năm (%)", min_value=0.0, max_value=100.0, value=12.0, step=0.5, format="%.1f", help="Mức lợi nhuận bạn mong muốn đạt được bình quân mỗi năm. Đây là mục tiêu, không phải cam kết lợi nhuận.")

with st.container(border=True):
    st.subheader("2.2. Bạn chấp nhận biến động đến mức nào?")
    risk_tolerance = st.slider("Khẩu vị rủi ro", 0, 100, 50, 5, help="Mức độ bạn cảm thấy thoải mái khi danh mục biến động hoặc tạm thời thua lỗ.")
    st.caption(f"Khẩu vị hiện tại: **{risk_label(risk_tolerance)}**. Đây là mức bạn cảm thấy chấp nhận được về mặt tâm lý.")
    risk_capacity = st.slider("Khả năng chịu rủi ro", 0, 100, 50, 5, help="Khả năng tài chính thực tế để chịu thua lỗ mà không ảnh hưởng nghiêm trọng đến kế hoạch tài chính.")
    st.caption(f"Khả năng hiện tại: **{risk_label(risk_capacity)}**. Hai khái niệm này có thể khác nhau và hệ thống sẽ kiểm tra sự phù hợp.")

with st.container(border=True):
    st.subheader("2.3. Khi nào bạn cần sử dụng số tiền này?")
    horizon_labels = {1: "Dưới 2 năm", 3: "2 đến 5 năm", 7: "5 đến 10 năm", 15: "Trên 10 năm"}
    investment_horizon_years = st.select_slider("Thời hạn đầu tư", options=list(horizon_labels), value=7, format_func=lambda x: horizon_labels[x], help="Khoảng thời gian bạn dự kiến duy trì khoản đầu tư trước khi cần sử dụng phần lớn số tiền.")
    liquidity_options = {
        "Cao": "Có thể cần tiền trong ngắn hạn. Nên ưu tiên tài sản có tính thanh khoản cao.",
        "Trung bình": "Có thể chấp nhận một phần vốn biến động trong thời gian dài hơn.",
        "Thấp": "Ít nhu cầu sử dụng vốn trong ngắn hạn.",
    }
    liquidity_need = st.selectbox("Nhu cầu sử dụng tiền", list(liquidity_options), index=1, help="Khả năng bạn cần rút tiền trong thời gian ngắn.")
    st.caption(liquidity_options[liquidity_need])

with st.container(border=True):
    st.subheader("2.4. Các giới hạn bạn muốn đặt cho danh mục")
    c1, c2, c3 = st.columns(3)
    with c1:
        max_single_stock_weight = st.number_input("Tối đa một cổ phiếu (%)", 1.0, 100.0, 10.0, 1.0, format="%.1f", help="Không để một cổ phiếu chiếm quá tỷ lệ này trong danh mục.")
    with c2:
        max_sector_weight = st.number_input("Tối đa một ngành (%)", 1.0, 100.0, 25.0, 1.0, format="%.1f", help="Không để một ngành chiếm quá tỷ lệ này trong danh mục.")
    with c3:
        emergency_cash_percent = st.number_input("Tiền dự phòng tối thiểu (%)", 0.0, 100.0, 10.0, 1.0, format="%.1f", help="Phần vốn tối thiểu không đưa vào cổ phiếu, dành cho thanh khoản hoặc phòng thủ.")
    c4, c5 = st.columns(2)
    with c4:
        allow_short = st.checkbox("Cho phép bán khống", value=False, help="Bán khống làm tăng độ phức tạp và rủi ro. Mặc định hệ thống không cho phép.")
    with c5:
        allow_leverage = st.checkbox("Cho phép sử dụng đòn bẩy", value=False, help="Cho phép tổng mức đầu tư vượt vốn thực có. Mặc định hệ thống không cho phép.")

with st.container(border=True):
    st.subheader("2.5. Nếu thị trường trở nên rủi ro, bạn muốn hệ thống chuyển tiền sang đâu?")
    defensive_asset = st.radio("Tài sản phòng thủ", ["Tiền mặt", "Tiền gửi ngắn hạn"], horizontal=True, help="Khi tín hiệu rủi ro tăng cao, hệ thống có thể giảm tỷ trọng cổ phiếu và chuyển phần vốn phòng thủ sang lựa chọn này.")

with st.container(border=True):
    st.subheader("2.6. Thị trường dùng để so sánh")
    benchmark = st.text_input("Chỉ số tham chiếu", value=DEFAULT_BENCHMARK, help="Ví dụ VNINDEX. Hệ thống dùng chỉ số này để đánh giá danh mục có tốt hơn thị trường hay không.").strip().upper()

policy = InvestmentPolicy(
    investor_goal=investor_goal,
    target_return=target_return / 100,
    risk_tolerance=risk_tolerance,
    risk_capacity=risk_capacity,
    investment_horizon_years=investment_horizon_years,
    liquidity_need=liquidity_need,
    benchmark=benchmark or DEFAULT_BENCHMARK,
    max_single_stock_weight=max_single_stock_weight / 100,
    max_sector_weight=max_sector_weight / 100,
    allow_short=allow_short,
    allow_leverage=allow_leverage,
    defensive_asset=defensive_asset,
    emergency_cash_percent=emergency_cash_percent / 100,
)

policy_errors = validate_policy(policy)
if policy_errors:
    for error in policy_errors:
        st.warning(error)
else:
    st.success(f"Hồ sơ hợp lệ. Mục tiêu: **{target_return:.1f}% mỗi năm**. Khẩu vị rủi ro: **{risk_label(risk_tolerance)}**.")

if st.button("LƯU HỒ SƠ ĐẦU TƯ", type="primary", use_container_width=True, disabled=bool(policy_errors)):
    st.session_state["policy"] = policy.to_dict()
    st.success("Đã lưu hồ sơ. Các bước phân bổ và kiểm soát rủi ro sau này sẽ sử dụng các giới hạn này.")

st.divider()
st.header("Bước 3. Lấy dữ liệu thị trường")
st.caption("Sau khi lưu hồ sơ, chọn các cổ phiếu và khoảng thời gian cần theo dõi.")
col1, col2 = st.columns(2)
with col1:
    tickers_text = st.text_input("Các mã cổ phiếu muốn theo dõi", value=", ".join(DEFAULT_TICKERS), help="Nhập mã cách nhau bằng dấu phẩy, ví dụ FPT, MBB, VCB, HPG.")
    start_date = st.date_input("Ngày bắt đầu dữ liệu", value=pd.Timestamp("2022-01-01").date())
with col2:
    end_date = st.date_input("Ngày kết thúc dữ liệu", value=pd.Timestamp.today().date())
    benchmark_data = st.text_input("Benchmark dữ liệu", value=benchmark or DEFAULT_BENCHMARK).strip().upper()

run = st.button("LẤY DỮ LIỆU", type="secondary", use_container_width=True)
if run:
    if st.session_state.get("policy") is None:
        st.warning("Hãy lưu Hồ sơ đầu tư trước khi lấy dữ liệu.")
        st.stop()
    tickers = list(dict.fromkeys([x.strip().upper() for x in tickers_text.split(",") if x.strip()]))
    if len(tickers) < 2:
        st.error("Cần ít nhất 2 mã cổ phiếu để bắt đầu phân tích danh mục.")
        st.stop()
    if start_date >= end_date:
        st.error("Ngày bắt đầu phải trước ngày kết thúc.")
        st.stop()
    auth = configure_vnstock(api_key)
    st.info(auth["message"])
    try:
        with st.spinner("Đang lấy dữ liệu giá, benchmark và dữ liệu doanh nghiệp..."):
            data = load_market_dataset(tickers=tickers, start_date=pd.Timestamp(start_date), end_date=pd.Timestamp(end_date), benchmark=benchmark_data or DEFAULT_BENCHMARK)
        st.session_state["market_data"] = data
    except Exception as exc:
        st.error(f"{type(exc).__name__}: {exc}")
        st.stop()

if "market_data" in st.session_state:
    data = st.session_state["market_data"]
    st.header("Bước 4. Kiểm tra dữ liệu")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Số mã", len(data["prices"].columns))
    c2.metric("Số phiên", len(data["prices"]))
    c3.metric("Ngày bắt đầu", pd.Timestamp(data["start_date"]).strftime("%d/%m/%Y"))
    c4.metric("Ngày kết thúc", pd.Timestamp(data["end_date"]).strftime("%d/%m/%Y"))
    with st.expander("Xem chất lượng dữ liệu", expanded=True):
        st.dataframe(data["data_quality"], use_container_width=True, hide_index=True)
    with st.expander("Xem dữ liệu giá", expanded=False):
        st.dataframe(data["prices"].tail(20), use_container_width=True)
    with st.expander("Xem lợi suất", expanded=False):
        st.dataframe(data["returns"].tail(20), use_container_width=True)
    with st.expander("Xem benchmark", expanded=False):
        benchmark_table = pd.DataFrame({"Ngày": data["benchmark_prices"].index, data["benchmark"]: data["benchmark_prices"].values, "Lợi suất": data["benchmark_returns"].reindex(data["benchmark_prices"].index)}).dropna(how="all")
        st.dataframe(benchmark_table.tail(20), use_container_width=True, hide_index=True)
    with st.expander("Xem thông tin doanh nghiệp", expanded=False):
        st.dataframe(data["company_table"], use_container_width=True, hide_index=True)
    st.success("Dữ liệu nền đã sẵn sàng. Bước tiếp theo sẽ dùng Hồ sơ đầu tư để xây dựng trạng thái thị trường và phân bổ cổ phiếu.")
