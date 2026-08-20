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

# Giao diện giữ nguyên phong cách hiện có của ứng dụng.
st.markdown("""
<style>
:root{--bg:#080b12;--panel:#10151f;--panel-2:#141b27;--border:rgba(148,163,184,.14);--border-strong:rgba(148,163,184,.24);--text:#f4f7fb;--muted:#8993a4;--accent:#5b8cff;--accent-2:#7c6cff;--radius:16px;--shadow:0 14px 40px rgba(0,0,0,.18)}
.stApp{background:radial-gradient(circle at 82% 0%,rgba(91,140,255,.09),transparent 28%),radial-gradient(circle at 12% 20%,rgba(124,108,255,.045),transparent 25%),var(--bg);color:var(--text)}
.block-container{max-width:1500px;padding:2.2rem 3rem 5rem}[data-testid="stHeader"]{background:rgba(8,11,18,.72);backdrop-filter:blur(14px)}
h1,h2,h3{color:var(--text)!important;letter-spacing:-.025em}h1{font-size:2.45rem!important;font-weight:760!important;line-height:1.1!important}h2{font-size:1.42rem!important;font-weight:720!important;margin-top:2.35rem!important;margin-bottom:1rem!important;padding:0 0 0 .85rem;border-left:3px solid var(--accent)}h3{font-size:1.08rem!important;font-weight:680!important;margin-top:1.5rem!important}
.hero{position:relative;overflow:hidden;border:1px solid var(--border-strong);border-radius:24px;padding:2rem 2.1rem 1.65rem;margin:0 0 1.5rem;background:linear-gradient(135deg,rgba(18,25,38,.96),rgba(12,17,27,.92));box-shadow:var(--shadow)}
.hero-title{font-size:2rem;font-weight:780;line-height:1.12;margin-bottom:.55rem}.hero-subtitle{color:#9ba6b7;font-size:.92rem;line-height:1.65;max-width:930px}.hero-chip{display:inline-block;margin-top:1rem;margin-right:.42rem;padding:.36rem .72rem;border-radius:999px;border:1px solid var(--border-strong);font-size:.72rem;color:#b9c2d1;background:rgba(255,255,255,.035)}
.section-note,.small-note,.metric-note{color:var(--muted);font-size:.82rem;line-height:1.65}.section-note{margin-top:-.3rem;margin-bottom:1.05rem}
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#0d121b 0%,#090d14 100%);border-right:1px solid var(--border)}section[data-testid="stSidebar"] > div{padding-top:1.4rem}section[data-testid="stSidebar"] h3{font-size:.82rem!important;text-transform:uppercase;letter-spacing:.12em;color:#aeb8c8!important}
[data-testid="stMetric"]{border:1px solid var(--border);border-radius:14px;padding:1rem 1.05rem;background:linear-gradient(145deg,rgba(20,27,39,.88),rgba(13,18,27,.78));min-height:108px;box-shadow:0 7px 22px rgba(0,0,0,.12)}
[data-testid="stMetricLabel"]{font-size:.72rem!important;color:var(--muted)!important;font-weight:560!important}[data-testid="stMetricValue"]{font-size:1.55rem!important;font-weight:730!important;color:#f7f9fc!important}
div[data-baseweb="input"]>div,div[data-baseweb="select"]>div,div[data-baseweb="textarea"]>div{background:#0d131d!important;border-color:var(--border-strong)!important;border-radius:11px!important}input,textarea{color:var(--text)!important}label{color:#aeb7c6!important;font-size:.79rem!important;font-weight:560!important}
div.stButton>button{border-radius:11px!important;min-height:2.75rem;font-weight:680!important;letter-spacing:.01em;border:1px solid var(--border-strong)!important}div.stButton>button[kind="primary"]{background:linear-gradient(135deg,#5b8cff,#7166ed)!important;border:0!important}
[data-testid="stExpander"]{border:1px solid var(--border);border-radius:14px!important;overflow:hidden;background:rgba(14,20,29,.54)}
[data-testid="stDataFrame"]{border:1px solid var(--border);border-radius:14px;overflow:hidden;box-shadow:0 8px 25px rgba(0,0,0,.10)}
div[data-testid="stAlert"]{border-radius:13px!important;border:1px solid var(--border)!important;background:rgba(16,22,32,.72)!important}
hr{border-color:var(--border)!important;margin:1.5rem 0!important}.stCaption{color:var(--muted)!important}
@media(max-width:900px){.block-container{padding:1.25rem 1rem 3rem}.hero{padding:1.35rem 1.2rem}.hero-title{font-size:1.65rem}h1{font-size:2rem!important}h2{font-size:1.25rem!important}}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
<div class="hero-title">Quản trị danh mục đầu tư</div>
<div class="hero-subtitle">Hệ thống được tổ chức theo quy trình quản trị danh mục: bắt đầu từ mục tiêu và nguồn vốn, đánh giá bối cảnh thị trường, xác định ngân sách rủi ro, chọn cổ phiếu, tối ưu tỷ trọng, kiểm soát đòn bẩy và cuối cùng đánh giá hiệu quả.</div>
<span class="hero-chip">Quản trị danh mục</span><span class="hero-chip">Phân bổ tài sản</span><span class="hero-chip">Market Risk</span><span class="hero-chip">Tối ưu hóa</span><span class="hero-chip">Đòn bẩy</span>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### Kiến trúc quản trị danh mục")
    steps=[
        ("1","Quản trị danh mục",st.session_state.get("policy") is not None),
        ("2","Phân bổ tài sản",st.session_state.get("regime_result") is not None),
        ("3","Kiểm soát Market Risk","market_data" in st.session_state),
        ("4","Chọn cổ phiếu","market_data" in st.session_state),
        ("5","Tối ưu tỷ trọng","optimization_result" in st.session_state),
        ("6","Kiểm soát đòn bẩy","complete_portfolio_result" in st.session_state),
        ("7","Đánh giá hiệu quả","portfolio_performance" in st.session_state),
    ]
    for number,label,done in steps:
        mark="Đã sẵn sàng" if done else "Chưa thực hiện"
        color="#62d39b" if done else "#8f96a3"
        st.markdown(f'<div style="display:flex;gap:.6rem;align-items:center;margin:.38rem 0"><span style="width:25px;height:25px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;border:1px solid rgba(128,128,128,.25);font-size:.72rem">{number}</span><div><div style="font-size:.82rem;font-weight:600">{label}</div><div style="font-size:.68rem;color:{color}">{mark}</div></div></div>',unsafe_allow_html=True)
    st.divider()
    st.caption("Không đặt lệnh. Mục tiêu của ứng dụng là hỗ trợ ra quyết định và kiểm soát rủi ro.")

with st.expander("Chi phí và giả định tham khảo",expanded=False):
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Phí giao dịch mua/bán","0,10%")
    c2.metric("Thuế khi bán","0,10%")
    c3.metric("Phí lưu ký","0,27 đồng/cổ phiếu/tháng")
    c4.metric("Lãi suất Margin","12%/năm")
    st.caption("Các thông số chỉ mang tính tham khảo và cần cập nhật theo điều kiện thực tế.")

# 1. QUẢN TRỊ DANH MỤC
st.header("Bước 1. Quản trị danh mục")
st.markdown('<div class="section-note">Xác định mục tiêu, nguồn vốn, khả năng chịu rủi ro và các giới hạn trước khi nhìn vào mã cổ phiếu cụ thể.</div>',unsafe_allow_html=True)

api_key=st.text_input("Mã truy cập Vnstock",type="password",key="api_key")
goals={"Bảo toàn vốn":"Ưu tiên hạn chế thua lỗ và biến động.","Tăng trưởng ổn định":"Chấp nhận biến động vừa phải để tăng trưởng vốn.","Tăng trưởng cao":"Chấp nhận biến động lớn hơn để tìm kiếm mức tăng trưởng cao hơn."}
investor_goal=st.radio("Mục tiêu chính",list(goals),horizontal=True,key="investor_goal")
st.caption(goals[investor_goal])

c1,c2=st.columns(2)
with c1: investment_capital=st.number_input("Vốn đầu tư dự kiến (VNĐ)",min_value=0.,value=100000000.,step=10000000.,format="%.0f",key="investment_capital_input")
with c2: target_return=st.number_input("Mục tiêu lợi nhuận mỗi năm (%)",0.,100.,12.,.5,format="%.1f",key="target_return")

risk_options={"Thận trọng":25,"Cân bằng":50,"Tăng trưởng":75}
risk_profile=st.radio("Mức chấp nhận biến động",list(risk_options),horizontal=True,key="risk_profile")
risk_score=risk_options[risk_profile]
st.info(risk_profile_description(risk_score))

with st.expander("Giới hạn danh mục",expanded=True):
    c1,c2=st.columns(2)
    with c1:max_single_stock_weight=st.number_input("Giới hạn một cổ phiếu (%)",1.,100.,20.,1.,format="%.1f",key="max_stock")
    with c2:max_sector_weight=st.number_input("Giới hạn một ngành (%)",1.,100.,35.,1.,format="%.1f",key="max_sector")

with st.expander("Nguồn vốn, thanh khoản và đòn bẩy",expanded=True):
    c1,c2=st.columns(2)
    with c1:
        defensive_asset=st.radio("Tài sản phòng thủ",["Tiền mặt","Tiền gửi ngắn hạn"],horizontal=True,key="defensive_asset")
        emergency_cash_percent=st.number_input("Tiền mặt dự phòng (%)",0.,100.,0.,1.,format="%.1f",key="emergency_cash")
    with c2:
        allow_leverage=st.checkbox("Cho phép vay Margin",value=False,key="allow_leverage",help="Cho phép tổng phơi nhiễm cổ phiếu vượt 100% vốn tự có trong giới hạn đòn bẩy.")
        margin_rate=st.number_input("Lãi suất vay Margin (%/năm)",9.,20.,12.,.25,format="%.2f",disabled=not allow_leverage,key="margin_rate")
        max_leverage=st.number_input("Đòn bẩy tối đa trên vốn tự có (lần)",1.,3.,2.,.1,format="%.1f",disabled=not allow_leverage,key="max_leverage")

benchmark=st.text_input("Benchmark",value=DEFAULT_BENCHMARK,key="benchmark_profile").strip().upper()
risk_free_rate=st.number_input("Lãi suất phi rủi ro (%/năm)",0.,15.,4.,.25,format="%.2f",key="risk_free_rate")
policy=InvestmentPolicy(
    investor_goal=investor_goal,target_return=target_return/100,risk_tolerance=risk_score,risk_capacity=risk_score,
    investment_horizon_years=5,liquidity_need="Không đặt trong phiên bản hiện tại",benchmark=benchmark or DEFAULT_BENCHMARK,
    max_single_stock_weight=max_single_stock_weight/100,max_sector_weight=max_sector_weight/100,allow_short=False,
    allow_leverage=allow_leverage,defensive_asset=defensive_asset,emergency_cash_percent=emergency_cash_percent/100,risk_free_rate=risk_free_rate/100,
)
# Các tham số runtime được lưu thêm trong policy để tầng Complete Portfolio không phải phụ thuộc giao diện.
policy_dict=policy.to_dict();policy_dict.update({"margin_rate":margin_rate/100,"max_leverage":max_leverage})
errors=validate_policy(policy)
if errors:
    for e in errors:st.warning(e)
else:
    st.success(f"Hồ sơ hợp lệ. Mục tiêu {target_return:.1f}% mỗi năm. Mức chấp nhận biến động: {risk_label(risk_score)}.")

if st.button("LƯU HỒ SƠ ĐẦU TƯ",type="primary",use_container_width=True,key="save_policy",disabled=bool(errors)):
    st.session_state["policy"]=policy_dict
    st.session_state["investment_capital"]=investment_capital
    st.session_state["saved_margin_rate"]=margin_rate/100
    st.session_state["saved_max_leverage"]=max_leverage
    for key in ["regime_result","optimization_result","recommended_portfolio","recommendation_result","complete_portfolio_result","target_equity","portfolio_performance"]:st.session_state.pop(key,None)
    st.success("Đã lưu hồ sơ. Từ đây hệ thống sẽ đi theo quy trình quản trị danh mục.")

# 2. PHÂN BỔ TÀI SẢN
st.header("Bước 2. Phân bổ tài sản theo bối cảnh thị trường")
st.markdown('<div class="section-note">Market Regime được sử dụng để xác định ngân sách cổ phiếu trước khi chọn tỷ trọng từng mã. Đây là tầng phân bổ tài sản, không phải tầng chọn cổ phiếu.</div>',unsafe_allow_html=True)

st.subheader("Nguồn dữ liệu")
col1,col2=st.columns(2)
with col1: tickers_text=st.text_input("Tập cổ phiếu để hệ thống xem xét",value=", ".join(DEFAULT_TICKERS),key="tickers_input")
with col2: benchmark_data=st.text_input("Benchmark dữ liệu",value=benchmark or DEFAULT_BENCHMARK,key="benchmark_data").strip().upper()
col1,col2=st.columns(2)
with col1:start_date=st.date_input("Ngày bắt đầu",value=pd.Timestamp("2022-01-01").date(),key="start_date")
with col2:end_date=st.date_input("Ngày kết thúc",value=pd.Timestamp.today().date(),key="end_date")

if st.button("LẤY DỮ LIỆU VÀ XÁC ĐỊNH NGÂN SÁCH CỔ PHIẾU",type="secondary",use_container_width=True,key="load_data"):
    if st.session_state.get("policy") is None:
        st.warning("Hãy lưu Hồ sơ đầu tư trước.");st.stop()
    tickers=list(dict.fromkeys([x.strip().upper() for x in tickers_text.split(",") if x.strip()]))
    if len(tickers)<2:st.error("Cần ít nhất 2 mã cổ phiếu.");st.stop()
    if start_date>=end_date:st.error("Ngày bắt đầu phải trước ngày kết thúc.");st.stop()
    configure_vnstock(api_key)
    try:
        with st.spinner("Đang lấy dữ liệu và xác định Market Regime..."):
            data=load_market_dataset(tickers,pd.Timestamp(start_date),pd.Timestamp(end_date),benchmark_data or DEFAULT_BENCHMARK)
            st.session_state["market_data"]=data
        for key in ["optimization_result","recommended_portfolio","recommendation_result","complete_portfolio_result","target_equity","portfolio_performance"]:st.session_state.pop(key,None)
    except Exception as exc:
        st.error(f"{type(exc).__name__}: {exc}");st.stop()

if "market_data" in st.session_state:
    data=st.session_state["market_data"]

    st.header("Bước 3. Kiểm soát Market Risk")
    quality=data["data_quality"].copy()
    pct_cols=["Tăng/Giảm 1M","Tăng/Giảm 6M","Tăng/Giảm 12M","Biến động Annualized","Độ phủ dữ liệu"]
    for col in pct_cols:
        if col in quality.columns:quality[col]=quality[col].map(lambda x:"N/A" if pd.isna(x) else f"{x:.2%}")
    for col in ["Giá hiện tại","Khối lượng TB"]:
        if col in quality.columns:quality[col]=quality[col].map(lambda x:"N/A" if pd.isna(x) else f"{x:,.2f}")
    st.subheader("Chất lượng dữ liệu")
    st.dataframe(quality,use_container_width=True,hide_index=True)

    render_market_regime(data["benchmark_prices"],None,data["benchmark_ohlcv"]["volume"])
    regime_result=st.session_state.get("regime_result")
    if regime_result is not None:
        st.session_state["asset_allocation_result"]={
            "regime":getattr(regime_result,"regime","Trung tính"),
            "score":float(getattr(regime_result,"score",50)),
            "equity_min":float(getattr(regime_result,"equity_min",0.5)),
            "equity_max":float(getattr(regime_result,"equity_max",0.7)),
            "defensive_min":1.0-float(getattr(regime_result,"equity_max",0.7)),
            "defensive_max":1.0-float(getattr(regime_result,"equity_min",0.5)),
        }
        a=st.session_state["asset_allocation_result"]
        st.subheader("Ngân sách tài sản")
        c1,c2,c3,c4=st.columns(4)
        c1.metric("Market Regime",a["regime"]);c2.metric("Điểm Regime",f'{a["score"]:.1f}/100');c3.metric("Cổ phiếu tối thiểu",f'{a["equity_min"]:.0%}');c4.metric("Cổ phiếu tối đa",f'{a["equity_max"]:.0%}')
        st.caption(f'Phần còn lại được dành cho {policy_dict.get("defensive_asset","tài sản phòng thủ")}, trong khoảng {a["defensive_min"]:.0%} đến {a["defensive_max"]:.0%}.')

    st.header("Bước 4. Chọn cổ phiếu")
    st.markdown('<div class="section-note">Sau khi xác định ngân sách cổ phiếu, hệ thống mới đánh giá quan hệ lợi suất, biến động và hiệp phương sai để tìm cấu trúc cổ phiếu phù hợp.</div>',unsafe_allow_html=True)
    rf=float((st.session_state.get("policy") or {}).get("risk_free_rate",0.04))
    render_portfolio_risk(data["returns"],data["benchmark_returns"],risk_free_rate=rf)

    st.header("Bước 5. Tối ưu tỷ trọng")
    render_portfolio_optimization(data["returns"],st.session_state.get("policy") or {},data["benchmark_returns"])

    if "optimization_result" in st.session_state and regime_result is not None:
        st.header("Bước 6. Kiểm soát đòn bẩy và xây dựng Complete Portfolio")
        render_recommendation(data["returns"],st.session_state["optimization_result"],regime_result,st.session_state.get("policy") or {})

    if "target_equity" in st.session_state:
        st.header("Bước 7. Đánh giá hiệu quả")
        render_portfolio_performance(data["returns"],data["benchmark_returns"],st.session_state["target_equity"],risk_free_rate=rf)
    if "portfolio_performance" in st.session_state:
        target_equity_total=float(pd.Series(st.session_state.get("target_equity"),dtype=float).sum())
        st.divider()
        render_portfolio_summary(st.session_state.get("portfolio_performance"),st.session_state.get("regime_result"),None,target_equity_total)
