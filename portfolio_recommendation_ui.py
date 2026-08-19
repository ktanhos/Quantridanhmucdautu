import pandas as pd
import streamlit as st
from portfolio_recommendation import build_recommendation

SCENARIOS=['Phân bổ tham chiếu','Minimum Variance','Optimal Risky','Maximum Return']

def _choose_best(summary, policy):
    s=summary.copy();target=float(policy.get('target_return',0));capacity=float(policy.get('risk_capacity',50));risk_limit=0.15+0.25*capacity/100
    feasible=s[(s['Lợi suất kỳ vọng']>=target)&(s['Độ biến động']<=risk_limit)]
    if not feasible.empty:return feasible['Sharpe Ratio'].idxmax(),'Đạt cả mục tiêu lợi nhuận và giới hạn rủi ro.'
    target_ok=s[s['Lợi suất kỳ vọng']>=target]
    if not target_ok.empty:return target_ok['Sharpe Ratio'].idxmax(),'Không có phương án nào đồng thời đạt giới hạn rủi ro; chọn phương án đạt mục tiêu với Sharpe cao nhất.'
    return s['Sharpe Ratio'].idxmax(),'Không phương án nào đạt mục tiêu lợi nhuận; ưu tiên phương án có hiệu quả điều chỉnh theo rủi ro tốt nhất.'

def _diagnose_target_gap(optimization_result,best,policy):
    target=float(policy.get('target_return',0))
    summary=optimization_result['summary'];expected=float(summary.loc[best,'Lợi suất kỳ vọng'])
    mu=pd.Series(optimization_result.get('expected_returns',pd.Series(dtype=float)),dtype=float)
    weights=pd.Series(optimization_result['weights'][best],dtype=float).reindex(mu.index).fillna(0)
    stock=pd.DataFrame({'Tỷ trọng':weights,'Lợi suất kỳ vọng':mu,'Đóng góp vào lợi suất':weights*mu,'Ảnh hưởng so với mục tiêu':weights*(mu-target)})
    return expected,target,stock[stock['Tỷ trọng']>1e-8].sort_values('Ảnh hưởng so với mục tiêu')

def render_recommendation(returns,optimization_result,regime_result,policy):
    st.header('Bước 8. So sánh và đề xuất phân bổ')
    st.caption('Đây là bước guiding: hệ thống so sánh các phương án mô hình, chọn phương án phù hợp nhất với hồ sơ, sau đó chuyển thành tỷ trọng mục tiêu. Người dùng không cần nhập trước danh mục.')
    if not optimization_result or regime_result is None:return
    summary=optimization_result['summary'];best,reason=_choose_best(summary,policy)
    if best not in SCENARIOS:best='Optimal Risky'
    equity_min=float(getattr(regime_result,'equity_min',.5));equity_max=float(getattr(regime_result,'equity_max',.7));regime=str(getattr(regime_result,'regime','Trung tính'))
    zero_current=pd.Series(0.,index=returns.columns);rec_best=build_recommendation(zero_current,optimization_result['weights'][best],regime,equity_min,equity_max)
    st.subheader('8.1. Phương án phù hợp nhất với hồ sơ')
    c1,c2,c3=st.columns(3);c1.metric('Phương án đề xuất',best);c2.metric('Market Regime',regime);c3.metric('Tỷ trọng cổ phiếu đề xuất',f'{rec_best["target_equity_weights"].sum():.1%}')
    st.info(reason)
    st.caption('Phương án được chọn theo mục tiêu lợi nhuận, giới hạn rủi ro suy ra từ khả năng chịu rủi ro và Sharpe Ratio. Đây là tiêu chí định hướng của ứng dụng, không phải bảo đảm lợi nhuận.')
    st.subheader('8.2. Các phương án để nhà đầu tư so sánh')
    comparison=summary.copy();comparison['Đạt mục tiêu']=comparison['Lợi suất kỳ vọng']>=float(policy.get('target_return',0));comparison['Phù hợp rủi ro']=comparison['Độ biến động']<=(0.15+0.25*float(policy.get('risk_capacity',50))/100);comparison['Lợi suất kỳ vọng']=comparison['Lợi suất kỳ vọng'].map(lambda x:f'{x:.2%}');comparison['Độ biến động']=comparison['Độ biến động'].map(lambda x:f'{x:.2%}');comparison['Sharpe Ratio']=comparison['Sharpe Ratio'].map(lambda x:f'{x:.2f}');st.dataframe(comparison,use_container_width=True)
    st.subheader('8.3. Phân bổ mục tiêu của phương án đề xuất')
    c1,c2,c3=st.columns(3);c1.metric('Cổ phiếu',f'{rec_best["target_equity_weights"].sum():.1%}');c2.metric('Tài sản phòng thủ',f'{rec_best["defensive_weight"]:.1%}');c3.metric('Vốn đầu tư',f'{float(st.session_state.get("investment_capital",0)):,.0f} VNĐ')
    table=rec_best['target_equity_weights'].sort_values(ascending=False).rename('Tỷ trọng mục tiêu').to_frame();table=table[table['Tỷ trọng mục tiêu']>1e-6];table['Số tiền dự kiến']=table['Tỷ trọng mục tiêu']*float(st.session_state.get('investment_capital',0));table['Tỷ trọng mục tiêu']=table['Tỷ trọng mục tiêu'].map(lambda x:f'{x:.2%}');table['Số tiền dự kiến']=table['Số tiền dự kiến'].map(lambda x:f'{x:,.0f} VNĐ');st.dataframe(table,use_container_width=True)
    defensive_value=rec_best['defensive_weight']*float(st.session_state.get('investment_capital',0));st.caption(f'Tài sản phòng thủ dự kiến: {defensive_value:,.0f} VNĐ. Tỷ trọng phòng thủ phụ thuộc Market Regime và được dùng để giảm mức phơi nhiễm cổ phiếu khi thị trường không thuận lợi.')
    st.subheader('8.4. Vì sao phương án này chưa đạt mục tiêu?')
    expected,target,stock=_diagnose_target_gap(optimization_result,best,policy);gap=expected-target
    if expected<target:
        st.warning(f'Danh mục {best} có lợi suất kỳ vọng {expected:.2%}, thấp hơn mục tiêu {target:.2%}, chênh {abs(gap):.2%}. Hệ thống kiểm tra tiếp xem mức thiếu hụt đến từ một vài mã hay từ toàn bộ tập cổ phiếu.')
        negative=stock[stock['Ảnh hưởng so với mục tiêu']<0].copy()
        if not negative.empty:
            view=negative.copy();view['Tỷ trọng']=view['Tỷ trọng'].map(lambda x:f'{x:.2%}');view['Lợi suất kỳ vọng']=view['Lợi suất kỳ vọng'].map(lambda x:f'{x:.2%}');view['Đóng góp vào lợi suất']=view['Đóng góp vào lợi suất'].map(lambda x:f'{x:.2%}');view['Ảnh hưởng so với mục tiêu']=view['Ảnh hưởng so với mục tiêu'].map(lambda x:f'{x:.2%}');st.dataframe(view,use_container_width=True);st.caption('Ảnh hưởng so với mục tiêu = tỷ trọng × lợi suất kỳ vọng của mã trừ phần lợi suất mục tiêu tương ứng. Giá trị âm cho biết mã đó đang kéo lợi suất kỳ vọng của danh mục xuống so với mục tiêu.')
        max_mu=float(stock['Lợi suất kỳ vọng'].max()) if not stock.empty else float('nan')
        if pd.notna(max_mu) and max_mu<target:
            st.error(f'Toàn bộ các mã trong tập hiện tại đều có lợi suất kỳ vọng thấp hơn mục tiêu {target:.2%}. Đây là vấn đề của toàn bộ tập cổ phiếu, không phải một mã riêng lẻ. Nên mở rộng tập cổ phiếu hoặc xem lại mục tiêu.')
        elif len(negative)>1:
            st.info('Có nhiều mã cùng tạo ảnh hưởng âm. Việc chỉ thay một mã khó giải quyết toàn bộ mức thiếu hụt; nên đánh giá lại cả tập cổ phiếu.')
        elif len(negative)==1:
            st.info('Mức thiếu hụt tập trung chủ yếu ở một mã. Có thể kiểm tra mã này trước khi thay đổi toàn bộ tập cổ phiếu.')
    else:
        st.success(f'Danh mục {best} có lợi suất kỳ vọng {expected:.2%}, đạt mục tiêu {target:.2%}.')
        below=stock[stock['Lợi suất kỳ vọng']<target]
        if not below.empty:st.info(f'{len(below)} mã có lợi suất kỳ vọng thấp hơn mục tiêu nhưng các mã còn lại bù đắp đủ để toàn danh mục đạt mục tiêu.')
        else:st.info('Không có mã riêng lẻ nào có lợi suất kỳ vọng thấp hơn mục tiêu. Danh mục đạt mục tiêu trên cơ sở dữ liệu đang sử dụng.')
    st.subheader('8.5. Có nên mở rộng tập cổ phiếu không?')
    requested_max=float(optimization_result.get('requested_max_weight',policy.get('max_single_stock_weight',.10)));universe_size=int(optimization_result.get('universe_size',len(returns.columns)));required=int(__import__('math').ceil(1/requested_max)) if requested_max>0 else universe_size;effective_max=float(optimization_result.get('effective_max_weight',1/universe_size if universe_size else 1));max_w=float(rec_best['target_equity_weights'].max())
    if universe_size<required:st.warning(f'Tập hiện tại có {universe_size} mã trong khi giới hạn hồ sơ là {requested_max:.0%}/mã. Muốn giữ giới hạn này mà vẫn phân bổ đủ 100% cổ phiếu, cần ít nhất {required} mã. Nên mở rộng tập cổ phiếu.')
    elif max_w>requested_max+.001:st.warning('Một số tỷ trọng mục tiêu cao hơn giới hạn hồ sơ sau điều chỉnh Market Regime. Nên kiểm tra lại giới hạn trước khi sử dụng kết quả.')
    else:st.success('Tập cổ phiếu hiện tại đủ rộng để áp dụng giới hạn tỷ trọng theo hồ sơ. Không có cơ sở chỉ từ một mã có lợi suất cao để kết luận phải thay mã khác.')
    st.caption('Khuyến nghị chọn cổ phiếu được hiểu là lựa chọn trong tập dữ liệu đầu vào dựa trên lợi suất kỳ vọng, biến động và tương quan. Ứng dụng không kết luận một mã chắc chắn sẽ tăng giá.')
    st.session_state['target_equity']=rec_best['target_equity_weights'];st.session_state['recommended_portfolio']=best;st.session_state['recommendation_result']=rec_best
