from __future__ import annotations
import pandas as pd

def explain_sharpe(x):
    if pd.isna(x): return 'Chưa đủ dữ liệu để đánh giá hiệu quả trên mức biến động đã chịu.'
    if x<0:return 'Trong giai đoạn đánh giá, lợi suất của danh mục chưa đủ bù lãi suất tham chiếu sau khi xét đến mức biến động.'
    return 'Danh mục có lợi suất vượt lãi suất tham chiếu trong giai đoạn đánh giá. Nên đọc cùng mức sụt giảm và kết quả so với VNINDEX thay vì chỉ nhìn riêng chỉ tiêu này.'

def explain_drawdown(x):
    if pd.isna(x):return 'Chưa đủ dữ liệu để đánh giá.'
    return f'Danh mục từng giảm tối đa khoảng {abs(x):.1%} so với đỉnh trước đó.'

def explain_regime(regime):
    text=str(regime).lower()
    if 'rủi ro cao' in text:return 'Thị trường đang có rủi ro cao. Ưu tiên giữ tỷ trọng cổ phiếu ở mức thấp trong khung phù hợp với bạn.'
    if 'phòng thủ' in text:return 'Thị trường cần thận trọng. Tỷ trọng cổ phiếu nên nghiêng về phần thấp trong khung đầu tư của bạn.'
    if 'tích cực mạnh' in text:return 'Thị trường có tín hiệu tích cực mạnh. Có thể nghiêng về phần cao của khung cổ phiếu, nhưng không vượt giới hạn đã đặt.'
    if 'tích cực' in text:return 'Thị trường có tín hiệu tích cực. Có thể duy trì tỷ trọng cổ phiếu cao hơn trong giới hạn phù hợp với bạn.'
    return 'Thị trường chưa cho tín hiệu đủ mạnh để nghiêng rõ về tăng tỷ trọng hoặc giảm mạnh tỷ trọng cổ phiếu.'

def build_actions(performance,regime_result,rebalance_needed,target_equity):
    actions=[];dd=performance.get('Maximum Drawdown') if performance else None;cagr=performance.get('Annualized Return') if performance else None
    if rebalance_needed:actions.append('Xem xét tái cân bằng vì một số tỷ trọng đã lệch khỏi mức mục tiêu.')
    else:actions.append('Chưa cần tái cân bằng theo ngưỡng hiện tại. Tiếp tục theo dõi tỷ trọng và rủi ro.')
    if dd is not None and dd<=-0.25:actions.append('Ưu tiên kiểm tra nguyên nhân khiến danh mục từng giảm sâu và khả năng chịu đựng mức giảm này trước khi tăng thêm tỷ trọng.')
    if target_equity is not None:actions.append(f'Duy trì tổng tỷ trọng cổ phiếu quanh mức mục tiêu {float(target_equity):.1%}, trừ khi thiết lập của bạn hoặc tình trạng thị trường thay đổi.')
    if cagr is not None and cagr<0:actions.append('Kết quả lịch sử đang âm. Không nên tăng rủi ro chỉ để cố đạt mục tiêu lợi nhuận.')
    return actions

def build_summary(performance,regime_result,rebalance_needed,target_equity=None):
    s=performance or {};actions=build_actions(s,regime_result,rebalance_needed,target_equity)
    return {'sharpe':s.get('Sharpe Ratio'),'drawdown':s.get('Maximum Drawdown'),'cagr':s.get('Annualized Return'),'sharpe_text':explain_sharpe(s.get('Sharpe Ratio')),'drawdown_text':explain_drawdown(s.get('Maximum Drawdown')),'regime_text':explain_regime(getattr(regime_result,'regime','Trung tính') if regime_result else 'Trung tính'),'rebalance_text':'Danh mục đang lệch khỏi mức mục tiêu và nên xem xét điều chỉnh.' if rebalance_needed else 'Danh mục chưa lệch đủ xa khỏi mức mục tiêu để cần điều chỉnh.','target_equity':target_equity,'actions':actions}
