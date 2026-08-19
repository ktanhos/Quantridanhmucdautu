import pandas as pd
import streamlit as st
from config import APP_NAME, DEFAULT_BENCHMARK, DEFAULT_TICKERS
from data_pipeline import load_market_dataset
from data_provider import configure_vnstock
from market_regime_ui import render_market_regime
from portfolio_risk_ui import render_portfolio_risk
from portfolio_optimization_ui import render_portfolio_optimization
from portfolio_recommendation_ui import render_recommendation
from portfolio_rebalancing_ui import render_rebalancing
from policy import InvestmentPolicy, risk_label, validate_policy
st.set_page_config(page_title=APP_NAME,page_icon='📊',layout='wide',initial_sidebar_state='expanded')
st.title('Quản trị danh mục đầu tư');st.caption('Danh mục cổ phiếu Việt Nam và tài sản phòng thủ. Market Regime được xác định độc lập với danh mục người dùng.')
if 'policy' not in st.session_state:st.session_state['policy']=None
st.header('Bước 1. Kết nối dữ liệu');api_key=st.text_input('Mã truy cập Vnstock',type='password')
st.header('Bước 2. Hồ sơ đầu tư')
goals={'Bảo toàn vốn':'Ưu tiên hạn chế thua lỗ.','Tăng trưởng ổn định':'Chấp nhận biến động vừa phải.','Tăng trưởng cao':'Chấp nhận biến động lớn hơn.'};investor_goal=st.radio('Mục tiêu chính',list(goals),horizontal=True);st.caption(goals[investor_goal]);target_return=st.number_input('Lợi nhuận mục tiêu mỗi năm (%)',0.,100.,12.,.5,format='%.1f');risk_tolerance=st.slider('Khẩu vị rủi ro',0,100,50,5);risk_capacity=st.slider('Khả năng chịu rủi ro',0,100,50,5);horizon_labels={1:'Dưới 2 năm',3:'2 đến 5 năm',7:'5 đến 10 năm',15:'Trên 10 năm'};investment_horizon_years=st.select_slider('Thời hạn đầu tư',options=list(horizon_labels),value=7,format_func=lambda x:horizon_labels[x]);liquidity_need=st.selectbox('Nhu cầu sử dụng tiền',['Cao','Trung bình','Thấp'])
c1,c2,c3=st.columns(3)
with c1:max_single_stock_weight=st.number_input('Tối đa một cổ phiếu (%)',1.,100.,10.,1.,format='%.1f')
with c2:max_sector_weight=st.number_input('Tối đa một ngành (%)',1.,100.,25.,1.,format='%.1f')
with c3:emergency_cash_percent=st.number_input('Tiền dự phòng tối thiểu (%)',0.,100.,10.,1.,format='%.1f')
allow_short=st.checkbox('Cho phép bán khống');allow_leverage=st.checkbox('Cho phép sử dụng đòn bẩy');defensive_asset=st.radio('Tài sản phòng thủ',['Tiền mặt','Tiền gửi ngắn hạn'],horizontal=True);benchmark=st.text_input('Benchmark',value=DEFAULT_BENCHMARK).strip().upper()
policy=InvestmentPolicy(investor_goal=investor_goal,target_return=target_return/100,risk_tolerance=risk_tolerance,risk_capacity=risk_capacity,investment_horizon_years=investment_horizon_years,liquidity_need=liquidity_need,benchmark=benchmark or DEFAULT_BENCHMARK,max_single_stock_weight=max_single_stock_weight/100,max_sector_weight=max_sector_weight/100,allow_short=allow_short,allow_leverage=allow_leverage,defensive_asset=defensive_asset,emergency_cash_percent=emergency_cash_percent/100);errors=validate_policy(policy)
if errors:
    for e in errors:st.warning(e)
else:st.success(f'Hồ sơ hợp lệ. Mục tiêu {target_return:.1f}% mỗi năm. Khẩu vị rủi ro {risk_label(risk_tolerance)}.')
if st.button('LƯU HỒ SƠ ĐẦU TƯ',type='primary',use_container_width=True,disabled=bool(errors)):st.session_state['policy']=policy.to_dict();st.success('Đã lưu hồ sơ.')
st.divider();st.header('Bước 3. Lấy dữ liệu');st.caption('Danh mục người dùng lấy giá và khối lượng riêng. Market Regime dùng VNINDEX OHLCV theo ngày, trong đó khối lượng VNINDEX dùng để đánh giá thanh khoản thị trường.')
col1,col2=st.columns(2)
with col1:tickers_text=st.text_input('Các mã cổ phiếu muốn theo dõi',value=', '.join(DEFAULT_TICKERS));start_date=st.date_input('Ngày bắt đầu',value=pd.Timestamp('2022-01-01').date())
with col2:end_date=st.date_input('Ngày kết thúc',value=pd.Timestamp.today().date());benchmark_data=st.text_input('Benchmark',value=benchmark or DEFAULT_BENCHMARK).strip().upper()
if st.button('LẤY DỮ LIỆU',type='secondary',use_container_width=True):
    if st.session_state.get('policy') is None:st.warning('Hãy lưu Hồ sơ đầu tư trước.');st.stop()
    tickers=list(dict.fromkeys([x.strip().upper() for x in tickers_text.split(',') if x.strip()]))
    if len(tickers)<2:st.error('Cần ít nhất 2 mã cổ phiếu.');st.stop()
    if start_date>=end_date:st.error('Ngày bắt đầu phải trước ngày kết thúc.');st.stop()
    configure_vnstock(api_key)
    try:
        with st.spinner('Đang lấy dữ liệu danh mục và VNINDEX OHLCV...'):st.session_state['market_data']=load_market_dataset(tickers,pd.Timestamp(start_date),pd.Timestamp(end_date),benchmark_data or DEFAULT_BENCHMARK)
    except Exception as exc:st.error(f'{type(exc).__name__}: {exc}');st.stop()
if 'market_data' in st.session_state:
    data=st.session_state['market_data'];st.header('Bước 4. Kiểm tra dữ liệu');c1,c2,c3,c4=st.columns(4);c1.metric('Số mã danh mục',len(data['prices'].columns));c2.metric('Số phiên',len(data['prices']));c3.metric('Ngày bắt đầu',pd.Timestamp(data['start_date']).strftime('%d/%m/%Y'));c4.metric('Ngày kết thúc',pd.Timestamp(data['end_date']).strftime('%d/%m/%Y'))
    with st.expander('Dữ liệu VNINDEX OHLCV',expanded=True):st.dataframe(data['benchmark_ohlcv'].tail(20),use_container_width=True)
    with st.expander('Khối lượng danh mục',expanded=False):st.dataframe(data['volumes'].tail(20),use_container_width=True)
    with st.expander('Chất lượng dữ liệu',expanded=False):st.dataframe(data['data_quality'],use_container_width=True,hide_index=True)
    with st.expander('Thông tin doanh nghiệp',expanded=False):st.dataframe(data['company_table'],use_container_width=True,hide_index=True)
    st.divider();render_market_regime(data['benchmark_prices'],None,data['benchmark_ohlcv']['volume']);st.caption('Market Regime được xác định từ VNINDEX OHLCV, độc lập với danh mục người dùng.')
    st.divider();render_portfolio_risk(data['returns'],data['benchmark_returns'])
    st.divider();render_portfolio_optimization(data['returns'],st.session_state.get('policy') or {})
    if 'optimization_result' in st.session_state:render_recommendation(data['returns'],st.session_state['optimization_result'],st.session_state.get('regime_result'),st.session_state.get('policy') or {})
    if 'optimization_result' in st.session_state:render_rebalancing(data['returns'],st.session_state['optimization_result'])
