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

st.markdown("""
<style>
:root{
    --bg:#080b12;
    --panel:#10151f;
    --panel-2:#141b27;
    --panel-3:#0d121b;
    --border:rgba(148,163,184,.14);
    --border-strong:rgba(148,163,184,.24);
    --text:#f4f7fb;
    --muted:#8993a4;
    --muted-2:#657083;
    --accent:#5b8cff;
    --accent-2:#7c6cff;
    --positive:#2fcf8f;
    --negative:#ff647c;
    --warning:#f3b94f;
    --radius:16px;
    --shadow:0 14px 40px rgba(0,0,0,.18);
}

.stApp{
    background:
        radial-gradient(circle at 82% 0%,rgba(91,140,255,.09),transparent 28%),
        radial-gradient(circle at 12% 20%,rgba(124,108,255,.045),transparent 25%),
        var(--bg);
    color:var(--text);
}

.block-container{max-width:1500px;padding:2.2rem 3rem 5rem}
[data-testid="stHeader"]{background:rgba(8,11,18,.72);backdrop-filter:blur(14px)}

h1,h2,h3{color:var(--text)!important;letter-spacing:-.025em}
h1{font-size:2.45rem!important;font-weight:760!important;line-height:1.1!important}
h2{font-size:1.42rem!important;font-weight:720!important;margin-top:2.35rem!important;margin-bottom:1rem!important;padding:0 0 0 .85rem;border-left:3px solid var(--accent)}
h3{font-size:1.08rem!important;font-weight:680!important;margin-top:1.5rem!important}

.hero{
    position:relative;overflow:hidden;
    border:1px solid var(--border-strong);
    border-radius:24px;
    padding:2rem 2.1rem 1.65rem;
    margin:0 0 1.5rem;
    background:linear-gradient(135deg,rgba(18,25,38,.96),rgba(12,17,27,.92));
    box-shadow:var(--shadow);
}
.hero:before{
    content:"";position:absolute;width:360px;height:360px;right:-150px;top:-210px;border-radius:50%;
    background:radial-gradient(circle,rgba(91,140,255,.22),transparent 68%);pointer-events:none;
}
.hero:after{
    content:"";position:absolute;left:0;right:0;bottom:0;height:1px;background:linear-gradient(90deg,transparent,rgba(91,140,255,.45),transparent);
}
.hero-title{font-size:2rem;font-weight:780;line-height:1.12;margin-bottom:.55rem;position:relative;z-index:1}
.hero-subtitle{color:#9ba6b7;font-size:.92rem;line-height:1.65;max-width:930px;position:relative;z-index:1}
.hero-chip{display:inline-block;margin-top:1rem;margin-right:.42rem;padding:.36rem .72rem;border-radius:999px;border:1px solid var(--border-strong);font-size:.72rem;color:#b9c2d1;background:rgba(255,255,255,.035);position:relative;z-index:1}

.section-note{color:var(--muted);font-size:.86rem;line-height:1.65;margin-top:-.3rem;margin-bottom:1.05rem}
.small-note,.metric-note{color:var(--muted);font-size:.76rem;line-height:1.55}

/* Thanh bên */
section[data-testid="stSidebar"]{
    background:linear-gradient(180deg,#0d121b 0%,#090d14 100%);
    border-right:1px solid var(--border);
}
section[data-testid="stSidebar"] > div{padding-top:1.4rem}
section[data-testid="stSidebar"] h3{font-size:.82rem!important;text-transform:uppercase;letter-spacing:.12em;color:#aeb8c8!important}
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"]{color:var(--muted-2)}

/* Thẻ chỉ số */
[data-testid="stMetric"]{
    border:1px solid var(--border);
    border-radius:14px;
    padding:1rem 1.05rem;
    background:linear-gradient(145deg,rgba(20,27,39,.88),rgba(13,18,27,.78));
    min-height:108px;
    box-shadow:0 7px 22px rgba(0,0,0,.12);
    transition:transform .16s ease,border-color .16s ease,background .16s ease;
}
[data-testid="stMetric"]:hover{transform:translateY(-1px);border-color:rgba(91,140,255,.32);background:linear-gradient(145deg,rgba(23,31,45,.94),rgba(13,18,27,.84))}
[data-testid="stMetricLabel"]{font-size:.72rem!important;color:var(--muted)!important;font-weight:560!important}
[data-testid="stMetricValue"]{font-size:1.55rem!important;font-weight:730!important;letter-spacing:-.025em;color:#f7f9fc!important}
[data-testid="stMetricDelta"]{font-size:.72rem!important}

/* Ô nhập liệu */
div[data-baseweb="input"],div[data-baseweb="select"],div[data-baseweb="textarea"]{
    border-radius:11px;
}
div[data-baseweb="input"] > div,div[data-baseweb="select"] > div,div[data-baseweb="textarea"] > div{
    background:#0d131d!important;border-color:var(--border-strong)!important;border-radius:11px!important;
}
input,textarea{color:var(--text)!important}
label{color:#aeb7c6!important;font-size:.79rem!important;font-weight:560!important}

/* Nút */
div.stButton>button{
    border-radius:11px!important;
    min-height:2.75rem;
    font-weight:680!important;
    letter-spacing:.01em;
    border:1px solid var(--border-strong)!important;
    transition:all .16s ease!important;
}
div.stButton>button:hover{transform:translateY(-1px);border-color:rgba(91,140,255,.55)!important;box-shadow:0 8px 24px rgba(0,0,0,.2)!important}
div.stButton>button[kind="primary"]{background:linear-gradient(135deg,#5b8cff,#7166ed)!important;border:0!important;box-shadow:0 8px 24px rgba(91,140,255,.16)!important}

/* Thẻ mở rộng */
[data-testid="stExpander"]{border:1px solid var(--border);border-radius:14px!important;overflow:hidden;background:rgba(14,20,29,.54)}
[data-testid="stExpander"] summary{padding:.75rem .9rem!important}

/* Bảng */
[data-testid="stDataFrame"]{border:1px solid var(--border);border-radius:14px;overflow:hidden;box-shadow:0 8px 25px rgba(0,0,0,.10)}
[data-testid="stDataFrame"] div[role="columnheader"]{font-size:.73rem!important;font-weight:650!important}

/* Thông báo */
div[data-testid="stAlert"]{border-radius:13px!important;border:1px solid var(--border)!important;background:rgba(16,22,32,.72)!important}

/* Tab */
button[data-baseweb="tab"]{font-size:.79rem!important;font-weight:650!important;color:var(--muted)!important;padding:0 1rem!important}
button[data-baseweb="tab"][aria-selected="true"]{color:#f3f6fb!important}
div[data-baseweb="tab-highlight"]{background:linear-gradient(90deg,var(--accent),var(--accent-2))!important;height:2px!important}

/* Bộ chọn */
div[role="radiogroup"] label,div[role="group"] label{border-radius:10px!important}

/* Đường phân cách */
hr{border-color:var(--border)!important;margin:1.5rem 0!important}

/* Biểu đồ */
[data-testid="stVegaLiteChart"]{border:1px solid var(--border);border-radius:14px;padding:.35rem;background:rgba(13,18,27,.55)}

/* Chữ phụ */
.stCaption{color:var(--muted)!important}

/* Mobile */
@media(max-width:900px){
    .block-container{padding:1.25rem 1rem 3rem}
    .hero{padding:1.35rem 1.2rem}
    .hero-title{font-size:1.65rem}
    h1{font-size:2rem!important}
    h2{font-size:1.25rem!important}
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <div class="hero-title">Quản trị danh mục đầu tư</div>
    <div class="hero-subtitle">Công cụ định hướng xây dựng danh mục cổ phiếu Việt Nam theo dữ liệu thị trường, trạng thái thị trường và hồ sơ nhà đầu tư. Người dùng đi từ mục tiêu đến phương án phân bổ thay vì phải tự nhập một danh mục có sẵn.</div>
    <span class="hero-chip">Dữ liệu thị trường Việt Nam</span>
    <span class="hero-chip">Phân tích rủi ro</span>
    <span class="hero-chip">Tối ưu hóa danh mục</span>
    <span class="hero-chip">So sánh với VNINDEX</span>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### Quy trình")
    steps=[
        ("1","Kết nối dữ liệu",True),
        ("2","Hồ sơ đầu tư",st.session_state.get("policy") is not None),
        ("3","Lấy dữ liệu","market_data" in st.session_state),
        ("4","Kiểm tra dữ liệu","market_data" in st.session_state),
        ("5","Market Regime","regime_result" in st.session_state),
        ("6","Phân tích rủi ro","market_data" in st.session_state),
        ("7","Tối ưu hóa","optimization_result" in st.session_state),
        ("8","Đề xuất phân bổ","recommendation_result" in st.session_state),
        ("9","Hiệu quả lịch sử","portfolio_performance" in st.session_state),
        ("11","Tổng kết","portfolio_performance" in st.session_state),
    ]
    for number,label,done in steps:
        mark="Đã sẵn sàng" if done else "Chưa thực hiện"
        color="#62d39b" if done else "#8f96a3"
        st.markdown(f'<div style="display:flex;gap:.6rem;align-items:center;margin:.38rem 0"><span style="width:25px;height:25px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;border:1px solid rgba(128,128,128,.25);font-size:.72rem">{number}</span><div><div style="font-size:.82rem;font-weight:600">{label}</div><div style="font-size:.68rem;color:{color}">{mark}</div></div></div>',unsafe_allow_html=True)
    st.divider()
    st.caption("Ứng dụng tập trung vào hướng dẫn xây dựng danh mục. Không đặt lệnh và không yêu cầu nhập lịch sử giao dịch.")

with st.expander("Chi phí và giả định tham khảo",expanded=False):
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Phí giao dịch mua/bán","0,10%")
    c2.metric("Thuế khi bán","0,10%")
    c3.metric("Phí lưu ký","0,27 đồng/cổ phiếu/tháng")
    c4.metric("Lãi suất Margin","12%/năm")
    st.caption("Các thông số chỉ mang tính tham khảo. Ứng dụng không mô phỏng lịch sử giao dịch hoặc tính chi phí theo từng lệnh.")

st.header("Bước 1. Kết nối dữ liệu")
st.markdown('<div class="section-note">Nhập mã truy cập để ứng dụng lấy dữ liệu giá, khối lượng và VNINDEX phục vụ các bước phân tích phía sau.</div>',unsafe_allow_html=True)
api_key=st.text_input("Mã truy cập Vnstock",type="password",key="api_key")

st.header("Bước 2. Hồ sơ và nguồn vốn đầu tư")
goals={"Bảo toàn vốn":"Ưu tiên hạn chế thua lỗ và biến động.","Tăng trưởng ổn định":"Chấp nhận biến động vừa phải để tăng trưởng vốn.","Tăng trưởng cao":"Chấp nhận biến động lớn hơn để tìm kiếm mức tăng trưởng cao hơn."}
investor_goal=st.radio("Mục tiêu chính",list(goals),horizontal=True,key="investor_goal")
st.caption(goals[investor_goal])

c1,c2=st.columns(2)
with c1:
    investment_capital=st.number_input("Vốn đầu tư dự kiến (VNĐ)",min_value=0.,value=100000000.,step=10000000.,format="%.0f",key="investment_capital_input")
with c2:
    target_return=st.number_input("Mục tiêu lợi nhuận mỗi năm (%)",0.,100.,12.,.5,format="%.1f",key="target_return",help="Đây là mức lợi nhuận mong muốn để so sánh các phương án, không phải dự báo chắc chắn.")
st.caption("Mục tiêu lợi nhuận là yêu cầu đầu vào để so sánh các phương án, không phải cam kết lợi nhuận.")

risk_options={"Thận trọng":25,"Cân bằng":50,"Tăng trưởng":75}
risk_profile=st.radio("Bạn chấp nhận mức biến động nào?",list(risk_options),horizontal=True,key="risk_profile",help="Chọn mức gần với phản ứng thực tế của bạn khi danh mục giảm mạnh.")
risk_score=risk_options[risk_profile]
st.info(risk_profile_description(risk_score))

with st.expander("Ràng buộc phân bổ",expanded=True):
    c1,c2=st.columns(2)
    with c1:
        max_single_stock_weight=st.number_input("Giới hạn một cổ phiếu (%)",1.,100.,20.,1.,format="%.1f",key="max_stock",help="Tỷ trọng tối đa dành cho một mã.")
    with c2:
        max_sector_weight=st.number_input("Giới hạn một ngành (%)",1.,100.,35.,1.,format="%.1f",key="max_sector",help="Giới hạn tổng tỷ trọng các cổ phiếu cùng ngành.")
    st.caption("Giới hạn ngành hiện được lưu trong hồ sơ; thuật toán tối ưu hiện tại chưa dùng dữ liệu ngành làm ràng buộc toán học.")

with st.expander("Tùy chọn nâng cao",expanded=False):
    allow_short=False
    st.checkbox("Cho phép bán khống",value=False,disabled=True,help="Phiên bản hiện tại không hỗ trợ bán khống.",key="short_disabled")
    allow_leverage=st.checkbox("Cho phép vay Margin",value=False,key="allow_leverage",help="Chỉ dùng để định hướng mức độ chấp nhận vốn vay.")
    margin_rate=st.number_input("Lãi suất vay Margin (%/năm)",9.,15.,12.,.25,format="%.2f",disabled=not allow_leverage,key="margin_rate")
    defensive_asset=st.radio("Tài sản phòng thủ",["Tiền mặt","Tiền gửi ngắn hạn"],horizontal=True,key="defensive_asset")
    risk_free_rate=st.number_input("Lãi suất phi rủi ro (%/năm)",0.,15.,4.,.25,format="%.2f",key="risk_free_rate",help="Giả định dùng cho Sharpe, Sortino, Treynor, Jensen Alpha và tối ưu hóa. Nên cập nhật theo công cụ phi rủi ro phù hợp với kỳ đánh giá.")

benchmark=st.text_input("Benchmark",value=DEFAULT_BENCHMARK,key="benchmark_profile").strip().upper()
policy=InvestmentPolicy(
    investor_goal=investor_goal,target_return=target_return/100,risk_tolerance=risk_score,risk_capacity=risk_score,
    investment_horizon_years=5,liquidity_need="Không đặt trong phiên bản hiện tại",benchmark=benchmark or DEFAULT_BENCHMARK,
    max_single_stock_weight=max_single_stock_weight/100,max_sector_weight=max_sector_weight/100,allow_short=allow_short,
    allow_leverage=allow_leverage,defensive_asset=defensive_asset,emergency_cash_percent=0.0,risk_free_rate=risk_free_rate/100,
)
errors=validate_policy(policy)
if errors:
    for e in errors:st.warning(e)
else:
    st.success(f"Hồ sơ hợp lệ. Mục tiêu {target_return:.1f}% mỗi năm. Mức chấp nhận biến động: {risk_label(risk_score)}. Lãi suất phi rủi ro: {risk_free_rate:.2f}%.")

if st.button("LƯU HỒ SƠ ĐẦU TƯ",type="primary",use_container_width=True,disabled=bool(errors),key="save_policy"):
    st.session_state["policy"]=policy.to_dict()
    st.session_state["investment_capital"]=investment_capital
    st.session_state["saved_margin_rate"]=margin_rate/100
    for key in ["optimization_result","recommended_portfolio","recommendation_result","target_equity","portfolio_performance"]:st.session_state.pop(key,None)
    st.success("Đã lưu hồ sơ và nguồn vốn. Các bước phía sau sẽ tính lại theo hồ sơ mới.")

st.divider()
st.header("Bước 3. Lấy dữ liệu")
st.markdown('<div class="section-note">Chọn tập cổ phiếu để hệ thống nghiên cứu. Đây là tập đầu vào để tìm phương án phân bổ, không phải danh mục đang nắm giữ.</div>',unsafe_allow_html=True)
col1,col2=st.columns(2)
with col1:
    tickers_text=st.text_input("Tập cổ phiếu để hệ thống xem xét",value=", ".join(DEFAULT_TICKERS),key="tickers_input")
    start_date=st.date_input("Ngày bắt đầu",value=pd.Timestamp("2022-01-01").date(),key="start_date")
with col2:
    end_date=st.date_input("Ngày kết thúc",value=pd.Timestamp.today().date(),key="end_date")
    benchmark_data=st.text_input("Benchmark",value=benchmark or DEFAULT_BENCHMARK,key="benchmark_data").strip().upper()

if st.button("LẤY DỮ LIỆU",type="secondary",use_container_width=True,key="load_data"):
    if st.session_state.get("policy") is None:
        st.warning("Hãy lưu Hồ sơ đầu tư trước.");st.stop()
    tickers=list(dict.fromkeys([x.strip().upper() for x in tickers_text.split(",") if x.strip()]))
    if len(tickers)<2:
        st.error("Cần ít nhất 2 mã cổ phiếu để so sánh và đa dạng hóa.");st.stop()
    if start_date>=end_date:
        st.error("Ngày bắt đầu phải trước ngày kết thúc.");st.stop()
    configure_vnstock(api_key)
    try:
        with st.spinner("Đang lấy dữ liệu danh mục và VNINDEX OHLCV..."):
            st.session_state["market_data"]=load_market_dataset(tickers,pd.Timestamp(start_date),pd.Timestamp(end_date),benchmark_data or DEFAULT_BENCHMARK)
        for key in ["optimization_result","recommended_portfolio","recommendation_result","target_equity","portfolio_performance"]:st.session_state.pop(key,None)
    except Exception as exc:
        st.error(f"{type(exc).__name__}: {exc}");st.stop()

if "market_data" in st.session_state:
    data=st.session_state["market_data"]
    st.header("Bước 4. Kiểm tra dữ liệu")
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Số mã xem xét",len(data["prices"].columns));c2.metric("Số phiên",len(data["prices"]))
    c3.metric("Ngày bắt đầu",pd.Timestamp(data["start_date"]).strftime("%d/%m/%Y"));c4.metric("Ngày kết thúc",pd.Timestamp(data["end_date"]).strftime("%d/%m/%Y"))
    quality=data["data_quality"].copy()
    pct_cols=["Tăng/Giảm 1M","Tăng/Giảm 6M","Tăng/Giảm 12M","Biến động Annualized","Độ phủ dữ liệu"]
    for col in pct_cols:quality[col]=quality[col].map(lambda x:"N/A" if pd.isna(x) else f"{x:.2%}")
    quality["Giá hiện tại"]=quality["Giá hiện tại"].map(lambda x:"N/A" if pd.isna(x) else f"{x:,.2f}")
    quality["Khối lượng TB"]=quality["Khối lượng TB"].map(lambda x:"N/A" if pd.isna(x) else f"{x:,.0f}")
    quality["Số phiên có dữ liệu"]=quality["Số phiên có dữ liệu"].map(lambda x:f"{int(x):,}")
    quality["Số phiên thiếu"]=quality["Số phiên thiếu"].map(lambda x:f"{int(x):,}")
    quality=quality.rename(columns={"Giá hiện tại":"Giá hiện tại (nghìn đồng)","Biến động Annualized":"Volatility Annualized","Khối lượng TB":"Average Volume","Số phiên có dữ liệu":"Số phiên dữ liệu","Độ phủ dữ liệu":"Data Coverage"})
    st.subheader("Thống kê thị trường và chất lượng dữ liệu")
    st.dataframe(quality,use_container_width=True,hide_index=True)
    st.caption("Giá cổ phiếu hiển thị theo chuẩn dữ liệu Vnstock hiện tại: đơn vị nghìn đồng và hai chữ số thập phân. Các chỉ tiêu lợi suất và biến động được tính từ chuỗi giá gốc.")

    st.divider()
    render_market_regime(data["benchmark_prices"],None,data["benchmark_ohlcv"]["volume"])
    st.caption("Market Regime được xác định từ VNINDEX OHLCV, độc lập với danh mục mục tiêu.")
    st.divider()
    rf=float((st.session_state.get("policy") or {}).get("risk_free_rate",0.04))
    render_portfolio_risk(data["returns"],data["benchmark_returns"],risk_free_rate=rf)
    st.divider()
    render_portfolio_optimization(data["returns"],st.session_state.get("policy") or {},data["benchmark_returns"])
    if "optimization_result" in st.session_state:
        render_recommendation(data["returns"],st.session_state["optimization_result"],st.session_state.get("regime_result"),st.session_state.get("policy") or {})
    if "target_equity" in st.session_state:
        render_portfolio_performance(data["returns"],data["benchmark_returns"],st.session_state["target_equity"],risk_free_rate=rf)
    if "portfolio_performance" in st.session_state:
        target_equity_total=float(pd.Series(st.session_state.get("target_equity"),dtype=float).sum())
        st.divider()
        render_portfolio_summary(st.session_state.get("portfolio_performance"),st.session_state.get("regime_result"),None,target_equity_total)
