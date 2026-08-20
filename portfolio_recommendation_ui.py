import math
import numpy as np
import pandas as pd
import streamlit as st
from portfolio_recommendation import build_complete_portfolio


def _normalized_summary(summary):
    s=summary.copy()
    aliases={'Lợi suất ước tính':'Lợi suất kỳ vọng','Độ biến động ước tính':'Độ biến động','Sharpe Ratio ước tính':'Sharpe Ratio'}
    rename={old:new for old,new in aliases.items() if old in s.columns and new not in s.columns}
    if rename:s=s.rename(columns=rename)
    required=['Lợi suất kỳ vọng','Độ biến động','Sharpe Ratio']
    missing=[c for c in required if c not in s.columns]
    if missing:raise ValueError('Kết quả tính toán thiếu chỉ tiêu: '+', '.join(missing))
    return s


def _risk_limit(policy):
    return 0.15+0.25*float(policy.get('risk_capacity',50))/100


def _choose_best(summary,policy):
    s=_normalized_summary(summary)
    target=float(policy.get('target_return',0))
    limit=_risk_limit(policy)
    feasible=s[(s['Lợi suất kỳ vọng']>=target)&(s['Độ biến động']<=limit)]
    if not feasible.empty:return feasible['Sharpe Ratio'].idxmax(),'Đạt mục tiêu lợi nhuận và nằm trong mức biến động phù hợp.','Phù hợp'
    target_ok=s[s['Lợi suất kỳ vọng']>=target]
    if not target_ok.empty:
        best=target_ok['Sharpe Ratio'].idxmax()
        return best,'Có thể đạt mục tiêu lợi nhuận nhưng cần chấp nhận biến động cao hơn mức bạn đặt ra.','Đánh đổi'
    return None,'Tập cổ phiếu hiện tại chưa tạo được phương án đạt mục tiêu lợi nhuận.','Chưa phù hợp'


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
    st.subheader('Chưa tạo được danh mục hợp lệ')
    c1,c2,c3=st.columns(3)
    c1.metric('Số mã hiện có',f'{n}');c2.metric('Giới hạn mỗi mã',f'{requested:.0%}');c3.metric('Số mã tối thiểu',f'{required}')
    st.warning(f'Với {n} mã và giới hạn {requested:.0%} cho mỗi mã, tổng tỷ trọng tối đa chỉ là {n*requested:.0%}. Chưa thể tạo danh mục 100% cổ phiếu mà vẫn giữ đúng giới hạn.')
    st.write(f'Có thể bổ sung ít nhất {max(0,required-n)} mã, hoặc nếu giữ {n} mã thì tăng giới hạn tối đa lên ít nhất {1/n:.0%} mỗi mã.')
    st.write('Không ép một cổ phiếu vượt giới hạn chỉ để tạo ra một kết quả đẹp.')


def _render_complete_portfolio(optimization_result,best,regime_result,policy):
    equity_min=float(getattr(regime_result,'equity_min',0.0))
    equity_max=float(getattr(regime_result,'equity_max',1.0))
    regime=str(getattr(regime_result,'regime','Trung tính'))
    allow_leverage=bool(policy.get('allow_leverage',False))
    margin_rate=float(policy.get('margin_rate',0.12))
    max_leverage=float(policy.get('max_leverage',2.0))
    complete=build_complete_portfolio(
        optimization_result['weights']['Optimal Risky'],optimization_result['expected_returns'],optimization_result['covariance'],
        float(policy.get('risk_free_rate',.04)),float(policy.get('risk_tolerance',50)),
        allow_leverage=allow_leverage,margin_rate=margin_rate,max_leverage=max_leverage,
        regime=regime,equity_min=equity_min,equity_max=equity_max,
        max_single_stock_weight=float(policy.get('max_single_stock_weight',.20)),
    )
    st.session_state['complete_portfolio_result']=complete
    st.session_state['target_equity']=complete['complete_equity_weights']
    st.session_state['recommended_portfolio']=best

    st.subheader('Phân bổ vốn cuối cùng')
    st.caption('Sau khi xác định nhóm cổ phiếu phù hợp, hệ thống tính xem nên đưa bao nhiêu vốn vào cổ phiếu, bao nhiêu giữ ở tài sản phòng thủ và có nên sử dụng tiền vay hay không.')
    c1,c2,c3,c4,c5=st.columns(5)
    c1.metric('Lợi suất kỳ vọng cổ phiếu',f'{complete["expected_return_orp"]:.2%}')
    c2.metric('Biến động',f'{complete["volatility_orp"]:.2%}')
    c3.metric('Vốn dành cho cổ phiếu',f'{complete["y"]:.1%}')
    c4.metric('Vốn vay',f'{complete["borrowed_weight"]:.1%}')
    c5.metric('Vốn phòng thủ',f'{complete["defensive_weight"]:.1%}')
    c1,c2,c3=st.columns(3)
    c1.metric('Lợi suất kỳ vọng toàn danh mục',f'{complete["complete_expected_return"]:.2%}')
    c2.metric('Biến động toàn danh mục',f'{complete["complete_volatility"]:.2%}')
    c3.metric('Hiệu quả trên mỗi đơn vị rủi ro',f'{complete["complete_sharpe"]:.2f}' if np.isfinite(complete['complete_sharpe']) else 'N/A')
    if complete['allow_leverage']:
        st.warning(f'Bạn đang sử dụng tiền vay. Mức đầu tư vào cổ phiếu là {complete["y"]:.1%} vốn tự có, trong đó {complete["borrowed_weight"]:.1%} là vốn vay. Lãi suất vay giả định {complete["margin_rate"]:.2%}/năm.')
    else:
        st.info('Chưa sử dụng tiền vay. Tổng vốn đầu tư vào cổ phiếu không vượt quá vốn tự có.')
    table=complete['complete_equity_weights'].sort_values(ascending=False).rename('Tỷ trọng mục tiêu').to_frame()
    table=table[table['Tỷ trọng mục tiêu']>1e-8]
    capital=float(st.session_state.get('investment_capital',0))
    table['Số tiền dự kiến']=table['Tỷ trọng mục tiêu']*capital
    table['Tỷ trọng mục tiêu']=table['Tỷ trọng mục tiêu'].map(lambda x:f'{x:.2%}')
    table['Số tiền dự kiến']=table['Số tiền dự kiến'].map(lambda x:f'{x:,.0f} VNĐ')
    st.dataframe(table,use_container_width=True)
    if complete['borrowed_weight']>1e-8:
        st.warning(f'Vốn vay dự kiến khoảng {complete["borrowed_weight"]*capital:,.0f} VNĐ nếu vốn tự có là {capital:,.0f} VNĐ. Đây là mô phỏng chi phí vốn, không phải khuyến nghị vay thực tế.')
    return complete


def render_recommendation(returns,optimization_result,regime_result,policy):
    st.header('Bước 6. Chia tỷ trọng và kiểm soát tiền vay')
    st.markdown('<div class="section-note">Sau khi biết thị trường đang ở trạng thái nào và đã chọn được tập cổ phiếu, hệ thống chuyển sang câu hỏi quan trọng nhất: mỗi nhóm và mỗi cổ phiếu nên chiếm bao nhiêu trong tổng vốn?</div>',unsafe_allow_html=True)
    if not optimization_result or regime_result is None:return
    if not optimization_result.get('constraint_feasible',True):
        _render_invalid_constraints(optimization_result,policy);return
    summary=_normalized_summary(optimization_result['summary'])
    best,reason,status=_choose_best(summary,policy)
    if best is None:
        target=float(policy.get('target_return',0));max_expected=float(summary['Lợi suất kỳ vọng'].max())
        st.subheader('Chưa có phương án phù hợp')
        c1,c2=st.columns(2);c1.metric('Mục tiêu lợi nhuận',f'{target:.2%}');c2.metric('Lợi suất kỳ vọng cao nhất',f'{max_expected:.2%}')
        st.error(f'Tập cổ phiếu hiện tại chưa tạo được phương án có lợi suất kỳ vọng đạt {target:.2%}.')
        st.write('Có thể mở rộng tập cổ phiếu, giảm mục tiêu hoặc chấp nhận mức biến động cao hơn.')
        return
    st.subheader('Phương án phù hợp nhất với mục tiêu')
    c1,c2,c3=st.columns(3);c1.metric('Phương án phân bổ',best);c2.metric('Tình trạng thị trường',str(getattr(regime_result,'regime','Trung tính')));c3.metric('Lợi suất kỳ vọng',f'{summary.loc[best,"Lợi suất kỳ vọng"]:.2%}')
    if status=='Phù hợp':st.success(reason)
    else:st.warning(reason)
    st.subheader('So sánh các cách phân bổ')
    comparison=summary.copy();comparison['Đạt mục tiêu']=comparison['Lợi suất kỳ vọng']>=float(policy.get('target_return',0));comparison['Phù hợp mức biến động']=comparison['Độ biến động']<=_risk_limit(policy);comparison['Lợi suất kỳ vọng']=comparison['Lợi suất kỳ vọng'].map(lambda x:f'{x:.2%}');comparison['Độ biến động']=comparison['Độ biến động'].map(lambda x:f'{x:.2%}');comparison['Sharpe Ratio']=comparison['Sharpe Ratio'].map(lambda x:f'{x:.2f}')
    st.dataframe(comparison,use_container_width=True)
    complete=_render_complete_portfolio(optimization_result,best,regime_result,policy)
    st.subheader('Kiểm tra mục tiêu lợi nhuận')
    expected,target,stock=_diagnose_target_gap(optimization_result,best,policy)
    if expected<target:
        st.warning(f'Danh mục được chọn có lợi suất kỳ vọng {expected:.2%}, thấp hơn mục tiêu {target:.2%}.')
        negative=stock[stock['Ảnh hưởng so với mục tiêu']<0].copy()
        if not negative.empty:
            view=negative.copy()
            for col in ['Tỷ trọng','Lợi suất kỳ vọng','Đóng góp vào lợi suất','Ảnh hưởng so với mục tiêu']:view[col]=view[col].map(lambda x:f'{x:.2%}')
            st.dataframe(view,use_container_width=True);st.caption('Bảng này cho biết cổ phiếu nào đang kéo lợi suất kỳ vọng của danh mục xuống so với mục tiêu.')
    else:st.success(f'Danh mục được chọn có lợi suất kỳ vọng {expected:.2%}, đạt mục tiêu {target:.2%} trước khi xét kết quả thực tế.')
    st.subheader('Có cần thay đổi tập cổ phiếu không?')
    if expected<target:
        max_expected=float(summary['Lợi suất kỳ vọng'].max())
        if max_expected<target:st.warning('Tập cổ phiếu hiện tại chưa tạo được phương án đạt mục tiêu. Nên mở rộng tập cổ phiếu hoặc điều chỉnh mục tiêu.')
        else:st.info('Tập cổ phiếu có phương án đạt mục tiêu nhưng phương án phù hợp với mức rủi ro hiện tại chưa đạt. Nên xem lại sự đánh đổi giữa lợi nhuận và biến động.')
    else:st.success('Chưa có lý do từ riêng mục tiêu lợi nhuận để thay đổi tập cổ phiếu.')
    st.session_state['recommended_portfolio']=best;st.session_state['recommendation_result']=complete
