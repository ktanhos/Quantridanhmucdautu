import numpy as np
import pandas as pd
import streamlit as st
from portfolio_risk import calculate_portfolio_risk

def render_portfolio_risk(returns, benchmark_returns):
    st.header('Bước 6. Phân tích rủi ro tập cổ phiếu')
    st.caption('Phân tích mức lợi suất, biến động, tương quan và rủi ro của tập cổ phiếu trước khi hệ thống xây dựng các phương án phân bổ. Người dùng không cần nhập tỷ trọng hiện tại.')

    tickers=list(returns.columns)
    if len(tickers) < 2:
        st.warning('Cần ít nhất 2 mã cổ phiếu để thực hiện phân tích đa dạng hóa.')
        return

    # Phân bổ đều chỉ là chuẩn tham chiếu kỹ thuật, không phải danh mục hiện tại.
    equal_weight = 1 / len(tickers)
    weights = pd.Series(equal_weight, index=tickers, dtype=float)

    st.subheader('6.1. Phân tích cơ sở')
    c1,c2,c3=st.columns(3)
    c1.metric('Số cổ phiếu được phân tích',f'{len(tickers):,}')
    c2.metric('Phân bổ cơ sở mỗi mã',f'{equal_weight:.2%}')
    c3.metric('Tổng phân bổ cơ sở',f'{weights.sum():.2%}')
    st.info('Phân bổ đều chỉ được dùng làm mốc tham chiếu để đo rủi ro của tập cổ phiếu. Hệ thống sẽ xây dựng tỷ trọng tối ưu riêng ở bước tiếp theo.')

    try:
        result=calculate_portfolio_risk(returns,weights,benchmark_returns)
    except Exception as exc:
        st.error(str(exc))
        return

    st.subheader('6.2. Tổng quan rủi ro và lợi suất')
    c1,c2,c3,c4=st.columns(4)
    c1.metric('Lợi suất Annualized',f'{result["annual_return"]:.2%}')
    c2.metric('Volatility Annualized',f'{result["annual_volatility"]:.2%}')
    c3.metric('Sharpe Ratio',f'{result["sharpe"]:.2f}')
    c4.metric('Maximum Drawdown',f'{result["max_drawdown"]:.2%}')

    c1,c2,c3,c4=st.columns(4)
    c1.metric('VaR 95% theo ngày',f'{result["var_95_daily"]:.2%}')
    c2.metric('CVaR 95% theo ngày',f'{result["cvar_95_daily"]:.2%}')
    c3.metric('Beta với VNINDEX',f'{result["beta"]:.2f}' if np.isfinite(result['beta']) else 'N/A')
    c4.metric('Information Ratio',f'{result["information_ratio"]:.2f}' if np.isfinite(result['information_ratio']) else 'N/A')

    st.markdown('**Bảng 6.1. Đóng góp rủi ro theo cổ phiếu**')
    rc=result['risk_contribution'].sort_values(ascending=False).rename('Đóng góp rủi ro')
    table=rc.to_frame()
    table['Tỷ trọng cơ sở']=result['weights']
    table['Đóng góp rủi ro']=table['Đóng góp rủi ro'].map(lambda x:f'{x:.2%}')
    table['Tỷ trọng cơ sở']=table['Tỷ trọng cơ sở'].map(lambda x:f'{x:.2%}')
    st.dataframe(table,use_container_width=True)

    st.markdown('**Bảng 6.2. Tương quan giữa các cổ phiếu**')
    st.dataframe(result['correlation'].round(3),use_container_width=True)

    st.markdown('**Bảng 6.3. Mức độ tập trung của phân bổ cơ sở**')
    st.metric('Herfindahl Hirschman Index',f'{result["concentration_hhi"]:.3f}')
    st.caption('HHI được tính trên phân bổ đều làm chuẩn tham chiếu. HHI càng cao thì danh mục càng tập trung. Đây chưa phải tỷ trọng tối ưu hoặc tỷ trọng khuyến nghị.')

    st.subheader('6.3. Diễn giải nhanh')
    sharpe=result['sharpe']
    vol=result['annual_volatility']
    if np.isfinite(sharpe):
        if sharpe >= 1:
            sharpe_text='Hiệu quả điều chỉnh theo rủi ro của phân bổ cơ sở đang ở mức tốt.'
        elif sharpe >= 0.5:
            sharpe_text='Hiệu quả điều chỉnh theo rủi ro của phân bổ cơ sở ở mức khá.'
        else:
            sharpe_text='Hiệu quả điều chỉnh theo rủi ro của phân bổ cơ sở còn thấp.'
        st.write(f'Sharpe Ratio {sharpe:.2f}: {sharpe_text}')
    st.write(f'Volatility Annualized {vol:.2%}: đây là mức biến động ước tính của phân bổ đều trong giai đoạn dữ liệu được phân tích.')
    st.write('Các kết quả ở bước này chỉ mô tả đặc điểm rủi ro của tập cổ phiếu. Bước tối ưu hóa tiếp theo mới quyết định tỷ trọng và phương án phù hợp với hồ sơ nhà đầu tư.')
