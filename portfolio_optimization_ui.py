import math
import numpy as np
import streamlit as st
import pandas as pd
import altair as alt
from portfolio_optimization import optimize_portfolios
from portfolio_risk import calculate_portfolio_risk


def _fmt_pct(x):
    return "N/A" if pd.isna(x) else f"{x:.2%}"


def _fmt_ratio(x):
    return "N/A" if pd.isna(x) or not np.isfinite(x) else f"{x:.2f}"


def _historical_comparison(returns, benchmark_returns, weights):
    r = returns.apply(pd.to_numeric, errors="coerce").copy()
    w = pd.Series(weights, dtype=float).reindex(r.columns).fillna(0.0)
    portfolio_daily = r.mul(w, axis=1).sum(axis=1, min_count=1)
    benchmark = pd.Series(benchmark_returns, dtype=float).reindex(portfolio_daily.index)
    frame = pd.concat(
        [portfolio_daily.rename("Danh mục"), benchmark.rename("VNINDEX")], axis=1
    ).dropna()
    if frame.empty:
        return pd.DataFrame()
    return ((1 + frame).cumprod() * 100).sort_index()


def _allocation_chart(weights):
    chart_data = weights.mul(100).reset_index().rename(columns={"index": "Mã"})
    chart_data = chart_data.melt(
        id_vars="Mã", var_name="Phương án", value_name="Tỷ trọng"
    )
    return alt.Chart(chart_data).mark_bar().encode(
        x=alt.X("Phương án:N", title="Phương án", axis=alt.Axis(labelAngle=0)),
        xOffset=alt.XOffset("Mã:N", title="Mã cổ phiếu"),
        y=alt.Y(
            "Tỷ trọng:Q",
            title="Tỷ trọng (%)",
            scale=alt.Scale(domain=[0, 100]),
        ),
        color=alt.Color("Mã:N", title="Mã cổ phiếu"),
        tooltip=[
            alt.Tooltip("Phương án:N"),
            alt.Tooltip("Mã:N"),
            alt.Tooltip("Tỷ trọng:Q", format=".2f"),
        ],
    ).properties(height=420)


def _scenario_metrics_table(result, weights, benchmark_returns):
    rows = []
    for label in weights.columns:
        metrics = calculate_portfolio_risk(
            result["returns"],
            weights[label],
            benchmark_returns=benchmark_returns,
        )
        rows.append(
            {
                "Phương án": label,
                "Lợi suất lịch sử": metrics["annual_return"],
                "Biến động": metrics["annual_volatility"],
                "Sharpe": metrics["sharpe"],
                "Sortino": metrics["sortino"],
                "Maximum Drawdown": metrics["max_drawdown"],
                "VaR 95% ngày": metrics["var_95_daily"],
                "CVaR 95% ngày": metrics["cvar_95_daily"],
                "Beta VNINDEX": metrics["beta"],
                "Information Ratio": metrics["information_ratio"],
                "HHI": metrics["concentration_hhi"],
            }
        )

    table = pd.DataFrame(rows).set_index("Phương án")
    for col in [
        "Lợi suất lịch sử",
        "Biến động",
        "Maximum Drawdown",
        "VaR 95% ngày",
        "CVaR 95% ngày",
    ]:
        table[col] = table[col].map(_fmt_pct)
    for col in ["Sharpe", "Sortino", "Beta VNINDEX", "Information Ratio"]:
        table[col] = table[col].map(_fmt_ratio)
    table["HHI"] = table["HHI"].map(lambda x: "N/A" if pd.isna(x) else f"{x:.3f}")
    return table


def _scenario_detail(label, result, weights, benchmark_returns, investment_capital):
    metrics = calculate_portfolio_risk(
        result["returns"],
        weights[label],
        benchmark_returns=benchmark_returns,
    )

    st.markdown(f"**Đánh giá phương án: {label}**")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Lợi suất lịch sử", _fmt_pct(metrics["annual_return"]))
    c2.metric("Biến động", _fmt_pct(metrics["annual_volatility"]))
    c3.metric("Sharpe Ratio", _fmt_ratio(metrics["sharpe"]))
    c4.metric("Sortino Ratio", _fmt_ratio(metrics["sortino"]))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Maximum Drawdown", _fmt_pct(metrics["max_drawdown"]))
    c2.metric("VaR 95% ngày", _fmt_pct(metrics["var_95_daily"]))
    c3.metric("CVaR 95% ngày", _fmt_pct(metrics["cvar_95_daily"]))
    c4.metric("Calmar Ratio", _fmt_ratio(metrics["calmar"]))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Beta VNINDEX", _fmt_ratio(metrics["beta"]))
    c2.metric("Information Ratio", _fmt_ratio(metrics["information_ratio"]))
    c3.metric("HHI", f"{metrics['concentration_hhi']:.3f}")
    c4.metric("Số vị thế tương đương", f"{metrics['effective_positions']:.1f}")

    st.caption(
        "Các chỉ tiêu lợi suất và rủi ro trong phần này được tính trên chuỗi lợi suất lịch sử của chính phương án. "
        "Lợi suất ước tính trong bảng tối ưu hóa được tính từ trung bình lợi suất lịch sử và dùng làm đầu vào cho bài toán tối ưu."
    )

    selected_weights = weights[label].sort_values(ascending=False)
    selected_table = selected_weights[selected_weights > 1e-6].rename("Tỷ trọng").to_frame()
    selected_table["Số tiền dự kiến"] = selected_table["Tỷ trọng"] * float(investment_capital)
    selected_table["Tỷ trọng"] = selected_table["Tỷ trọng"].map(lambda x: f"{x:.2%}")
    selected_table["Số tiền dự kiến"] = selected_table["Số tiền dự kiến"].map(
        lambda x: f"{x:,.0f} VNĐ" if x > 0 else "N/A"
    )
    st.markdown("**Phân bổ vốn**")
    st.dataframe(selected_table, use_container_width=True)

    st.markdown("**Lịch sử phương án so với VNINDEX**")
    historical = (
        _historical_comparison(result["returns"], benchmark_returns, weights[label])
        if benchmark_returns is not None
        else pd.DataFrame()
    )
    if historical.empty:
        st.info("Chưa đủ dữ liệu chung giữa phương án và VNINDEX để vẽ biểu đồ lịch sử.")
    else:
        st.line_chart(historical, use_container_width=True)
        st.caption(
            "Cả phương án và VNINDEX được quy đổi về 100 tại ngày đầu tiên có dữ liệu chung. Đây là so sánh quá khứ, không phải dự báo lợi nhuận tương lai."
        )
        st.caption(
            f"Giai đoạn so sánh: {historical.index.min().strftime('%d/%m/%Y')} đến {historical.index.max().strftime('%d/%m/%Y')}."
        )


def render_portfolio_optimization(returns, policy, benchmark_returns=None):
    st.header("Bước 7. Tối ưu hóa danh mục")
    st.caption(
        "Xây dựng các phương án phân bổ từ dữ liệu lịch sử. Phân bổ tham chiếu chỉ là mốc so sánh, không phải danh mục nhà đầu tư đang nắm giữ."
    )

    max_weight = float(policy.get("max_single_stock_weight", 0.10)) if policy else 0.10
    target = float(policy.get("target_return", 0)) if policy else None

    try:
        result = optimize_portfolios(
            returns,
            max_weight=max_weight,
            target_return=target,
        )
    except Exception as exc:
        st.error(str(exc))
        return

    st.subheader("7.1. So sánh hiệu quả và rủi ro")
    summary = result["summary"].copy()
    summary["Lợi suất ước tính"] = summary["Lợi suất ước tính"].map(_fmt_pct)
    summary["Độ biến động ước tính"] = summary["Độ biến động ước tính"].map(_fmt_pct)
    summary["Sharpe Ratio ước tính"] = summary["Sharpe Ratio ước tính"].map(_fmt_ratio)
    st.dataframe(summary, use_container_width=True, hide_index=False)

    historical_metrics = _scenario_metrics_table(
        result,
        result["weights"],
        benchmark_returns,
    )
    st.markdown("**Các chỉ tiêu đánh giá trên dữ liệu lịch sử**")
    st.dataframe(historical_metrics, use_container_width=True, hide_index=False)

    constraints_feasible = result.get("constraint_feasible", True)
    if not constraints_feasible:
        required = int(
            result.get(
                "required_assets",
                math.ceil(1 / result["requested_max_weight"]),
            )
        )
        st.warning(
            f"Không thể áp dụng giới hạn {result['requested_max_weight']:.0%}/mã với chỉ {result['universe_size']} mã. "
            f"Cần ít nhất {required} mã để phân bổ đủ 100% vốn cổ phiếu."
        )
        return

    if result.get("target_return") is not None and not result.get("target_feasible", False):
        st.warning(
            "Không tìm thấy phương án thỏa đồng thời mục tiêu lợi nhuận và các ràng buộc hiện tại. "
            "Hệ thống không coi nghiệm không đạt mục tiêu là phương án tối ưu."
        )

    weights = result["weights"].copy()
    n = len(weights.index)
    if abs(result["requested_max_weight"] - 1 / n) < 1e-10:
        st.info(
            f"Tập hiện tại có đúng {n} mã và giới hạn tỷ trọng {result['requested_max_weight']:.0%}/mã, "
            "nên tổng ràng buộc buộc mọi mã phải nhận đúng tỷ trọng giới hạn. Vì vậy các phương án có thể trùng nhau. "
            "Muốn tối ưu hóa có ý nghĩa hơn, cần mở rộng tập mã hoặc điều chỉnh giới hạn tỷ trọng."
        )

    st.subheader("7.2. Phân bổ giữa các phương án")
    display = weights.copy()
    for col in display.columns:
        display[col] = display[col].map(lambda x: f"{x:.2%}")
    st.dataframe(display, use_container_width=True)
    st.markdown("**Biểu đồ 7.1. So sánh tỷ trọng giữa các phương án**")
    st.altair_chart(_allocation_chart(weights), use_container_width=True)
    st.caption(
        "Các cột được đặt cạnh nhau theo từng phương án để so sánh trực tiếp tỷ trọng từng mã. Tổng tỷ trọng của mỗi phương án vẫn bằng 100%."
    )

    scenarios = [
        "Phân bổ tham chiếu",
        "Minimum Variance",
        "Optimal Risky",
        "Maximum Return",
    ]
    tabs = st.tabs(scenarios)
    investment_capital = float(st.session_state.get("investment_capital", 0))
    for tab, label in zip(tabs, scenarios):
        with tab:
            _scenario_detail(
                label,
                result,
                weights,
                benchmark_returns,
                investment_capital,
            )

    st.session_state["optimization_result"] = result
    st.session_state["scenario_weights"] = weights
