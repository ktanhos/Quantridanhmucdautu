from __future__ import annotations
import pandas as pd
import streamlit as st
from market_regime import calculate_market_regime


def render_market_regime(index_prices: pd.Series, stock_prices: pd.DataFrame | None = None, volume_data: pd.DataFrame | None = None) -> None:
    st.subheader('3.1. Tình trạng thị trường hiện tại')
    st.markdown('<div class="section-note">Hệ thống nhìn xu hướng, mức tăng giảm, biến động và thanh khoản của VNINDEX để xác định thị trường đang thuận lợi, trung tính hay cần thận trọng. Đây là tín hiệu điều chỉnh tỷ trọng, không phải dự báo chắc chắn.</div>',unsafe_allow_html=True)
    try: result=calculate_market_regime(index_prices,None,volume_data)
    except ValueError as exc: st.warning(str(exc));return
    st.session_state['regime_result']=result
    c1,c2,c3,c4=st.columns(4);c1.metric('Điểm thị trường',f'{result.score:.1f}/100');c2.metric('Trạng thái',result.regime);c3.metric('Độ đồng thuận tín hiệu',result.confidence);c4.metric('Khung cổ phiếu theo thị trường',f'{result.equity_min:.0%} đến {result.equity_max:.0%}')
    st.caption('Độ đồng thuận tín hiệu cho biết các nhóm chỉ báo đang cùng hướng đến trạng thái hiện tại ở mức nào. Đây không phải xác suất thị trường sẽ tăng.')
    with st.expander('Vì sao hệ thống đưa ra kết luận này?',expanded=True):
        display=result.components.copy();display['Điểm']=display['Điểm'].round(1);display['Trọng số']=display['Trọng số'].map(lambda x:f'{x:.0%}');display['Đóng góp']=display['Đóng góp'].round(1);st.dataframe(display,use_container_width=True,hide_index=True)
    with st.expander('Xem các chỉ báo chi tiết',expanded=False):
        rows=[]
        for name,value in result.indicators.items():
            if name.startswith('%'): text='N/A' if pd.isna(value) else f'{value:.1f}%'
            elif 'Return' in name or 'Drawdown' in name or 'change' in name or 'Volatility' in name:text='N/A' if pd.isna(value) else f'{value:.2%}'
            else:text='N/A' if pd.isna(value) else f'{value:.3f}'
            rows.append({'Chỉ báo':name,'Giá trị':text})
        st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
    with st.expander('Cách quy đổi điểm thành trạng thái',expanded=False):
        thresholds=pd.DataFrame([['80 đến 100','Tích cực mạnh','90% đến 100%'],['65 đến dưới 80','Tích cực','70% đến 90%'],['45 đến dưới 65','Trung tính','50% đến 70%'],['25 đến dưới 45','Phòng thủ','20% đến 50%'],['0 đến dưới 25','Rủi ro cao','0% đến 20%']],columns=['Điểm thị trường','Trạng thái','Khung cổ phiếu tham chiếu']);st.dataframe(thresholds,use_container_width=True,hide_index=True)
    st.info(f'Kết luận hiện tại: {result.regime}. Khung cổ phiếu theo riêng tín hiệu thị trường là {result.equity_min:.0%} đến {result.equity_max:.0%}; ứng dụng vẫn kiểm tra giới hạn rủi ro của bạn trước khi áp dụng.')
