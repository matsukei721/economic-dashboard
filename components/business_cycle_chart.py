"""景気動向指数グラフコンポーネント。"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from loguru import logger


def render_business_cycle_chart(df: pd.DataFrame, config: dict) -> None:
    """景気動向指数（CI）折れ線グラフとサマリー統計を描画する。

    Args:
        df: date列とci列を持つDataFrame（月次）
        config: chart設定辞書（business_cycle_color, height, template を含む）
    """
    if df.empty:
        st.warning("景気動向指数データがありません。")
        logger.warning("景気動向指数グラフの描画をスキップ: データなし")
        return

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["ci"],
            mode="lines",
            name="景気動向指数（CI）",
            line=dict(color=config["business_cycle_color"], width=1.5),
            hovertemplate="<b>%{x|%Y年%m月}</b><br>CI: %{y:.1f}<extra></extra>",
        )
    )

    # 景気判断の基準線
    fig.add_hline(
        y=100,
        line_dash="dash",
        line_color="gray",
        annotation_text="基準値（100）",
        annotation_position="bottom right",
    )

    fig.update_layout(
        title="景気動向指数（CI）の推移",
        xaxis_title="年月",
        yaxis_title="CI値",
        height=config["height"],
        template=config["template"],
        hovermode="x unified",
        showlegend=True,
    )

    st.plotly_chart(fig, use_container_width=True)

    # サマリー指標
    latest = df["ci"].iloc[-1]
    col1, col2, col3 = st.columns(3)
    col1.metric("最新値", f"{latest:.1f}")
    col2.metric("期間最大", f"{df['ci'].max():.1f}")
    col3.metric("期間最小", f"{df['ci'].min():.1f}")
