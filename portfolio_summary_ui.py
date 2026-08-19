import streamlit as st
from portfolio_summary import build_summary

def render_portfolio_summary(performance,regime_result,rebalance_table,target_equity=None):
    st.header('Bước 11. Tổng kết danh mục')
    if performance is None:
        st.info('Chưa có đủ dữ liệu để tổng kết danh mục.');return
    needed=bool(rebalance_table is not None and 'Cần tái cân bằng' in rebalance_table and rebalance_table['Cần tái cân bằng'].any());s=build_summary(performance,regime_result,needed,target_equity)
    c1,c2,c3,c4=st.columns(4);c1.metric('Market Regime',getattr(regime_result,'regime','Trung tính') if regime_result else 'Trung tính');c2.metric('Lợi suất năm hóa','N/A' if s['cagr'] is None else f'{s["cagr"]:.2%}');c3.metric('Sharpe Ratio','N/A' if s['sharpe'] is None else f'{s["sharpe"]:.2f}');c4.metric('Maximum Drawdown','N/A' if s['drawdown'] is None else f'{s["drawdown"]:.2%}')
    st.subheader('11.1. Đánh giá tổng thể');st.write(s['regime_text']);st.write(s['sharpe_text']);st.write(s['drawdown_text']);st.write(s['rebalance_text'])
    if target_equity is not None:st.metric('Tỷ trọng cổ phiếu mục tiêu',f'{target_equity:.1%}')
    st.subheader('11.2. Kết luận');st.info('Danh mục đang có độ lệch vượt ngưỡng tái cân bằng đã đặt. Nên xem xét điều chỉnh tỷ trọng về gần danh mục mục tiêu.' if needed else 'Danh mục hiện tại đang nằm trong ngưỡng tái cân bằng đã đặt. Chưa có tín hiệu bắt buộc phải điều chỉnh tỷ trọng.')
