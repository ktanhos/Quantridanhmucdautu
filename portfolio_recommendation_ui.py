import math
import numpy as np
import pandas as pd
import streamlit as st
from portfolio_recommendation import build_complete_portfolio

SCENARIOS=['Phân bổ tham chiếu','Minimum Variance','Optimal Risky','Maximum Return']


def _normalized_summary(summary):
    s=summary.copy()
    aliases={'Lợi suất ước tính':'Lợi suất kỳ vọng','Độ biến động ước tính':'Độ biến động','Sharpe Ratio ước tính':'Sharpe Ratio'}
    rename={old:new for old,new in aliases.items() if old in s.columns and new not in s.columns}
    if rename:s=s.rename(columns=rename)
    required=['Lợi suất kỳ vọng','Độ biến động','Sharpe Ratio']
    missing=[c for c in required if c not in s.columns]
    if missing:raise ValueError('Kết quả tối ưu hóa thiếu chỉ tiêu: '+', '.join(missing))
    return s


def _risk_limit(policy):
    return 0.15+0.25*float(policy.get('risk_capacity',50))/100


def _choose_best(summary,policy):
    s=_normalized_summary(summary)
    target=float(policy.get('target_return',0))
    limit=_risk_limit(policy)
    feasible=s[(s['Lợi suất kỳ vọng']>=target)&(s['Độ biến động']<=limit)]
    if not feasible.empty:return feasible['Sharpe Ratio'].idxmax(),'Đạt cả mục tiêu lợi nhuận và giới hạn rủi ro.','Đề xuất'
    target_ok=s[s['Lợi suất kỳ vọng']>=target]
    if not target_ok.empty:
        best=target_ok['Sharpe Ratio'].idxmax()
        return best,'Có thể đạt mục tiêu lợi nhuận nhưng phải chấp nhận mức rủi ro cao hơn giới hạn hồ sơ. Đây là phương án đánh đổi.','Đánh đổi'
    return None,'Không phương án nào đạt mục tiêu lợi nhuận với tập cổ phiếu hiện tại.','Không có phương án phù hợp'


def _diagnose_target_gap(optimization_result,best,policy):
    target=float(policy.get('target_return',0))
    summary=_normalized_summary(optimization_result['summary'])
    expected=float(summary.loc[best,'Lợi suất kỳ vọng'])
    mu=pd.Series(optimization_result.get('expected_returns',pd.Series(dtype=float)),dtype=float)
    weights=pd.Series(optimization_result['weights'][best],dtype=float).reindex(mu.index).fillna(0)
    stock=pd.DataFrame({'Tỷ trọng':weights,'Lợi suất kỳ vọng':mu,'Đóng góp vào lợi suất':weights*mu,'Ảnh hưởng so với mục tiêu':weights*(mu-target)})
    return expected,target,stock[stock['Tỷ trọng']>1e-8].sort_values('Ảnh hưởng so với mục tiêu')


def _render_invalid_constraints(optimization_result,policy):
    requested=float(optimization_result.get('requested_max_weight',policy.get('max_single_stock_weight',.20)))
    n=int(optimization_result.get('universe_size',0))
    required=int(optimization_result.get('required_assets',math.ceil(1/requested))) if requested>0 else n
    st.subheader('8.1. Chưa có phương án hợp lệ')
    c1,c2,c3=st.columns(3)
    c1.metric('Số mã hiện có',f'{n}');c2.metric('Giới hạn mỗi mã',f'{requested:.0%}');c3.metric('Số mã tối thiểu',f'{required}')
    st.warning(f'Với {n} mã và giới hạn {requested:.0%} cho mỗi mã, tổng tỷ trọng tối đa chỉ là {n*requested:.0%}. Chưa thể tạo danh mục 100% cổ phiếu mà vẫn tuân thủ giới hạn.')
    st.write(f'Có thể bổ sung ít nhất {max(0,required-n)} mã, hoặc nếu giữ {n} mã thì tăng giới hạn tối đa lên ít nhất {1/n:.0%} mỗi mã.')
    st.write('Nếu mục tiêu lợi nhuận quá cao, có thể giảm mục tiêu hoặc mở rộng tập cổ phiếu. Không ép một mã vượt giới hạn chỉ để đạt mục tiêu.')


def _render_complete_portfolio(optimization_result,best,regime_result,policy):
    weights=optimization_result['weights'][best]
    if best!='Optimal Risky':
        st.info('Complete Portfolio được xây dựng trên Optimal Risky Portfolio. Vì phương án đang được chọn không phải Optimal Risky, hệ thống vẫn hiển thị Complete Portfolio dựa trên ORP để giữ đúng logic CFA.')
    equity_min=float(getattr(regime_result,'equity_min',0.0))
    equity_max=float(getattr(regime_result,'equity_max',1.0))
    regime=str(getattr(regime_result,'regime','Trung tính'))
    complete=build_complete_portfolio(
        optimization_result['weights']['Optimal Risky'],
        optimization_result['expected_returns'],
        optimization_result['covariance'],
        float(policy.get('risk_free_rate',.04)),
        float(policy.get('risk_tolerance',50)),
        regime=regime,equity_min=equity_min,equity_max=equity_max,
        max_single_stock_weight=float(policy.get('max_single_stock_weight',.20)),
    )
    st.session_state['complete_portfolio_result']=complete
    st.session_state['target_equity']=complete['complete_equity_weights']
    st.session_state['recommended_portfolio']=best
    st.subheader('8.3. Complete Portfolio theo logic CFA')
    st.caption('Optimal Risky Portfolio xác định cấu trúc cổ phiếu. Sau đó hệ thống xác định mức đầu tư vào danh mục rủi ro theo hàm Utility và hồ sơ rủi ro. Phần còn lại được giữ ở tài sản phòng thủ. Phiên bản hiện tại không cho phép bán khống hoặc đòn bẩy.')
    c1,c2,c3,c4=st.columns(4)
    c1.metric('Optimal Risky Portfolio',f'{complete["expected_return_orp"]:.2%}')
    c2.metric('Biến động ORP',f'{complete["volatility_orp"]:.2%}')
    c3.metric('Hệ số ngại rủi ro A',f'{complete["risk_aversion"]:.2f}')
    c4.metric('Tỷ trọng cổ phiếu y',f'{complete["y"]:.1%}')
    st.caption(f'Tỷ trọng cổ phiếu y được tính từ y = [E(R_ORP) − Rf] / [A × σ²_ORP]. Hệ số A là tham số nội bộ được quy đổi từ lựa chọn hồ sơ rủi ro, không phải thang điểm CFA quy định.')
    c1,c2,c3=st.columns(3)
    c1.metric('Lợi suất kỳ vọng Complete',f'{complete["complete_expected_return"]:.2%}')
    c2.metric('Biến động Complete',f'{complete["complete_volatility"]:.2%}')
    c3.metric('Sharpe Complete',f'{complete["complete_sharpe"]:.2f}' if np.isfinite(complete['complete_sharpe']) else 'N/A')
    st.markdown('#### Phân bổ cuối cùng')
    table=complete['complete_equity_weights'].sort_values(ascending=False).rename('Tỷ trọng mục tiêu').to_frame()
    table=table[table['Tỷ trọng mục tiêu']>1e-8]
    capital=float(st.session_state.get('investment_capital',0))
    table['Số tiền dự kiến']=table['Tỷ trọng mục tiêu']*capital
    table['Tỷ trọng mục tiêu']=table['Tỷ trọng mục tiêu'].map(lambda x:f'{x:.2%}')
    table['Số tiền dự kiến']=table['Số tiền dự kiến'].map(lambda x:f'{x:,.0f} VNĐ')
    st.dataframe(table,use_container_width=True)
    defensive_value=complete['defensive_weight']*capital
    st.info(f'Tài sản phòng thủ: {complete["defensive_weight"]:.1%}, tương đương khoảng {defensive_value:,.0f} VNĐ. Đây là phần vốn không phân bổ vào ORP.')
    with st.expander('Giải thích theo CFA',expanded=False):
        st.write('Optimal Risky Portfolio là danh mục cổ phiếu có Sharpe Ratio cao nhất trong tập phương án. Complete Portfolio trả lời câu hỏi tiếp theo: nhà đầu tư nên đưa bao nhiêu phần vốn vào danh mục rủi ro và bao nhiêu phần vào tài sản phòng thủ.')
        st.write('Nếu y bằng 100%, toàn bộ vốn được đầu tư vào ORP. Nếu y nhỏ hơn 100%, phần còn lại là tài sản phòng thủ. Phiên bản hiện tại không cho phép y lớn hơn 100% vì ứng dụng không hỗ trợ đòn bẩy.')
    return complete


def render_recommendation(returns,optimization_result,regime_result,policy):
    st.header('Bước 8. So sánh và đề xuất phân bổ')
    st.caption('Hệ thống đi từ các phương án tối ưu hóa đến Optimal Risky Portfolio, sau đó chuyển sang Complete Portfolio theo hồ sơ rủi ro. Người dùng không cần nhập trước danh mục.')
    if not optimization_result or regime_result is None:return
    if not optimization_result.get('constraint_feasible',True):
        _render_invalid_constraints(optimization_result,policy)
        st.info('Các nghiệm ở Bước 7 chưa đáp ứng giới hạn tỷ trọng nên hệ thống không chuyển chúng thành danh mục mục tiêu.')
        return
    summary=_normalized_summary(optimization_result['summary'])
    best,reason,status=_choose_best(summary,policy)
    if best is None:
        target=float(policy.get('target_return',0));max_expected=float(summary['Lợi suất kỳ vọng'].max())
        st.subheader('8.1. Chưa có phương án đạt mục tiêu')
        c1,c2=st.columns(2);c1.metric('Mục tiêu lợi nhuận',f'{target:.2%}');c2.metric('Lợi suất kỳ vọng cao nhất',f'{max_expected:.2%}')
        st.error(f'Tập cổ phiếu hiện tại chưa tạo được phương án có lợi suất kỳ vọng đạt {target:.2%}. Không gắn nhãn một phương án là tối ưu chỉ để có kết luận.')
        st.write('Có thể mở rộng tập cổ phiếu, giảm mục tiêu hoặc chấp nhận đánh đổi rủi ro cao hơn.')
        best_gap=summary['Lợi suất kỳ vọng'].idxmax();expected,target,stock=_diagnose_target_gap(optimization_result,best_gap,policy)
        negative=stock[stock['Ảnh hưởng so với mục tiêu']<0].copy()
        if not negative.empty:
            view=negative.copy()
            for col in ['Tỷ trọng','Lợi suất kỳ vọng','Đóng góp vào lợi suất','Ảnh hưởng so với mục tiêu']:view[col]=view[col].map(lambda x:f'{x:.2%}')
            st.dataframe(view,use_container_width=True)
        return

    st.subheader('8.1. Phương án phù hợp nhất với hồ sơ')
    c1,c2,c3=st.columns(3);c1.metric('Phương án',best);c2.metric('Market Regime',str(getattr(regime_result,'regime','Trung tính')));c3.metric('Lợi suất kỳ vọng',f'{summary.loc[best,"Lợi suất kỳ vọng"]:.2%}')
    if status=='Đề xuất':st.success(reason)
    else:st.warning(reason)
    st.caption('Phương án được chọn theo mục tiêu lợi nhuận, giới hạn rủi ro và Sharpe Ratio. Đây là tiêu chí định hướng, không phải bảo đảm lợi nhuận.')

    st.subheader('8.2. So sánh các phương án')
    comparison=summary.copy();comparison['Đạt mục tiêu']=comparison['Lợi suất kỳ vọng']>=float(policy.get('target_return',0));comparison['Phù hợp rủi ro']=comparison['Độ biến động']<=_risk_limit(policy)
    comparison['Lợi suất kỳ vọng']=comparison['Lợi suất kỳ vọng'].map(lambda x:f'{x:.2%}');comparison['Độ biến động']=comparison['Độ biến động'].map(lambda x:f'{x:.2%}');comparison['Sharpe Ratio']=comparison['Sharpe Ratio'].map(lambda x:f'{x:.2f}')
    st.dataframe(comparison,use_container_width=True)

    complete=_render_complete_portfolio(optimization_result,best,regime_result,policy)

    st.subheader('8.4. Vì sao phương án này đạt hoặc chưa đạt mục tiêu?')
    expected,target,stock=_diagnose_target_gap(optimization_result,best,policy)
    if expected<target:
        st.warning(f'Danh mục {best} có lợi suất kỳ vọng {expected:.2%}, thấp hơn mục tiêu {target:.2%}.')
        negative=stock[stock['Ảnh hưởng so với mục tiêu']<0].copy()
        if not negative.empty:
            view=negative.copy()
            for col in ['Tỷ trọng','Lợi suất kỳ vọng','Đóng góp vào lợi suất','Ảnh hưởng so với mục tiêu']:view[col]=view[col].map(lambda x:f'{x:.2%}')
            st.dataframe(view,use_container_width=True)
            st.caption('Ảnh hưởng so với mục tiêu = tỷ trọng × phần lợi suất của mã thấp hơn mục tiêu. Giá trị âm cho biết mã đó đang kéo lợi suất kỳ vọng của danh mục xuống.')
        if float(stock['Lợi suất kỳ vọng'].max())<target:st.error('Tất cả các mã trong tập hiện tại đều có lợi suất kỳ vọng thấp hơn mục tiêu. Nên mở rộng tập cổ phiếu hoặc điều chỉnh mục tiêu.')
        elif len(negative)>1:st.info('Có nhiều mã cùng tạo ảnh hưởng âm. Nên đánh giá lại cả tập cổ phiếu.')
        elif len(negative)==1:st.info('Mức thiếu hụt tập trung chủ yếu ở một mã. Có thể xem xét mã này trước khi thay đổi toàn bộ tập cổ phiếu.')
    else:
        st.success(f'Danh mục {best} có lợi suất kỳ vọng {expected:.2%}, đạt mục tiêu {target:.2%}.')

    st.subheader('8.5. Có nên thay đổi tập cổ phiếu không?')
    if expected<target:
        max_expected=float(summary['Lợi suất kỳ vọng'].max())
        if max_expected<target:st.warning('Tập cổ phiếu hiện tại chưa tạo được phương án đạt mục tiêu. Nên mở rộng tập cổ phiếu hoặc điều chỉnh mục tiêu.')
        else:st.info('Tập cổ phiếu có phương án đạt mục tiêu nhưng phương án phù hợp hồ sơ chưa đạt. Nên xem lại sự đánh đổi giữa lợi suất và rủi ro.')
    else:st.success('Chưa có lý do từ riêng chỉ tiêu lợi nhuận để thay đổi tập cổ phiếu.')
    st.caption('Khuyến nghị chọn cổ phiếu chỉ là lựa chọn trong tập dữ liệu đầu vào dựa trên lợi suất kỳ vọng, biến động và tương quan. Ứng dụng không kết luận một mã chắc chắn sẽ tăng giá.')
    st.session_state['recommended_portfolio']=best
    st.session_state['recommendation_result']=complete
