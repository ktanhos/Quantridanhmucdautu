from __future__ import annotations
import pandas as pd

def explain_sharpe(x):
    if pd.isna(x): return 'Chưa đủ dữ liệu để đánh giá.'
    if x < 0: return 'Trong giai đoạn đánh giá, danh mục chưa tạo được lợi suất đủ để bù lãi suất phi rủi ro trên mức biến động đã chịu.'
    if x < 0.5: return 'Danh mục có lợi suất vượt lãi suất phi rủi ro, nhưng mức lợi suất này chưa lớn so với biến động đã chịu. Nên xem thêm mức sụt giảm và kết quả so với VNINDEX.'
    if x < 1: return 'Danh mục tạo ra lợi suất tương đối tốt so với mức biến động trong giai đoạn đánh giá. Nên xem thêm mức sụt giảm và khả năng duy trì kết quả này.'
    return 'Danh mục có hiệu quả tốt trên mỗi đơn vị biến động trong giai đoạn đánh giá. Tuy nhiên, kết quả này không đồng nghĩa với rủi ro thấp hoặc lợi nhuận tương lai chắc chắn.'

def explain_drawdown(x):
    if pd.isna(x): return 'Chưa đủ dữ liệu để đánh giá.'
    return f'Danh mục từng giảm tối đa khoảng {abs(x):.1%} so với đỉnh trước đó.'

def explain_regime(regime):
    text=str(regime).lower()
    if 'rủi ro cao' in text or 'phòng thủ' in text: return 'Thị trường có tín hiệu yếu hoặc rủi ro cao. Nên thận trọng với tỷ trọng cổ phiếu.'
    if 'tích cực' in text: return 'Thị trường có tín hiệu tích cực. Có thể duy trì tỷ trọng cổ phiếu phù hợp với khả năng chịu rủi ro.'
    return 'Thị trường chưa cho tín hiệu đủ mạnh để nghiêng rõ về trạng thái tích cực hoặc phòng thủ.'

def build_summary(performance, regime_result, rebalance_needed, target_equity=None):
    s=performance or {};return {'sharpe':s.get('Sharpe Ratio'),'drawdown':s.get('Maximum Drawdown'),'cagr':s.get('Annualized Return'),'sharpe_text':explain_sharpe(s.get('Sharpe Ratio')),'drawdown_text':explain_drawdown(s.get('Maximum Drawdown')),'regime_text':explain_regime(getattr(regime_result,'regime','Trung tính') if regime_result else 'Trung tính'),'rebalance_text':'Danh mục đang lệch khỏi mức mục tiêu và nên xem xét điều chỉnh.' if rebalance_needed else 'Danh mục chưa lệch đủ xa khỏi mức mục tiêu để cần điều chỉnh.','target_equity':target_equity}
