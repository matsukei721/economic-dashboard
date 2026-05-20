"""消費者物価指数（CPI）データ取得モジュール。

World Bank の公開API（認証不要）から日本のCPIデータを取得する。
API仕様: https://datahelpdesk.worldbank.org/knowledgebase/articles/889392
"""

from typing import Optional

import pandas as pd
import requests
from loguru import logger


def fetch_cpi_data(config: dict, years: int = 20) -> Optional[pd.DataFrame]:
    """World Bank APIから日本のCPIデータを取得する。

    Args:
        config: worldbank設定辞書（base_url, country, cpi_indicator を含む）
        years: 取得する年数（直近N年分）

    Returns:
        year列とcpi列を持つDataFrame。取得失敗時はNone。
    """
    url = (
        f"{config['base_url']}/country/{config['country']}"
        f"/indicator/{config['cpi_indicator']}"
    )
    params: dict[str, str | int] = {
        "format": "json",
        "per_page": years,
        "mrv": years,
    }

    try:
        logger.info(f"CPI データ取得開始: country={config['country']}, years={years}")
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        # APIレスポンスは [メタデータ, データ配列] の構造
        if len(data) < 2 or data[1] is None:
            logger.warning("APIレスポンスにデータが含まれていません")
            return None

        records = [
            {"year": int(r["date"]), "cpi": r["value"]}
            for r in data[1]
            if r.get("value") is not None
        ]

        if not records:
            logger.warning("有効なCPIデータが見つかりません")
            return None

        df = pd.DataFrame(records).sort_values("year").reset_index(drop=True)
        logger.info(f"CPIデータ取得完了: {len(df)}件")
        return df

    except requests.exceptions.Timeout:
        logger.error("CPI APIリクエストがタイムアウトしました")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"CPI APIリクエスト失敗: {e}")
        return None
    except (KeyError, ValueError, IndexError) as e:
        logger.error(f"CPIデータの解析に失敗しました: {e}")
        return None
