import math
import numpy as np
import pandas as pd
import streamlit as st
from portfolio_recommendation import build_complete_portfolio,equity_frame_from_profile

def _normalized_summary(summary):
    s=summary.copy();aliases={'Lợi suất ước tính':'Lợi suất kỳ vọng','Độ biến động ước tính':'Độ biến động','Sharpe Ratio ước tính':'Sharpe Ratio'};rename={a:b for a,b in aliases.items() if a in s.columns and b not in s.columns};return s.rename(columns=rename) if rename else s

def _risk_limit(policy):return .15+.25*float(policy.get('risk_capacity',50))/100

def _choose_best(summary,policy):
    s=_normalized_summary(summary);target=float(policy.get('target_return',0));limit=_risk_limit(policy);feasible=s[(s['Lợi suất kỳ vọng']>=target)&(s['Độ biến động']<=limit)]
    if not feasible.empty:return feasible['Sharpe Ratio'].idxmax(),'Phương án này đáp ứng mục tiêu lợi nhuận và nằm trong mức biến động bạn đặt ra.','Phù hợp'
    target_ok=s[s['Lợi suất kỳ vọng']>=target]
    if not target_ok.empty:return target_ok['Sharpe Ratio'].idxmax(),'Có phương án đạt mục tiêu lợi nhuận nhưng cần chấp nhận biến động cao hơn mức bạn đặt ra.','Đánh đổi'
    return None,'Tập cổ phiếu hiện tại chưa tạo được phương án có lợi suất kỳ vọng đạt mục tiêu.','Chưa phù hợp'

def _render_invalid_constraints(result,policy):
    requested=float(result.get('requested_max_weight',policy.get('max_single_stock_weight',.20)));n=int(result.get('universe_size',0));required=math.ceil(1/requested) if requested>0 else n;st.warning(f'Với {n} mã và giới hạn {requested:.0%} mỗi mã, chưa thể tạo danh mục 100% cổ phiếu mà vẫn giữ đúng giới hạn. Cần ít nhất {required} mã.')

def _render_complete_portfolio(result,best,regime_result,policy):
    regime_min=float(getattr(regime_result,'equity_min',0));regime_max=float(getattr(regime_result,'equity_max',1));regime=str(getattr(regime_result,'regime','Trung tính'));profile_min,profile_max=equity_frame_from_profile(policy)
    complete=build_complete_portfolio(result['weights']['Optimal Risky'],result['expected_returns'],result['covariance'],float(policy.get('risk_free_rate',.04)),float(policy.get('risk_tolerance',50)),allow_leverage=bool(policy.get('allow_leverage',False)),margin_rate=float(policy.get('margin_rate',.12)),max_leverage=float(policy.get('max_leverage',2)),regime=regime,equity_min=regime_min,equity_max=regime_max,profile_equity_min=profile_min,profile_equity_max=profile_max,max_single_stock_weight=float(policy.get('max_single_stock_weight',.20)))
    st.session_state['complete_portfolio_result']=complete;st.session_state['target_equity']=complete['y'];st.session_state['recommended_portfolio']=best
    st.subheader('6.1. Khung đầu tư của bạn');c1,c2,c3=st.columns(3);c1.metric('Theo mức chấp nhận rủi ro',f'{profile_min:.0%} đến {profile_max:.0%}');c2.metric('Theo tình trạng thị trường',f'{regime_min:.0%} đến {regime_max:.0%}');c3.metric('Khung áp dụng',f'{complete["final_equity_min"]:.0%} đến {complete["final_equity_max"]:.0%}');st.caption('Mức chấp nhận rủi ro đặt giới hạn dài hạn. Tình trạng thị trường chỉ điều chỉnh trong giới hạn phù hợp với bạn.')
    st.subheader('6.2. Phân bổ vốn cuối cùng');c1,c2,c3,c4=st.columns(4);c1.metric('Vốn dành cho cổ phiếu',f'{complete["y"]:.1%}');c2.metric('Phần vốn chưa đầu tư vào cổ phiếu',f'{complete["defensive_weight"]:.1%}');c3.metric('Vốn vay',f'{complete["borrowed_weight"]:.1%}');c4.metric('Lợi suất kỳ vọng toàn danh mục',f'{complete["complete_expected_return"]:.2%}')
    table=complete['complete_equity_weights'].sort_values(ascending=False).rename('Tỷ trọng mục tiêu').to_frame();table=table[table['Tỷ trọng mục tiêu']>1e-8];capital=float(st.session_state.get('investment_capital',0));table['Số tiền dự kiến']=table['Tỷ trọng mục tiêu']*capital;view=table.copy();view['Tỷ trọng mục tiêu']=view['Tỷ trọng mục tiêu'].map(lambda x:f'{x:.2%}');view['Số tiền dự kiến']=view['Số tiền dự kiến'].map(lambda x:f'{x:,.0f} VNĐ');st.dataframe(view,use_container_width=True);return complete

def render_recommendation(returns,optimization_result,regime_result,policy):
    st.header('Bước 6. Xác định mức đầu tư cuối cùng');st.markdown('<div class="section-note">Sau khi biết cách chia tiền giữa các cổ phiếu, hệ thống xác định tổng phần vốn nên đưa vào cổ phiếu, phần chưa đầu tư và phần vốn vay nếu có.</div>',unsafe_allow_html=True)
    if not optimization_result or regime_result is None:return
    if not optimization_result.get('constraint_feasible',True):_render_invalid_constraints(optimization_result,policy);return
    summary=_normalized_summary(optimization_result['summary']);best,reason,status=_choose_best(summary,policy)
    if best is None:st.warning(reason);return
    c1,c2,c3=st.columns(3);c1.metric('Phương án phù hợp nhất',best);c2.metric('Tình trạng thị trường',str(getattr(regime_result,'regime','Trung tính')));c3.metric('Lợi suất kỳ vọng',f'{summary.loc[best,"Lợi suất kỳ vọng"]:.2%}');st.success(reason) if status=='Phù hợp' else st.warning(reason)
    complete=_render_complete_portfolio(optimization_result,best,regime_result,policy);st.subheader('6.3. Kiểm tra mục tiêu');expected=float(summary.loc[best,'Lợi suất kỳ vọng']);target=float(policy.get('target_return',0))
    if expected>=target:st.success(f'Phương án có lợi suất kỳ vọng {expected:.2%}, cao hơn mục tiêu {target:.2%}. Đây là ước tính từ dữ liệu và mô hình, không phải lợi nhuận được bảo đảm.')
    else:st.warning(f'Phương án có lợi suất kỳ vọng {expected:.2%}, thấp hơn mục tiêu {target:.2%}. Có thể xem lại tập cổ phiếu, mục tiêu hoặc mức biến động chấp nhận.')
    st.session_state['recommendation_result']=complete
