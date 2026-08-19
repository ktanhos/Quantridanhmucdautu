import pandas as pd
import streamlit as st
from portfolio_recommendation import build_recommendation

def render_recommendation(returns,optimization_result,regime_result,policy):
    st.header('Bước 8. So sánh và đề xuất phân bổ')
    st.caption('Chuyển kết quả tối ưu hóa thành phân bổ mục tiêu theo Market Regime. Đây là kết quả mô hình, không tự động đặt lệnh.')
    if not optimization_result or regime_result is None:return
    selected=st.selectbox('Danh mục mô hình làm cơ sở',['Optimal Risky','Minimum Variance','Maximum Return'])
    weights=optimization_result['weights'][selected]
    current=pd.Series({c:1/len(returns.columns) for c in returns.columns})
    equity_min=float(getattr(regime_result,'equity_min',.5));equity_max=float(getattr(regime_result,'equity_max',.7));regime=str(getattr(regime_result,'regime','Trung tính'))
    rec=build_recommendation(current,weights,regime,equity_min,equity_max)
    st.subheader('8.1. Phân bổ mục tiêu')
    c1,c2,c3=st.columns(3);c1.metric('Market Regime',regime);c2.metric('Tỷ trọng cổ phiếu',f'{rec["target_equity_weights"].sum():.1%}');c3.metric('Tài sản phòng thủ',f'{rec["defensive_weight"]:.1%}')
    table=rec['comparison'].copy();table['Tỷ trọng hiện tại']=table['Tỷ trọng hiện tại'].map(lambda x:f'{x:.2%}');table['Tỷ trọng mục tiêu']=table['Tỷ trọng mục tiêu'].map(lambda x:f'{x:.2%}');table['Thay đổi tỷ trọng']=table['Thay đổi tỷ trọng'].map(lambda x:f'{x:+.2%}');st.dataframe(table,use_container_width=True)
    st.subheader('8.2. Diễn giải thay đổi')
    changes=rec['comparison'];increase=changes[changes['Thay đổi tỷ trọng']>0].head(5);decrease=changes[changes['Thay đổi tỷ trọng']<0].tail(5)
    if not increase.empty:st.write('Ưu tiên tăng tỷ trọng:',', '.join(increase.index.tolist()))
    if not decrease.empty:st.write('Ưu tiên giảm tỷ trọng:',', '.join(decrease.index.tolist()))
    st.caption('Tỷ trọng hiện tại đang dùng phân bổ đều làm mốc vì ứng dụng chưa có dữ liệu tài sản thực tế của nhà đầu tư.')
