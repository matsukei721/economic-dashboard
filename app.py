"""経済指標ダッシュボード エントリーポイント。

実行方法:
    uv run streamlit run app.py
"""

from pathlib import Path
from typing import Any

import streamlit as st
import yaml
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

from components.business_cycle_chart import render_business_cycle_chart
from components.cpi_chart import render_cpi_chart
from data.business_cycle import fetch_business_cycle_data
from data.cpi import fetch_cpi_data

CONFIG_PATH = Path("config.yaml")


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    """設定ファイルを読み込む。

    Args:
        path: config.yamlのパス

    Returns:
        設定辞書

    Raises:
        FileNotFoundError: config.yamlが存在しない場合
    """
    if not path.exists():
        raise FileNotFoundError(f"設定ファイルが見つかりません: {path}")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def main() -> None:
    """メインアプリケーション。"""
    try:
        config = load_config()
    except FileNotFoundError as e:
        st.error(str(e))
        logger.critical(e)
        return

    st.set_page_config(
        page_title=config["app"]["title"],
        layout=config["app"]["layout"],
    )

    st.title(config["app"]["title"])
    st.markdown(
        "消費者物価指数（CPI）と景気動向指数のトレンドを可視化します。"
        "　CPIは [World Bank API](https://data.worldbank.org/) から取得、"
        "景気動向指数は [e-Stat（内閣府）](https://www.e-stat.go.jp/) から取得しています。"
    )

    # サイドバー設定
    st.sidebar.header("表示設定")
    display_years: int = st.sidebar.slider(
        "CPIの表示年数",
        min_value=5,
        max_value=30,
        value=config["worldbank"].get("default_years", 20),
        step=1,
    )

    # データ取得
    with st.spinner("データを取得中..."):
        cpi_df = fetch_cpi_data(config["worldbank"], years=display_years)
        bc_df = fetch_business_cycle_data(config["business_cycle"])

    # タブ切り替えで表示
    tab_cpi, tab_bc = st.tabs(["消費者物価指数（CPI）", "景気動向指数（CI）"])

    with tab_cpi:
        render_cpi_chart(cpi_df, config["chart"])
        if cpi_df is not None and not cpi_df.empty:
            with st.expander("データ詳細"):
                st.dataframe(cpi_df, use_container_width=True)

    with tab_bc:
        render_business_cycle_chart(bc_df, config["chart"])
        with st.expander("データ詳細"):
            st.dataframe(bc_df, use_container_width=True)


if __name__ == "__main__":
    main()
