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

st.set_page_config(page_title=APP_NAME, page_icon='📊', layout='wide', initial_sidebar_state='expanded')
st.title('Quản trị danh mục đầu tư')
st.caption('Công cụ định hướng xây dựng danh mục cổ phiếu Việt Nam theo dữ liệu thị trường và hồ sơ nhà đầu tư.')
if 'policy' not in st.session_state:
    st.session_state['policy'] = None

with st.expander('Chi phí và giả định tham khảo', expanded=False):
    c1,c2,c3,c4=st.columns(4)
    c1.metric('Phí giao dịch mua/bán','0,10%')
    c2.metric('Thuế khi bán','0,10%')
    c3.metric('Phí lưu ký','0,27 đồng/cổ phiếu/tháng')
    c4.metric('Lãi suất Margin','12%/năm')
    st.caption('Các thông số chỉ mang tính tham khảo. Ứng dụng không mô phỏng lịch sử giao dịch hoặc tính chi phí theo từng lệnh.')

st.header('Bước 1. Kết nối dữ liệu')
api_key=st.text_input('Mã truy cập Vnstock',type='password',key='api_key')

st.header('Bước 2. Hồ sơ và nguồn vốn đầu tư')
goals={
    'Bảo toàn vốn':'Ưu tiên hạn chế thua lỗ và biến động.',
    'Tăng trưởng ổn định':'Chấp nhận biến động vừa phải để tăng trưởng vốn.',
    'Tăng trưởng cao':'Chấp nhận biến động lớn hơn để tìm kiếm mức tăng trưởng cao hơn.'
}
investor_goal=st.radio('Mục tiêu chính',list(goals),horizontal=True,key='investor_goal')
st.caption(goals[investor_goal])

c1,c2=st.columns(2)
with c1:
    investment_capital=st.number_input('Vốn đầu tư dự kiến (VNĐ)',min_value=0.,value=100000000.,step=10000000.,format='%.0f',key='investment_capital_input')
with c2:
    target_return=st.number_input('Mục tiêu lợi nhuận mỗi năm (%)',0.,100.,12.,.5,format='%.1f',key='target_return',help='Đây là mức lợi nhuận bạn mong muốn đạt được, không phải dự báo chắc chắn của hệ thống. Mục tiêu càng cao thì hệ thống có thể phải chấp nhận nhiều rủi ro hơn hoặc đề xuất mở rộng tập cổ phiếu.')
st.caption('Mục tiêu lợi nhuận là yêu cầu đầu vào để so sánh các phương án, không phải cam kết lợi nhuận.')

risk_options={
    'Thận trọng':25,
    'Cân bằng':50,
    'Tăng trưởng':75
}
risk_profile=st.radio('Bạn chấp nhận mức biến động nào?',list(risk_options),horizontal=True,key='risk_profile',help='Nếu danh mục giảm mạnh trong ngắn hạn, mức nào khiến bạn vẫn có thể giữ kế hoạch đầu tư? Chọn mức gần với phản ứng thực tế của bạn, không phải mức lợi nhuận bạn mong muốn.')
risk_score=risk_options[risk_profile]
st.info(risk_profile_description(risk_score))
st.caption('Ứng dụng dùng câu trả lời này để chọn phương án có mức rủi ro phù hợp hơn. Bạn không cần tự chấm điểm rủi ro.')

with st.expander('Ràng buộc phân bổ',expanded=True):
    c1,c2=st.columns(2)
    with c1:
        max_single_stock_weight=st.number_input('Giới hạn một cổ phiếu (%)',1.,100.,20.,1.,format='%.1f',key='max_stock',help='Tỷ trọng tối đa dành cho một mã. Ví dụ 20% nghĩa là không quá 20% tổng vốn cổ phiếu được dành cho một mã. Nếu tập cổ phiếu quá ít, giới hạn này có thể khiến bài toán không thể phân bổ đủ 100%.')
    with c2:
        max_sector_weight=st.number_input('Giới hạn một ngành (%)',1.,100.,35.,1.,format='%.1f',key='max_sector',help='Giới hạn tổng tỷ trọng các cổ phiếu thuộc cùng một ngành. Phiên bản hiện tại dùng chủ yếu như một ràng buộc hồ sơ; dữ liệu ngành chưa phải đầu vào chính của thuật toán tối ưu.')
    st.caption('Nếu bạn chưa biết nên chọn gì, có thể giữ mức mặc định 20% cho một cổ phiếu. Hệ thống sẽ kiểm tra xem tập cổ phiếu có đủ rộng để áp dụng giới hạn này hay không.')

with st.expander('Tùy chọn nâng cao',expanded=False):
    allow_short=False
    st.checkbox('Cho phép bán khống',value=False,disabled=True,help='Phiên bản hiện tại không hỗ trợ bán khống.',key='short_disabled')
    allow_leverage=st.checkbox('Cho phép vay Margin',value=False,help='Chỉ dùng để định hướng mức độ chấp nhận vốn vay.',key='allow_leverage')
    margin_rate=st.number_input('Lãi suất vay Margin (%/năm)',9.,15.,12.,.25,format='%.2f',disabled=not allow_leverage,key='margin_rate')
    defensive_asset=st.radio('Tài sản phòng thủ',['Tiền mặt','Tiền gửi ngắn hạn'],horizontal=True,key='defensive_asset')

benchmark=st.text_input('Benchmark',value=DEFAULT_BENCHMARK,key='benchmark_profile').strip().upper()

# Các trường liquidity, emergency cash và time horizon chưa tham gia vào mô hình phiên bản này.
# Giữ giá trị nội bộ để tương thích với InvestmentPolicy và không buộc người dùng nhập tham số chưa có tác dụng.
policy=InvestmentPolicy(
    investor_goal=investor_goal,
    target_return=target_return/100,
    risk_tolerance=risk_score,
    risk_capacity=risk_score,
    investment_horizon_years=5,
    liquidity_need='Không đặt trong phiên bản hiện tại',
    benchmark=benchmark or DEFAULT_BENCHMARK,
    max_single_stock_weight=max_single_stock_weight/100,
    max_sector_weight=max_sector_weight/100,
    allow_short=allow_short,
    allow_leverage=allow_leverage,
    defensive_asset=defensive_asset,
    emergency_cash_percent=0.0
)
errors=validate_policy(policy)
if errors:
    for e in errors:st.warning(e)
else:
    st.success(f'Hồ sơ hợp lệ. Mục tiêu {target_return:.1f}% mỗi năm. Mức chấp nhận biến động: {risk_label(risk_score)}.')

if st.button('LƯU HỒ SƠ ĐẦU TƯ',type='primary',use_container_width=True,disabled=bool(errors),key='save_policy'):
    st.session_state['policy']=policy.to_dict()
    st.session_state['investment_capital']=investment_capital
    st.session_state['saved_margin_rate']=margin_rate/100
    for key in ['optimization_result','recommended_portfolio','recommendation_result','target_equity','portfolio_performance']:
        st.session_state.pop(key,None)
    if 'market_data' in st.session_state:
        st.info('Đã giữ nguyên dữ liệu thị trường đã tải. Thay đổi hồ sơ chỉ làm tính lại các bước phía sau, không cần gọi lại dữ liệu.')
    st.success('Đã lưu hồ sơ và nguồn vốn. Các bước phía sau sẽ tính lại theo hồ sơ mới.')

st.divider()
st.header('Bước 3. Lấy dữ liệu')
st.caption('Hệ thống xem xét tập cổ phiếu đầu vào và tự xây dựng các phương án phân bổ. Người dùng không cần nhập trước số mã hoặc tỷ trọng. Market Regime dùng VNINDEX OHLCV theo ngày, trong đó có khối lượng VNINDEX.')
col1,col2=st.columns(2)
with col1:
    tickers_text=st.text_input('Tập cổ phiếu để hệ thống xem xét',value=', '.join(DEFAULT_TICKERS),key='tickers_input')
    start_date=st.date_input('Ngày bắt đầu',value=pd.Timestamp('2022-01-01').date(),key='start_date')
with col2:
    end_date=st.date_input('Ngày kết thúc',value=pd.Timestamp.today().date(),key='end_date')
    benchmark_data=st.text_input('Benchmark',value=benchmark or DEFAULT_BENCHMARK,key='benchmark_data').strip().upper()

if st.button('LẤY DỮ LIỆU',type='secondary',use_container_width=True,key='load_data'):
    if st.session_state.get('policy') is None:
        st.warning('Hãy lưu Hồ sơ đầu tư trước.')
        st.stop()
    tickers=list(dict.fromkeys([x.strip().upper() for x in tickers_text.split(',') if x.strip()]))
    if len(tickers)<2:
        st.error('Cần ít nhất 2 mã cổ phiếu để so sánh và đa dạng hóa.')
        st.stop()
    if start_date>=end_date:
        st.error('Ngày bắt đầu phải trước ngày kết thúc.')
        st.stop()
    configure_vnstock(api_key)
    try:
        with st.spinner('Đang lấy dữ liệu danh mục và VNINDEX OHLCV...'):
            st.session_state['market_data']=load_market_dataset(tickers,pd.Timestamp(start_date),pd.Timestamp(end_date),benchmark_data or DEFAULT_BENCHMARK)
        for key in ['optimization_result','recommended_portfolio','recommendation_result','target_equity','portfolio_performance']:
            st.session_state.pop(key,None)
    except Exception as exc:
        st.error(f'{type(exc).__name__}: {exc}')
        st.stop()

if 'market_data' in st.session_state:
    data=st.session_state['market_data']
    st.header('Bước 4. Kiểm tra dữ liệu')
    c1,c2,c3,c4=st.columns(4)
    c1.metric('Số mã xem xét',len(data['prices'].columns))
    c2.metric('Số phiên',len(data['prices']))
    c3.metric('Ngày bắt đầu',pd.Timestamp(data['start_date']).strftime('%d/%m/%Y'))
    c4.metric('Ngày kết thúc',pd.Timestamp(data['end_date']).strftime('%d/%m/%Y'))
    quality=data['data_quality'].copy()
    pct_cols=['Tăng/Giảm 1M','Tăng/Giảm 6M','Tăng/Giảm 12M','Biến động Annualized','Độ phủ dữ liệu']
    for col in pct_cols:
        quality[col]=quality[col].map(lambda x:'N/A' if pd.isna(x) else f'{x:.2%}')
    quality['Giá hiện tại']=quality['Giá hiện tại'].map(lambda x:'N/A' if pd.isna(x) else f'{x:,.0f}')
    quality['Khối lượng TB']=quality['Khối lượng TB'].map(lambda x:'N/A' if pd.isna(x) else f'{x:,.0f}')
    quality['Số phiên có dữ liệu']=quality['Số phiên có dữ liệu'].map(lambda x:f'{int(x):,}')
    quality['Số phiên thiếu']=quality['Số phiên thiếu'].map(lambda x:f'{int(x):,}')
    quality=quality.rename(columns={'Giá hiện tại':'Giá hiện tại (VNĐ)','Biến động Annualized':'Volatility Annualized','Khối lượng TB':'Average Volume','Số phiên có dữ liệu':'Số phiên dữ liệu','Độ phủ dữ liệu':'Data Coverage'})
    st.subheader('Thống kê thị trường và chất lượng dữ liệu')
    st.dataframe(quality,use_container_width=True,hide_index=True)
    st.caption('1M khoảng 21 phiên, 6M khoảng 126 phiên và 12M khoảng 252 phiên. Volatility Annualized là độ biến động quy đổi về cơ sở một năm từ lợi suất ngày. Average Volume là khối lượng giao dịch bình quân mỗi phiên. Data Coverage là tỷ lệ phiên có dữ liệu hợp lệ.')
    st.divider()
    render_market_regime(data['benchmark_prices'],None,data['benchmark_ohlcv']['volume'])
    st.caption('Market Regime được xác định từ VNINDEX OHLCV, độc lập với danh mục mục tiêu.')
    st.divider()
    render_portfolio_risk(data['returns'],data['benchmark_returns'])
    st.divider()
    render_portfolio_optimization(data['returns'],st.session_state.get('policy') or {},data['benchmark_returns'])
    if 'optimization_result' in st.session_state:
        render_recommendation(data['returns'],st.session_state['optimization_result'],st.session_state.get('regime_result'),st.session_state.get('policy') or {})
    if 'target_equity' in st.session_state:
        render_portfolio_performance(data['returns'],data['benchmark_returns'],st.session_state['target_equity'])
    if 'portfolio_performance' in st.session_state:
        target_equity_total=float(pd.Series(st.session_state.get('target_equity'),dtype=float).sum())
        st.divider()
        render_portfolio_summary(st.session_state.get('portfolio_performance'),st.session_state.get('regime_result'),None,target_equity_total)
