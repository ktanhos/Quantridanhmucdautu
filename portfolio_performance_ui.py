import numpy as np
import pandas as pd
import streamlit as st
from portfolio_risk import calculate_portfolio_risk

def _fmt_pct(x):return 'N/A' if pd.isna(x) else f'{x:.2%}'
def _fmt_ratio(x):return 'N/A' if pd.isna(x) or not np.isfinite(x) else f'{x:.2f}'
def _portfolio_weights(current_weights,columns):
    if current_weights is None or np.isscalar(current_weights):return None
    try:
        w=pd.Series(current_weights,dtype=float).reindex(columns).fillna(0);return w if w.sum()>0 else None
    except Exception:return None

def render_portfolio_performance(returns,benchmark_returns=None,current_weights=None,risk_free_rate=0.0):
    st.subheader('7.1. Đánh giá hiệu quả lịch sử')
    st.markdown('<div class="section-note">Đây là nhìn lại dữ liệu quá khứ: danh mục đã tăng giảm ra sao, phải chịu mức rủi ro nào và kết quả so với VNINDEX như thế nào. Kết quả không phải dự báo tương lai.</div>',unsafe_allow_html=True)
    leverage=st.session_state.get('complete_portfolio_result') or {};borrowed=float(leverage.get('borrowed_weight',0));margin_rate=float(leverage.get('margin_rate',0));leveraged=borrowed>1e-10
    w=_portfolio_weights(current_weights,returns.columns) or _portfolio_weights(leverage.get('complete_equity_weights'),returns.columns)
    if w is not None:
        if leveraged:portfolio=returns.mul(w,axis=1).sum(axis=1)-borrowed*margin_rate/252;label='Danh mục đề xuất có sử dụng tiền vay'
        else:w=w/w.sum();portfolio=returns.mul(w,axis=1).sum(axis=1);label='Danh mục đề xuất'
    else:w=pd.Series(1/len(returns.columns),index=returns.columns);portfolio=returns.mul(w,axis=1).sum(axis=1);label='Tập cổ phiếu chia đều'
    portfolio=portfolio.replace([np.inf,-np.inf],np.nan).dropna();p=calculate_portfolio_risk(pd.DataFrame({'Portfolio':portfolio}),pd.Series({'Portfolio':1.0}),benchmark_returns,risk_free_rate);b=calculate_portfolio_risk(pd.DataFrame({'VNINDEX':benchmark_returns}),pd.Series({'VNINDEX':1.0}),None,risk_free_rate) if benchmark_returns is not None else None
    st.session_state['portfolio_performance']={'Cumulative Return':float((1+p['portfolio_returns']).prod()-1),'Annualized Return':p['annual_return'],'Annualized Volatility':p['annual_volatility'],'Sharpe Ratio':p['sharpe'],'Maximum Drawdown':p['max_drawdown']}
    if leveraged:st.warning(f'Kết quả đã trừ chi phí vay giả định {margin_rate:.2%}/năm trên phần vốn vay {borrowed:.1%}.')
    st.subheader('Kết quả chính');c1,c2,c3,c4=st.columns(4);c1.metric('Lợi suất tích lũy',_fmt_pct(st.session_state['portfolio_performance']['Cumulative Return']));c2.metric('Lợi suất quy đổi năm',_fmt_pct(p['annual_return']));c3.metric('Hiệu quả trên mức biến động',_fmt_ratio(p['sharpe']));c4.metric('Mức giảm lớn nhất',_fmt_pct(p['max_drawdown']))
    st.subheader('Nhìn danh mục từ nhiều góc độ');c1,c2,c3,c4=st.columns(4);c1.metric('Hiệu quả khi chỉ tính giai đoạn giảm',_fmt_ratio(p['sortino']));c2.metric('Chất lượng phần kết quả khác VNINDEX',_fmt_ratio(p['information_ratio']));c3.metric('Phần kết quả vượt mô hình thị trường',_fmt_pct(p['jensen_alpha']));c4.metric('Mức khác biệt so với VNINDEX',_fmt_pct(p['tracking_error']))
    with st.expander('Các chỉ tiêu này nói gì?',expanded=False):st.markdown('**Sharpe**: lợi nhuận có tương xứng với mức lên xuống đã chịu không.\n\n**Sortino**: chú ý nhiều hơn đến các giai đoạn giảm.\n\n**Information Ratio**: kết quả khác VNINDEX có đáng với mức khác biệt đã chấp nhận không.\n\n**Jensen Alpha**: phần kết quả còn lại sau khi đã tính đến mức danh mục thường đi cùng thị trường.\n\n**Treynor**: lợi nhuận so với phần rủi ro đến từ biến động chung của thị trường. Không chỉ tiêu nào một mình quyết định danh mục tốt hay xấu.')
    if benchmark_returns is not None:
        st.subheader('So sánh với VNINDEX');table=pd.DataFrame([[label,p['annual_return'],p['annual_volatility'],p['sharpe'],p['max_drawdown']],['VNINDEX',b['annual_return'],b['annual_volatility'],b['sharpe'],b['max_drawdown']]],columns=['Đối tượng','Lợi suất quy đổi năm','Biến động quy đổi năm','Hiệu quả trên biến động','Mức giảm lớn nhất'])
        for col in ['Lợi suất quy đổi năm','Biến động quy đổi năm','Mức giảm lớn nhất']:table[col]=table[col].map(_fmt_pct)
        table['Hiệu quả trên biến động']=table['Hiệu quả trên biến động'].map(_fmt_ratio);st.dataframe(table,use_container_width=True,hide_index=True)
    st.caption('Hãy nhìn đồng thời lợi suất, mức giảm lớn nhất và kết quả so với VNINDEX. Lợi nhuận cao nhưng mức giảm quá sâu vẫn có thể không phù hợp với bạn.')
