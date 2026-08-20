import numpy as np
import pandas as pd
import streamlit as st
from portfolio_risk import calculate_portfolio_risk


def _fmt_pct(x): return 'N/A' if pd.isna(x) else f'{x:.2%}'
def _fmt_ratio(x): return 'N/A' if pd.isna(x) or not np.isfinite(x) else f'{x:.2f}'


def render_portfolio_performance(returns,benchmark_returns=None,current_weights=None,risk_free_rate=0.0):
    st.header('Bước 9. Đánh giá hiệu quả lịch sử phương án')
    st.markdown('<div class="section-note">Đánh giá trên dữ liệu quá khứ theo bốn góc nhìn: lợi suất tuyệt đối, hiệu quả điều chỉnh theo tổng rủi ro, hiệu quả so với VNINDEX và mức sụt giảm. Đây là đánh giá lịch sử, không phải dự báo tương lai.</div>',unsafe_allow_html=True)
    leverage=st.session_state.get('complete_portfolio_result') or {}
    borrowed=float(leverage.get('borrowed_weight',0.0));margin_rate=float(leverage.get('margin_rate',0.0));leveraged=borrowed>1e-10
    if current_weights is not None and len(current_weights)>0:
        w=pd.Series(current_weights,dtype=float).reindex(returns.columns).fillna(0)
        if w.sum()<=0: st.error('Danh mục mục tiêu không có tỷ trọng hợp lệ.');return
        if leveraged:
            portfolio=returns.mul(w,axis=1).sum(axis=1)-borrowed*margin_rate/252
            label='Phương án đề xuất có vay tiền'
        else:
            w=w/w.sum();portfolio=returns.mul(w,axis=1).sum(axis=1);label='Phương án đề xuất'
    else:
        w=pd.Series(1/len(returns.columns),index=returns.columns);portfolio=returns.mul(w,axis=1).sum(axis=1);label='Tập cổ phiếu bình quân'

    portfolio=portfolio.replace([np.inf,-np.inf],np.nan).dropna()
    p=calculate_portfolio_risk(pd.DataFrame({'Portfolio':portfolio}),pd.Series({'Portfolio':1.0}),benchmark_returns,risk_free_rate)
    b=calculate_portfolio_risk(pd.DataFrame({'VNINDEX':benchmark_returns}),pd.Series({'VNINDEX':1.0}),None,risk_free_rate) if benchmark_returns is not None else None
    st.session_state['portfolio_performance']={'Cumulative Return':float((1+p['portfolio_returns']).prod()-1),'Annualized Return':p['annual_return'],'Annualized Volatility':p['annual_volatility'],'Sharpe Ratio':p['sharpe'],'Maximum Drawdown':p['max_drawdown']}

    if leveraged:
        st.warning(f'Đánh giá đã tính chi phí vay ở mức {margin_rate:.2%}/năm trên phần vốn vay {borrowed:.1%}. Đây là giả định mô hình, chưa mô phỏng biến động lãi suất vay theo thời gian.')
    st.subheader('9.1. Kết quả chính')
    c1,c2,c3,c4=st.columns(4);c1.metric('Lợi suất tích lũy',_fmt_pct(st.session_state['portfolio_performance']['Cumulative Return']));c2.metric('Lợi suất quy đổi theo năm',_fmt_pct(p['annual_return']));c3.metric('Sharpe Ratio',_fmt_ratio(p['sharpe']));c4.metric('Maximum Drawdown',_fmt_pct(p['max_drawdown']))

    st.subheader('9.2. Đánh giá đa chiều')
    c1,c2,c3,c4=st.columns(4);c1.metric('Sortino Ratio',_fmt_ratio(p['sortino']));c2.metric('Information Ratio',_fmt_ratio(p['information_ratio']));c3.metric('Jensen Alpha',_fmt_pct(p['jensen_alpha']));c4.metric('Tracking Error',_fmt_pct(p['tracking_error']))
    with st.expander('Chỉ tiêu chuyên sâu',expanded=False):
        c1,c2,c3,c4=st.columns(4);c1.metric('Beta VNINDEX',_fmt_ratio(p['beta']));c2.metric('Treynor Ratio',_fmt_ratio(p['treynor']));c3.metric('M²',_fmt_pct(p['m2']));c4.metric('R² với VNINDEX',_fmt_pct(p['r_squared']))
        st.caption('Sharpe cho biết lợi suất vượt lãi suất phi rủi ro so với mức biến động. Sortino tập trung hơn vào rủi ro giảm giá. Information Ratio cho biết mức lợi nhuận vượt VNINDEX có tương xứng với mức chênh lệch biến động hay không. Jensen Alpha cho biết phần lợi suất vượt mức giải thích bởi beta trong mô hình CAPM. Treynor tập trung vào rủi ro thị trường. Không nên dùng riêng một chỉ tiêu để kết luận danh mục tốt hay xấu.')

    if benchmark_returns is not None:
        st.subheader('9.3. So sánh với VNINDEX')
        rows=[[label,p['annual_return'],p['annual_volatility'],p['sharpe'],p['max_drawdown']],['VNINDEX',b['annual_return'],b['annual_volatility'],b['sharpe'],b['max_drawdown']]]
        table=pd.DataFrame(rows,columns=['Đối tượng','Lợi suất quy đổi theo năm','Biến động quy đổi theo năm','Sharpe Ratio','Maximum Drawdown'])
        for col in ['Lợi suất quy đổi theo năm','Biến động quy đổi theo năm','Maximum Drawdown']:table[col]=table[col].map(_fmt_pct)
        table['Sharpe Ratio']=table['Sharpe Ratio'].map(_fmt_ratio);st.dataframe(table,use_container_width=True,hide_index=True)
        c1,c2,c3=st.columns(3);c1.metric('Lợi suất chủ động',_fmt_pct(p['active_return']));c2.metric('Tracking Error',_fmt_pct(p['tracking_error']));c3.metric('T thống kê lợi suất chủ động',_fmt_ratio(p['active_t_stat']))
        st.caption('Lợi suất chủ động được tính so với VNINDEX. Information Ratio và t thống kê giúp đánh giá chất lượng của phần lợi suất vượt benchmark, thay vì chỉ nhìn chênh lệch lợi suất.')

    st.subheader('9.4. Đọc kết quả')
    if np.isfinite(p['sharpe']):
        if p['sharpe']<0: st.warning(f'Sharpe Ratio = {p["sharpe"]:.2f}. Trong giai đoạn đánh giá, danh mục chưa tạo được lợi suất đủ để bù lãi suất phi rủi ro trên mức biến động đã chịu.')
        elif p['sharpe']<0.5: st.warning(f'Sharpe Ratio = {p["sharpe"]:.2f}. Danh mục có lợi suất vượt lãi suất phi rủi ro, nhưng mức lợi suất này chưa lớn so với biến động đã chịu. Nên xem thêm Sortino, Maximum Drawdown và kết quả so với VNINDEX.')
        else: st.write(f'Sharpe Ratio = {p["sharpe"]:.2f}. Danh mục có hiệu quả tương đối tốt trên mỗi đơn vị biến động trong giai đoạn đánh giá. Tuy nhiên, Sharpe cao không đồng nghĩa với rủi ro thấp hoặc lợi nhuận tương lai chắc chắn.')
    if np.isfinite(p['information_ratio']):st.write(f'Information Ratio = {p["information_ratio"]:.2f}. Chỉ tiêu này cho biết phần lợi nhuận vượt VNINDEX đạt được có tương xứng với mức chênh lệch biến động so với VNINDEX hay không.')
    if np.isfinite(p['jensen_alpha']):st.write(f'Jensen Alpha = {p["jensen_alpha"]:.2%}/năm. Theo mô hình CAPM, danh mục tạo ra mức lợi suất cao hơn phần được giải thích bởi rủi ro thị trường. Kết quả này phụ thuộc vào VNINDEX và các giả định của mô hình, nên không nên hiểu là lợi nhuận chắc chắn.')
    st.info('Kết quả lịch sử nên được xem trong bối cảnh so sánh với các phương án khác, VNINDEX và mức rủi ro mà bạn chấp nhận. Kết quả còn chịu ảnh hưởng bởi giai đoạn dữ liệu, benchmark, chi phí giao dịch và sai số ước lượng.')
