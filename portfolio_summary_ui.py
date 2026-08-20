import pandas as pd
import streamlit as st
from portfolio_summary import build_summary


def _pct(v): return 'N/A' if v is None or pd.isna(v) else f'{v:.2%}'
def _ratio(v): return 'N/A' if v is None or pd.isna(v) else f'{v:.2f}'


def render_portfolio_summary(performance, regime_result, rebalance_table, target_equity=None):
    # Đây là phần tiếp nối của Bước 7, không tạo thêm một bước mới.
    if performance is None:
        return

    needed = bool(
        rebalance_table is not None
        and 'Cần tái cân bằng' in rebalance_table
        and rebalance_table['Cần tái cân bằng'].any()
    )
    summary = build_summary(performance, regime_result, needed, target_equity)
    regime = getattr(regime_result, 'regime', 'Trung tính') if regime_result else 'Trung tính'

    st.divider()
    st.subheader('Tổng kết và hành động tiếp theo')
    st.markdown(
        '<div class="section-note">Từ kết quả lịch sử và trạng thái hiện tại, phần này tập trung vào điều quan trọng nhất: danh mục đang phân bổ ra sao, rủi ro nào cần chú ý và bạn nên làm gì tiếp theo.</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric('Trạng thái thị trường', regime)
    c2.metric('Lợi suất quy đổi năm', _pct(summary.get('cagr')))
    c3.metric('Hiệu quả trên mức biến động', _ratio(summary.get('sharpe')))
    c4.metric('Mức giảm lớn nhất', _pct(summary.get('drawdown')))

    if target_equity is not None:
        st.subheader('Danh mục đang phân bổ như thế nào?')
        c1, c2, c3 = st.columns(3)
        c1.metric('Tỷ trọng cổ phiếu mục tiêu', f'{float(target_equity):.1%}')
        c2.metric('Phần vốn chưa đầu tư vào cổ phiếu', f'{max(0, 1 - float(target_equity)):.1%}')
        c3.metric('Tái cân bằng', 'Cần xem xét' if needed else 'Chưa cần')

    st.subheader('Rủi ro cần chú ý')
    st.info(summary.get('drawdown_text', ''))
    st.write(summary.get('regime_text', ''))
    st.write(summary.get('sharpe_text', ''))

    st.subheader('Kết quả có phù hợp mục tiêu không?')
    policy = st.session_state.get('policy') or {}
    target = float(policy.get('target_return', 0))
    cagr = summary.get('cagr')
    if cagr is None:
        st.info('Chưa đủ dữ liệu lịch sử để so sánh với mục tiêu.')
    elif cagr >= target:
        st.success(
            f'Trong giai đoạn đánh giá, lợi suất quy đổi năm {_pct(cagr)} cao hơn mục tiêu {_pct(target)}. Đây là kết quả lịch sử, không phải dự báo.'
        )
    else:
        st.warning(
            f'Trong giai đoạn đánh giá, lợi suất quy đổi năm {_pct(cagr)} thấp hơn mục tiêu {_pct(target)}. Không nên tăng rủi ro chỉ để cố đạt mục tiêu.'
        )

    st.subheader('Có cần tái cân bằng không?')
    if needed:
        st.warning(summary.get('rebalance_text', ''))
    else:
        st.success(summary.get('rebalance_text', ''))

    st.subheader('Việc nên làm tiếp theo')
    for i, action in enumerate(summary.get('actions', []), 1):
        st.write(f'{i}. {action}')

    st.caption('Kết quả lịch sử không bảo đảm lợi nhuận tương lai. Ứng dụng chỉ hỗ trợ định hướng quản trị danh mục và không đặt lệnh thay người dùng.')
