from __future__ import annotations
import pandas as pd

def explain_sharpe(x):
    if pd.isna(x): return 'Chưa đủ dữ liệu để đánh giá.'
    if x < 0: return 'Hiệu quả điều chỉnh theo rủi ro đang kém.'
    if x < 0.5: return 'Hiệu quả điều chỉnh theo rủi ro còn thấp.'
    if x < 1: return 'Hiệu quả điều chỉnh theo rủi ro ở mức khá.'
    if x < 2: return 'Hiệu quả điều chỉnh theo rủi ro ở mức tốt.'
    return 'Hiệu quả điều chỉnh theo rủi ro ở mức rất tốt.'

def explain_drawdown(x):
    if pd.isna(x): return 'Chưa đủ dữ liệu để đánh giá.'
    return f'Danh mục từng giảm tối đa khoảng {abs(x):.1%} so với đỉnh trước đó.'

def explain_regime(regime):
    text=str(regime).lower()
    if 'rủi ro cao' in text or 'phòng thủ' in text: return 'Thị trường có tín hiệu yếu hoặc rủi ro cao. Nên thận trọng với tỷ trọng cổ phiếu.'
    if 'tích cực' in text: return 'Thị trường có tín hiệu tích cực. Có thể duy trì tỷ trọng cổ phiếu phù hợp với khả năng chịu rủi ro.'
    return 'Thị trường chưa cho tín hiệu đủ mạnh để nghiêng rõ về trạng thái tích cực hoặc phòng thủ.'

def build_summary(performance, regime_result, rebalance_needed, target_equity=None):
    s=performance or {};return {'sharpe':s.get('Sharpe Ratio'),'drawdown':s.get('Maximum Drawdown'),'cagr':s.get('Annualized Return'),'sharpe_text':explain_sharpe(s.get('Sharpe Ratio')),'drawdown_text':explain_drawdown(s.get('Maximum Drawdown')),'regime_text':explain_regime(getattr(regime_result,'regime','Trung tính') if regime_result else 'Trung tính'),'rebalance_text':'Cần xem xét tái cân bằng theo ngưỡng đã đặt.' if rebalance_needed else 'Chưa cần tái cân bằng theo ngưỡng đã đặt.','target_equity':target_equity}
