import pandas as pd
import streamlit as st
from portfolio_recommendation import build_recommendation

def _choose_best(summary, policy):
    s=summary.copy();target=float(policy.get('target_return',0));capacity=float(policy.get('risk_capacity',50));risk_limit=0.15+0.25*capacity/100
    feasible=s[(s['Lợi suất kỳ vọng']>=target)&(s['Độ biến động']<=risk_limit)]
    if not feasible.empty:return feasible['Sharpe Ratio'].idxmax(),'Đạt cả mục tiêu lợi nhuận và giới hạn rủi ro.'
    target_ok=s[s['Lợi suất kỳ vọng']>=target]
    if not target_ok.empty:return target_ok['Sharpe Ratio'].idxmax(),'Không có phương án nào đồng thời đạt giới hạn rủi ro; chọn phương án đạt mục tiêu với Sharpe cao nhất.'
    return s['Sharpe Ratio'].idxmax(),'Không phương án nào đạt mục tiêu lợi nhuận; ưu tiên phương án có hiệu quả điều chỉnh theo rủi ro tốt nhất.'

def render_recommendation(returns,optimization_result,regime_result,policy):
    st.header('Bước 8. So sánh và đề xuất phân bổ')
    st.caption('Đây là bước guiding: hệ thống so sánh các phương án mô hình, chọn phương án phù hợp nhất với hồ sơ, sau đó chuyển thành tỷ trọng mục tiêu. Người dùng không cần nhập trước danh mục.')
    if not optimization_result or regime_result is None:return
    summary=optimization_result['summary'];best,reason=_choose_best(summary,policy)
    selected=st.selectbox('Phương án muốn xem chi tiết',['Minimum Variance','Optimal Risky','Maximum Return'],index=['Minimum Variance','Optimal Risky','Maximum Return'].index(best),key='recommendation_portfolio')
    weights=optimization_result['weights'][selected]
    equity_min=float(getattr(regime_result,'equity_min',.5));equity_max=float(getattr(regime_result,'equity_max',.7));regime=str(getattr(regime_result,'regime','Trung tính'))
    zero_current=pd.Series(0.,index=returns.columns)
    rec=build_recommendation(zero_current,weights,regime,equity_min,equity_max)
    st.subheader('8.1. Phương án phù hợp nhất với hồ sơ')
    c1,c2,c3=st.columns(3);c1.metric('Phương án đề xuất',best);c2.metric('Market Regime',regime);c3.metric('Tỷ trọng cổ phiếu đề xuất',f'{rec["target_equity_weights"].sum():.1%}')
    st.info(reason)
    st.caption('Phương án được chọn theo mục tiêu lợi nhuận, giới hạn rủi ro suy ra từ khả năng chịu rủi ro và Sharpe Ratio. Đây là tiêu chí định hướng của ứng dụng, không phải bảo đảm lợi nhuận.')
    st.subheader('8.2. Các phương án để nhà đầu tư so sánh')
    comparison=summary.copy();comparison['Đạt mục tiêu']=comparison['Lợi suất kỳ vọng']>=float(policy.get('target_return',0));comparison['Phù hợp rủi ro']=comparison['Độ biến động']<=(0.15+0.25*float(policy.get('risk_capacity',50))/100);comparison['Lợi suất kỳ vọng']=comparison['Lợi suất kỳ vọng'].map(lambda x:f'{x:.2%}');comparison['Độ biến động']=comparison['Độ biến động'].map(lambda x:f'{x:.2%}');comparison['Sharpe Ratio']=comparison['Sharpe Ratio'].map(lambda x:f'{x:.2f}');st.dataframe(comparison,use_container_width=True)
    st.subheader('8.3. Phân bổ mục tiêu')
    c1,c2,c3=st.columns(3);c1.metric('Cổ phiếu',f'{rec["target_equity_weights"].sum():.1%}');c2.metric('Tài sản phòng thủ',f'{rec["defensive_weight"]:.1%}');c3.metric('Vốn đầu tư',f'{float(st.session_state.get("investment_capital",0)):,.0f} VNĐ')
    table=rec['target_equity_weights'].sort_values(ascending=False).rename('Tỷ trọng mục tiêu').to_frame();table=table[table['Tỷ trọng mục tiêu']>1e-6];table['Số tiền dự kiến']=table['Tỷ trọng mục tiêu']*float(st.session_state.get('investment_capital',0));table['Tỷ trọng mục tiêu']=table['Tỷ trọng mục tiêu'].map(lambda x:f'{x:.2%}');table['Số tiền dự kiến']=table['Số tiền dự kiến'].map(lambda x:f'{x:,.0f} VNĐ');st.dataframe(table,use_container_width=True)
    defensive_value=rec['defensive_weight']*float(st.session_state.get('investment_capital',0))
    st.caption(f'Tài sản phòng thủ dự kiến: {defensive_value:,.0f} VNĐ. Tỷ trọng phòng thủ phụ thuộc Market Regime và được dùng để giảm mức phơi nhiễm cổ phiếu khi thị trường không thuận lợi.')
    st.subheader('8.4. Có nên chọn cổ phiếu khác không?')
    active=table.index.tolist();max_w=float(rec['target_equity_weights'].max());n=len(active)
    if n<5:st.warning(f'Mô hình hiện chỉ phân bổ vào {n} mã. Nếu mục tiêu là đa dạng hóa tốt hơn, nên mở rộng tập cổ phiếu đầu vào thay vì tự ý thêm mã chỉ vì một mã có lợi suất cao.')
    elif max_w>float(policy.get('max_single_stock_weight',.10))+.001:st.warning('Một số tỷ trọng đang cao hơn giới hạn hồ sơ. Cần kiểm tra lại giới hạn tỷ trọng hoặc mở rộng tập cổ phiếu để có thêm lựa chọn.')
    else:st.success('Tập cổ phiếu hiện tại đủ lựa chọn theo giới hạn tỷ trọng đang đặt ra. Chưa có cơ sở chỉ vì một mã có lợi suất cao mà thay thế bằng mã khác.')
    st.caption('Khuyến nghị chọn cổ phiếu được hiểu là lựa chọn trong tập dữ liệu đầu vào dựa trên đặc điểm lợi suất, biến động và tương quan. Ứng dụng không kết luận một mã chắc chắn sẽ tăng giá.')
    st.session_state['target_equity']=rec['target_equity_weights'];st.session_state['recommended_portfolio']=best;st.session_state['recommendation_result']=rec
