"""CPIグラフコンポーネント。"""

from typing import Optional

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from loguru import logger


def render_cpi_chart(df: Optional[pd.DataFrame], config: dict) -> None:
    """CPI折れ線グラフとサマリー統計を描画する。

    Args:
        df: year列とcpi列を持つDataFrame。Noneまたは空の場合はエラー表示。
        config: chart設定辞書（cpi_color, height, template を含む）
    """
    if df is None or df.empty:
        st.error("CPIデータが取得できませんでした。ネットワーク接続を確認してください。")
        logger.warning("CPIグラフの描画をスキップ: データなし")
        return

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["year"],
            y=df["cpi"],
            mode="lines+markers",
            name="CPI（日本）",
            line=dict(color=config["cpi_color"], width=2),
            marker=dict(size=5),
            hovertemplate="<b>%{x}年</b><br>CPI: %{y:.1f}<extra></extra>",
        )
    )

    fig.update_layout(
        title="消費者物価指数（CPI）の推移",
        xaxis_title="年",
        yaxis_title="CPI（2010年=100）",
        height=config["height"],
        template=config["template"],
        hovermode="x unified",
        showlegend=True,
    )

    st.plotly_chart(fig, use_container_width=True)

    # サマリー指標
    latest = df["cpi"].iloc[-1]
    prev = df["cpi"].iloc[-2] if len(df) >= 2 else latest
    col1, col2, col3 = st.columns(3)
    col1.metric("最新値", f"{latest:.1f}", f"{latest - prev:+.1f}")
    col2.metric("期間最大", f"{df['cpi'].max():.1f}")
    col3.metric("期間最小", f"{df['cpi'].min():.1f}")
