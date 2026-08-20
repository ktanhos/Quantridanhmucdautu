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
    s=_normalized_summary(summary);target=float(policy.get('target_return',0));limit=_risk_limit(policy)
    feasible=s[(s['Lợi suất kỳ vọng']>=target)&(s['Độ biến động']<=limit)]
    if not feasible.empty:return feasible['Sharpe Ratio'].idxmax(),'Đạt cả mục tiêu lợi nhuận và giới hạn rủi ro.','Đề xuất'
    target_ok=s[s['Lợi suất kỳ vọng']>=target]
    if not target_ok.empty:return target_ok['Sharpe Ratio'].idxmax(),'Có thể đạt mục tiêu lợi nhuận nhưng phải chấp nhận mức rủi ro cao hơn giới hạn hồ sơ.','Đánh đổi'
    return None,'Không phương án nào đạt mục tiêu lợi nhuận với tập cổ phiếu hiện tại.','Không có phương án phù hợp'

def _diagnose_target_gap(optimization_result,best,policy):
    target=float(policy.get('target_return',0));summary=_normalized_summary(optimization_result['summary']);expected=float(summary.loc[best,'Lợi suất kỳ vọng'])
    mu=pd.Series(optimization_result.get('expected_returns',pd.Series(dtype=float)),dtype=float);weights=pd.Series(optimization_result['weights'][best],dtype=float).reindex(mu.index).fillna(0)
    stock=pd.DataFrame({'Tỷ trọng':weights,'Lợi suất kỳ vọng':mu,'Đóng góp vào lợi suất':weights*mu,'Ảnh hưởng so với mục tiêu':weights*(mu-target)})
    return expected,target,stock[stock['Tỷ trọng']>1e-8].sort_values('Ảnh hưởng so với mục tiêu')

def _render_invalid_constraints(optimization_result,policy):
    requested=float(optimization_result.get('requested_max_weight',policy.get('max_single_stock_weight',.20)));n=int(optimization_result.get('universe_size',0));required=int(optimization_result.get('required_assets',math.ceil(1/requested))) if requested>0 else n
    st.subheader('6.1. Chưa có phương án hợp lệ')
    c1,c2,c3=st.columns(3);c1.metric('Số mã hiện có',f'{n}');c2.metric('Giới hạn mỗi mã',f'{requested:.0%}');c3.metric('Số mã tối thiểu',f'{required}')
    st.warning(f'Với {n} mã và giới hạn {requested:.0%} cho mỗi mã, tổng tỷ trọng tối đa chỉ là {n*requested:.0%}. Chưa thể tạo danh mục 100% cổ phiếu mà vẫn tuân thủ giới hạn.')
    st.write(f'Có thể bổ sung ít nhất {max(0,required-n)} mã, hoặc nếu giữ {n} mã thì tăng giới hạn tối đa lên ít nhất {1/n:.0%} mỗi mã.')

def _render_complete_portfolio(optimization_result,best,regime_result,policy):
    equity_min=float(getattr(regime_result,'equity_min',0.0));equity_max=float(getattr(regime_result,'equity_max',1.0));regime=str(getattr(regime_result,'regime','Trung tính'))
    allow_leverage=bool(policy.get('allow_leverage',False));margin_rate=float(policy.get('margin_rate',0.12));max_leverage=float(policy.get('max_leverage',2.0))
    complete=build_complete_portfolio(optimization_result['weights']['Optimal Risky'],optimization_result['expected_returns'],optimization_result['covariance'],float(policy.get('risk_free_rate',.04)),float(policy.get('risk_tolerance',50)),allow_leverage=allow_leverage,margin_rate=margin_rate,max_leverage=max_leverage,regime=regime,equity_min=equity_min,equity_max=equity_max,max_single_stock_weight=float(policy.get('max_single_stock_weight',.20)))
    st.session_state['complete_portfolio_result']=complete;st.session_state['target_equity']=complete['complete_equity_weights'];st.session_state['recommended_portfolio']=best
    st.subheader('6.2. Complete Portfolio và kiểm soát đòn bẩy')
    st.caption('Optimal Risky Portfolio quyết định cấu trúc cổ phiếu. Complete Portfolio quyết định mức phơi nhiễm cổ phiếu so với vốn tự có, phần tài sản phòng thủ và phần vốn vay nếu được cho phép.')
    c1,c2,c3,c4,c5=st.columns(5);c1.metric('Lợi suất ORP',f'{complete["expected_return_orp"]:.2%}');c2.metric('Biến động ORP',f'{complete["volatility_orp"]:.2%}');c3.metric('Tỷ trọng cổ phiếu',f'{complete["y"]:.1%}');c4.metric('Vốn vay',f'{complete["borrowed_weight"]:.1%}');c5.metric('Tài sản phòng thủ',f'{complete["defensive_weight"]:.1%}')
    c1,c2,c3=st.columns(3);c1.metric('Lợi suất Complete',f'{complete["complete_expected_return"]:.2%}');c2.metric('Biến động Complete',f'{complete["complete_volatility"]:.2%}');c3.metric('Sharpe Complete',f'{complete["complete_sharpe"]:.2f}' if np.isfinite(complete['complete_sharpe']) else 'N/A')
    if complete['allow_leverage']:st.info(f'Đòn bẩy tối đa {complete["max_leverage"]:.1f} lần vốn tự có. Lãi suất vay giả định {complete["margin_rate"]:.2%}/năm. Chi phí vay hiện tại tương đương {complete["borrowing_cost"]:.2%} vốn tự có mỗi năm.')
    else:st.info('Đòn bẩy đang tắt. Tổng phơi nhiễm cổ phiếu không vượt 100% vốn tự có và phần còn lại được giữ ở tài sản phòng thủ.')
    table=complete['complete_equity_weights'].sort_values(ascending=False).rename('Tỷ trọng mục tiêu').to_frame();table=table[table['Tỷ trọng mục tiêu']>1e-8]
    capital=float(st.session_state.get('investment_capital',0));table['Số tiền dự kiến']=table['Tỷ trọng mục tiêu']*capital;table['Tỷ trọng mục tiêu']=table['Tỷ trọng mục tiêu'].map(lambda x:f'{x:.2%}');table['Số tiền dự kiến']=table['Số tiền dự kiến'].map(lambda x:f'{x:,.0f} VNĐ');st.dataframe(table,use_container_width=True)
    if complete['borrowed_weight']>1e-8:st.warning(f'Vốn vay dự kiến khoảng {complete["borrowed_weight"]*capital:,.0f} VNĐ nếu vốn tự có là {capital:,.0f} VNĐ. Đây là mô hình hóa chi phí vốn, không phải khuyến nghị vay thực tế.')
    return complete

def render_recommendation(returns,optimization_result,regime_result,policy):
    st.caption('Tầng này nối từ chọn cổ phiếu và tối ưu tỷ trọng sang phân bổ vốn cuối cùng. Market Regime đã được xác định ở tầng phân bổ tài sản và được dùng để đặt khoảng ngân sách cổ phiếu.')
    if not optimization_result or regime_result is None:return
    if not optimization_result.get('constraint_feasible',True):_render_invalid_constraints(optimization_result,policy);return
    summary=_normalized_summary(optimization_result['summary']);best,reason,status=_choose_best(summary,policy)
    if best is None:
        target=float(policy.get('target_return',0));max_expected=float(summary['Lợi suất kỳ vọng'].max());st.subheader('6.1. Chưa có phương án đạt mục tiêu');c1,c2=st.columns(2);c1.metric('Mục tiêu lợi nhuận',f'{target:.2%}');c2.metric('Lợi suất kỳ vọng cao nhất',f'{max_expected:.2%}');st.error(f'Tập cổ phiếu hiện tại chưa tạo được phương án có lợi suất kỳ vọng đạt {target:.2%}. Không ép một nghiệm chỉ để có kết luận.');return
    st.subheader('6.1. Phương án phù hợp nhất với hồ sơ');c1,c2,c3=st.columns(3);c1.metric('Phương án',best);c2.metric('Market Regime',str(getattr(regime_result,'regime','Trung tính')));c3.metric('Lợi suất kỳ vọng',f'{summary.loc[best,"Lợi suất kỳ vọng"]:.2%}')
    st.success(reason) if status=='Đề xuất' else st.warning(reason)
    comparison=summary.copy();comparison['Đạt mục tiêu']=comparison['Lợi suất kỳ vọng']>=float(policy.get('target_return',0));comparison['Phù hợp rủi ro']=comparison['Độ biến động']<=_risk_limit(policy);comparison['Lợi suất kỳ vọng']=comparison['Lợi suất kỳ vọng'].map(lambda x:f'{x:.2%}');comparison['Độ biến động']=comparison['Độ biến động'].map(lambda x:f'{x:.2%}');comparison['Sharpe Ratio']=comparison['Sharpe Ratio'].map(lambda x:f'{x:.2f}');st.dataframe(comparison,use_container_width=True)
    complete=_render_complete_portfolio(optimization_result,best,regime_result,policy)
    st.subheader('6.3. Kiểm tra mục tiêu lợi nhuận');expected,target,stock=_diagnose_target_gap(optimization_result,best,policy)
    if expected<target:st.warning(f'Danh mục {best} có lợi suất kỳ vọng {expected:.2%}, thấp hơn mục tiêu {target:.2%}.')
    else:st.success(f'Danh mục {best} có lợi suất kỳ vọng {expected:.2%}, đạt mục tiêu {target:.2%} trước khi xét kết quả thực tế.')
    negative=stock[stock['Ảnh hưởng so với mục tiêu']<0].copy()
    if not negative.empty:
        for col in ['Tỷ trọng','Lợi suất kỳ vọng','Đóng góp vào lợi suất','Ảnh hưởng so với mục tiêu']:negative[col]=negative[col].map(lambda x:f'{x:.2%}')
        st.dataframe(negative,use_container_width=True)
    st.session_state['recommendation_result']=complete
