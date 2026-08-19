import pandas as pd
import streamlit as st
from portfolio_recommendation import build_recommendation

SCENARIOS=['Phân bổ tham chiếu','Minimum Variance','Optimal Risky','Maximum Return']


def _choose_best(summary, policy):
    s=summary.copy()
    target=float(policy.get('target_return',0))
    capacity=float(policy.get('risk_capacity',50))
    risk_limit=0.15+0.25*capacity/100
    feasible=s[(s['Lợi suất kỳ vọng']>=target)&(s['Độ biến động']<=risk_limit)]
    if not feasible.empty:
        return feasible['Sharpe Ratio'].idxmax(),'Đạt cả mục tiêu lợi nhuận và giới hạn rủi ro.','Đề xuất'
    target_ok=s[s['Lợi suất kỳ vọng']>=target]
    if not target_ok.empty:
        best=target_ok['Sharpe Ratio'].idxmax()
        return best,'Có thể đạt mục tiêu lợi nhuận nhưng phải chấp nhận mức rủi ro cao hơn giới hạn hồ sơ. Đây là phương án đánh đổi, không phải phương án hoàn toàn phù hợp.','Đánh đổi'
    return None,'Không phương án nào đạt mục tiêu lợi nhuận với tập cổ phiếu hiện tại.','Không có phương án phù hợp'


def _diagnose_target_gap(optimization_result,best,policy):
    target=float(policy.get('target_return',0))
    summary=optimization_result['summary']
    expected=float(summary.loc[best,'Lợi suất kỳ vọng'])
    mu=pd.Series(optimization_result.get('expected_returns',pd.Series(dtype=float)),dtype=float)
    weights=pd.Series(optimization_result['weights'][best],dtype=float).reindex(mu.index).fillna(0)
    stock=pd.DataFrame({'Tỷ trọng':weights,'Lợi suất kỳ vọng':mu,'Đóng góp vào lợi suất':weights*mu,'Ảnh hưởng so với mục tiêu':weights*(mu-target)})
    return expected,target,stock[stock['Tỷ trọng']>1e-8].sort_values('Ảnh hưởng so với mục tiêu')


def _render_invalid_constraints(optimization_result,policy):
    requested=float(optimization_result.get('requested_max_weight',policy.get('max_single_stock_weight',.20)))
    n=int(optimization_result.get('universe_size',0))
    required=int(optimization_result.get('required_assets',__import__('math').ceil(1/requested))) if requested>0 else n
    st.subheader('8.1. Chưa có phương án hợp lệ')
    c1,c2,c3=st.columns(3)
    c1.metric('Số mã hiện có',f'{n}')
    c2.metric('Giới hạn mỗi mã',f'{requested:.0%}')
    c3.metric('Số mã tối thiểu',f'{required}')
    st.warning(f'Với {n} mã và giới hạn {requested:.0%} cho mỗi mã, tổng tỷ trọng tối đa chỉ là {n*requested:.0%}. Vì vậy chưa thể tạo danh mục 100% cổ phiếu mà vẫn tuân thủ đúng hồ sơ.')
    st.markdown('**Có ba hướng xử lý:**')
    st.write(f'1. Bổ sung ít nhất {max(0,required-n)} mã để có đủ không gian phân bổ.')
    st.write(f'2. Nếu chỉ muốn giữ {n} mã, có thể tăng giới hạn tối đa lên ít nhất {1/n:.0%} mỗi mã.')
    st.write('3. Nếu mục tiêu lợi nhuận hiện tại quá cao so với tập cổ phiếu, có thể giảm mục tiêu hoặc mở rộng tập cổ phiếu để hệ thống có thêm lựa chọn.')
    st.caption('Việc có 4 hoặc 5 mã không tự động có nghĩa là danh mục xấu. Vấn đề ở đây chỉ là giới hạn tỷ trọng hiện tại có đủ không gian để phân bổ 100% hay không.')


def render_recommendation(returns,optimization_result,regime_result,policy):
    st.header('Bước 8. So sánh và đề xuất phân bổ')
    st.caption('Đây là bước guiding: hệ thống so sánh các phương án mô hình, chọn phương án phù hợp nhất với hồ sơ, sau đó chuyển thành tỷ trọng mục tiêu. Người dùng không cần nhập trước danh mục.')
    if not optimization_result or regime_result is None:return

    if not optimization_result.get('constraint_feasible',True):
        _render_invalid_constraints(optimization_result,policy)
        st.subheader('8.2. Tại sao chưa thể kết luận phương án tốt nhất?')
        st.info('Các phương án ở Bước 7 chỉ là nghiệm mô hình tham khảo vì chưa thỏa giới hạn tỷ trọng trong hồ sơ. Hệ thống không chuyển chúng thành danh mục mục tiêu để tránh trường hợp một cổ phiếu vượt quá giới hạn mà vẫn bị gắn nhãn tối ưu.')
        st.subheader('8.3. Nên làm gì tiếp theo?')
        st.write('Bổ sung thêm các cổ phiếu có đặc điểm lợi suất, biến động và tương quan khác nhau. Sau đó hệ thống sẽ tính lại các phương án và kiểm tra xem mục tiêu lợi nhuận có đạt được với giới hạn rủi ro hay không.')
        st.caption('Nếu sau khi mở rộng tập cổ phiếu mà lợi suất kỳ vọng tối đa vẫn thấp hơn mục tiêu, hệ thống sẽ chỉ ra rằng mục tiêu đang cao hơn khả năng của tập dữ liệu thay vì ép một mã lên tỷ trọng quá cao.')
        return

    summary=optimization_result['summary']
    best,reason,status=_choose_best(summary,policy)
    if best is None:
        target=float(policy.get('target_return',0))
        max_expected=float(summary['Lợi suất kỳ vọng'].max())
        st.subheader('8.1. Chưa có phương án đạt mục tiêu')
        c1,c2=st.columns(2)
        c1.metric('Mục tiêu lợi nhuận',f'{target:.2%}')
        c2.metric('Lợi suất kỳ vọng cao nhất',f'{max_expected:.2%}')
        st.error(f'Tập cổ phiếu hiện tại chưa tạo được phương án có lợi suất kỳ vọng đạt {target:.2%}. Không nên gắn nhãn một phương án là tối ưu chỉ để có kết luận.')
        st.subheader('8.2. Các hướng xử lý')
        st.write('1. Mở rộng tập cổ phiếu để tìm thêm cơ hội có lợi suất kỳ vọng và tương quan khác.')
        st.write('2. Giảm mục tiêu lợi nhuận nếu mục tiêu hiện tại cao hơn khả năng của tập dữ liệu.')
        st.write('3. Nếu vẫn muốn giữ mục tiêu, có thể chấp nhận mức rủi ro cao hơn, nhưng hệ thống phải thể hiện rõ đây là đánh đổi chứ không phải phương án phù hợp hoàn toàn.')
        st.subheader('8.3. Chẩn đoán nguyên nhân')
        best_gap=summary['Lợi suất kỳ vọng'].idxmax()
        expected,target,stock=_diagnose_target_gap(optimization_result,best_gap,policy)
        negative=stock[stock['Ảnh hưởng so với mục tiêu']<0].copy()
        if not negative.empty:
            view=negative.copy()
            view['Tỷ trọng']=view['Tỷ trọng'].map(lambda x:f'{x:.2%}')
            view['Lợi suất kỳ vọng']=view['Lợi suất kỳ vọng'].map(lambda x:f'{x:.2%}')
            view['Đóng góp vào lợi suất']=view['Đóng góp vào lợi suất'].map(lambda x:f'{x:.2%}')
            view['Ảnh hưởng so với mục tiêu']=view['Ảnh hưởng so với mục tiêu'].map(lambda x:f'{x:.2%}')
            st.dataframe(view,use_container_width=True)
        st.caption('Hệ thống đang chỉ ra các mã làm lợi suất kỳ vọng thấp hơn mức mục tiêu. Đây là chẩn đoán để người dùng xem xét tập cổ phiếu, không phải tín hiệu mua bán.')
        return

    equity_min=float(getattr(regime_result,'equity_min',.5))
    equity_max=float(getattr(regime_result,'equity_max',.7))
    regime=str(getattr(regime_result,'regime','Trung tính'))
    rec_best=build_recommendation(pd.Series(0.,index=returns.columns),optimization_result['weights'][best],regime,equity_min,equity_max,max_single_stock_weight=float(policy.get('max_single_stock_weight',.20)))

    st.subheader('8.1. Phương án phù hợp nhất với hồ sơ')
    c1,c2,c3=st.columns(3)
    c1.metric('Phương án',best)
    c2.metric('Market Regime',regime)
    c3.metric('Tỷ trọng cổ phiếu đề xuất',f'{rec_best["target_equity_weights"].sum():.1%}')
    if status=='Đề xuất':
        st.success(reason)
    else:
        st.warning(reason)
    st.caption('Phương án được chọn theo mục tiêu lợi nhuận, giới hạn rủi ro suy ra từ mức chấp nhận biến động và Sharpe Ratio. Đây là tiêu chí định hướng, không phải bảo đảm lợi nhuận.')

    st.subheader('8.2. Các phương án để nhà đầu tư so sánh')
    comparison=summary.copy()
    comparison['Đạt mục tiêu']=comparison['Lợi suất kỳ vọng']>=float(policy.get('target_return',0))
    comparison['Phù hợp rủi ro']=comparison['Độ biến động']<=(0.15+0.25*float(policy.get('risk_capacity',50))/100)
    comparison['Lợi suất kỳ vọng']=comparison['Lợi suất kỳ vọng'].map(lambda x:f'{x:.2%}')
    comparison['Độ biến động']=comparison['Độ biến động'].map(lambda x:f'{x:.2%}')
    comparison['Sharpe Ratio']=comparison['Sharpe Ratio'].map(lambda x:f'{x:.2f}')
    st.dataframe(comparison,use_container_width=True)

    st.subheader('8.3. Phân bổ mục tiêu của phương án đề xuất')
    c1,c2,c3=st.columns(3)
    c1.metric('Cổ phiếu',f'{rec_best["target_equity_weights"].sum():.1%}')
    c2.metric('Tài sản phòng thủ',f'{rec_best["defensive_weight"]:.1%}')
    c3.metric('Vốn đầu tư',f'{float(st.session_state.get("investment_capital",0)):,.0f} VNĐ')
    table=rec_best['target_equity_weights'].sort_values(ascending=False).rename('Tỷ trọng mục tiêu').to_frame()
    table=table[table['Tỷ trọng mục tiêu']>1e-6]
    table['Số tiền dự kiến']=table['Tỷ trọng mục tiêu']*float(st.session_state.get('investment_capital',0))
    table['Tỷ trọng mục tiêu']=table['Tỷ trọng mục tiêu'].map(lambda x:f'{x:.2%}')
    table['Số tiền dự kiến']=table['Số tiền dự kiến'].map(lambda x:f'{x:,.0f} VNĐ')
    st.dataframe(table,use_container_width=True)
    defensive_value=rec_best['defensive_weight']*float(st.session_state.get('investment_capital',0))
    st.caption(f'Tài sản phòng thủ dự kiến: {defensive_value:,.0f} VNĐ. Tỷ trọng phòng thủ phụ thuộc Market Regime và được dùng để giảm mức phơi nhiễm cổ phiếu khi thị trường không thuận lợi.')

    st.subheader('8.4. Vì sao phương án này đạt hoặc chưa đạt mục tiêu?')
    expected,target,stock=_diagnose_target_gap(optimization_result,best,policy)
    gap=expected-target
    if expected<target:
        st.warning(f'Danh mục {best} có lợi suất kỳ vọng {expected:.2%}, thấp hơn mục tiêu {target:.2%}, chênh {abs(gap):.2%}. Hệ thống kiểm tra tiếp xem mức thiếu hụt đến từ một vài mã hay từ toàn bộ tập cổ phiếu.')
        negative=stock[stock['Ảnh hưởng so với mục tiêu']<0].copy()
        if not negative.empty:
            view=negative.copy()
            view['Tỷ trọng']=view['Tỷ trọng'].map(lambda x:f'{x:.2%}')
            view['Lợi suất kỳ vọng']=view['Lợi suất kỳ vọng'].map(lambda x:f'{x:.2%}')
            view['Đóng góp vào lợi suất']=view['Đóng góp vào lợi suất'].map(lambda x:f'{x:.2%}')
            view['Ảnh hưởng so với mục tiêu']=view['Ảnh hưởng so với mục tiêu'].map(lambda x:f'{x:.2%}')
            st.dataframe(view,use_container_width=True)
            st.caption('Ảnh hưởng so với mục tiêu = tỷ trọng × phần lợi suất của mã thấp hơn mục tiêu. Giá trị âm cho biết mã đó đang kéo lợi suất kỳ vọng của danh mục xuống.')
        max_mu=float(stock['Lợi suất kỳ vọng'].max()) if not stock.empty else float('nan')
        if pd.notna(max_mu) and max_mu<target:
            st.error(f'Tất cả các mã trong tập hiện tại đều có lợi suất kỳ vọng thấp hơn mục tiêu {target:.2%}. Nên mở rộng tập cổ phiếu hoặc điều chỉnh mục tiêu; không nên ép tỷ trọng vào một mã chỉ để đạt con số mục tiêu.')
        elif len(negative)>1:
            st.info('Có nhiều mã cùng tạo ảnh hưởng âm. Nên đánh giá lại cả tập cổ phiếu thay vì chỉ thay một mã.')
        elif len(negative)==1:
            st.info('Mức thiếu hụt tập trung chủ yếu ở một mã. Có thể xem xét mã này trước khi thay đổi toàn bộ tập cổ phiếu.')
    else:
        st.success(f'Danh mục {best} có lợi suất kỳ vọng {expected:.2%}, đạt mục tiêu {target:.2%}.')
        below=stock[stock['Lợi suất kỳ vọng']<target]
        if not below.empty:
            st.info(f'{len(below)} mã có lợi suất kỳ vọng thấp hơn mục tiêu nhưng các mã còn lại bù đắp đủ để toàn danh mục đạt mục tiêu.')
        else:
            st.info('Các mã trong phương án đều có lợi suất kỳ vọng không thấp hơn mục tiêu trên cơ sở dữ liệu đang sử dụng.')

    st.subheader('8.5. Có nên thay đổi tập cổ phiếu không?')
    if expected<target:
        max_expected=float(summary['Lợi suất kỳ vọng'].max())
        if max_expected<target:
            st.warning('Tập cổ phiếu hiện tại chưa tạo được phương án đạt mục tiêu lợi nhuận. Nên mở rộng tập cổ phiếu với các mã có đặc điểm lợi suất, biến động và tương quan khác nhau, hoặc điều chỉnh mục tiêu xuống mức phù hợp hơn.')
        else:
            st.info('Tập cổ phiếu có ít nhất một phương án đạt mục tiêu, nhưng phương án phù hợp với hồ sơ hiện tại chưa đạt. Nên xem lại sự đánh đổi giữa lợi suất và rủi ro trước khi thay toàn bộ tập cổ phiếu.')
    else:
        st.success('Chưa có lý do từ riêng chỉ tiêu lợi nhuận để thay đổi tập cổ phiếu. Có thể giữ tập hiện tại và tập trung vào phương án phân bổ phù hợp.')
    st.caption('Khuyến nghị chọn cổ phiếu được hiểu là lựa chọn trong tập dữ liệu đầu vào dựa trên lợi suất kỳ vọng, biến động và tương quan. Ứng dụng không kết luận một mã chắc chắn sẽ tăng giá.')

    st.session_state['target_equity']=rec_best['target_equity_weights']
    st.session_state['recommended_portfolio']=best
    st.session_state['recommendation_result']=rec_best
