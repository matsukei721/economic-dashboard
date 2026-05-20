"""景気動向指数（CI）データ取得モジュール。

e-Stat API（内閣府）から一致指数を取得する。
APIキーは環境変数 ESTAT_API_KEY で設定すること。
APIキー取得: https://api.e-stat.go.jp/

取得失敗時はサンプルデータにフォールバックする。
"""

import os
from typing import Optional

import numpy as np
import pandas as pd
import requests
from loguru import logger

ESTAT_BASE_URL = "https://api.e-stat.go.jp/rest/3.0/app/json/getStatsData"


def _parse_estat_time(time_str: str) -> Optional[pd.Timestamp]:
    """e-Stat APIの時刻文字列をTimestampに変換する。

    月次データは "YYYYMM000000" 形式。

    Args:
        time_str: e-Stat の時刻コード文字列

    Returns:
        変換したTimestamp。解析失敗時はNone。
    """
    try:
        year = int(time_str[:4])
        # e-Statの月次コードは "YYYY00MMDD" 形式（例: "1980000101" = 1980年1月）
        month = int(time_str[6:8])
        return pd.Timestamp(year=year, month=month, day=1)
    except (ValueError, IndexError):
        return None


def _fetch_from_estat(config: dict) -> Optional[pd.DataFrame]:
    """e-Stat APIから景気動向指数（CI）を取得する。

    Args:
        config: business_cycle設定辞書

    Returns:
        date列とci列を持つDataFrame。失敗時はNone。
    """
    api_key = os.getenv("ESTAT_API_KEY")
    if not api_key:
        logger.warning("ESTAT_API_KEY が設定されていません。サンプルデータを使用します。")
        return None

    params: dict[str, str | int] = {
        "appId": api_key,
        "statsDataId": config["stats_data_id"],
        "metaGetFlg": "N",
        "cntGetFlg": "N",
        "limit": 10000,
    }
    if cat01 := config.get("cat01"):
        params["cdCat01"] = cat01
    if tab := config.get("tab"):
        params["cdTab"] = tab

    try:
        logger.info(f"e-Stat APIから景気動向指数を取得: statsDataId={config['stats_data_id']}")
        response = requests.get(ESTAT_BASE_URL, params=params, timeout=20)
        response.raise_for_status()
        body = response.json()

        result_status = (
            body.get("GET_STATS_DATA", {}).get("RESULT", {}).get("STATUS", -1)
        )
        if result_status != 0:
            error_msg = body["GET_STATS_DATA"]["RESULT"].get("ERROR_MSG", "不明なエラー")
            logger.error(f"e-Stat APIエラー: {error_msg}")
            return None

        values = (
            body["GET_STATS_DATA"]["STATISTICAL_DATA"]["DATA_INF"]["VALUE"]
        )

        records = []
        for v in values:
            ts = _parse_estat_time(v.get("@time", ""))
            raw_value = v.get("$")
            if ts is not None and raw_value not in (None, "-", ""):
                try:
                    records.append({"date": ts, "ci": float(raw_value)})
                except ValueError:
                    continue

        if not records:
            logger.warning("e-Statから有効なデータが取得できませんでした")
            return None

        start_year: int = config.get("start_year", 2000)
        df = (
            pd.DataFrame(records)
            .sort_values("date")
            .reset_index(drop=True)
        )
        df = df[df["date"].dt.year >= start_year]
        logger.info(f"e-Stat 景気動向指数取得完了: {len(df)}件")
        return df

    except requests.exceptions.Timeout:
        logger.error("e-Stat APIリクエストがタイムアウトしました")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"e-Stat APIリクエスト失敗: {e}")
        return None
    except (KeyError, ValueError) as e:
        logger.error(f"e-Statデータの解析に失敗しました: {e}")
        return None


def _generate_sample_data(start_year: int, end_year: int = 2024) -> pd.DataFrame:
    """歴史的なパターンを模した景気動向指数サンプルデータを生成する。

    Args:
        start_year: 開始年
        end_year: 終了年

    Returns:
        date列とci列を持つDataFrame（月次）
    """
    dates = pd.date_range(start=f"{start_year}-01", end=f"{end_year}-12", freq="MS")
    n = len(dates)

    rng = np.random.default_rng(42)
    trend = np.linspace(97.0, 103.0, n)
    cycle = 5.0 * np.sin(np.linspace(0, 10 * np.pi, n))
    noise = rng.normal(0, 0.8, n)
    ci = trend + cycle + noise

    def _apply_shock(
        arr: np.ndarray, year: int, month_start: int, month_end: int, magnitude: float
    ) -> np.ndarray:
        idx_start = (year - start_year) * 12 + month_start
        idx_end = (year - start_year) * 12 + month_end
        if 0 <= idx_start < n and idx_end <= n:
            arr[idx_start:idx_end] -= magnitude
        return arr

    if start_year <= 2001 <= end_year:
        ci = _apply_shock(ci, 2001, 3, 9, 5.0)
    if start_year <= 2008 <= end_year:
        ci = _apply_shock(ci, 2008, 9, 12, 10.0)
    if start_year <= 2009 <= end_year:
        ci = _apply_shock(ci, 2009, 0, 6, 8.0)
    if start_year <= 2020 <= end_year:
        ci = _apply_shock(ci, 2020, 2, 8, 12.0)

    return pd.DataFrame({"date": dates, "ci": ci.round(1)})


def fetch_business_cycle_data(config: dict) -> pd.DataFrame:
    """景気動向指数（CI）データを取得する。

    e-Stat API を優先し、失敗時はサンプルデータにフォールバックする。

    Args:
        config: business_cycle設定辞書

    Returns:
        date列とci列を持つDataFrame（月次）
    """
    source: str = config.get("source", "sample")
    start_year: int = config.get("start_year", 2000)

    if source == "estat":
        df = _fetch_from_estat(config)
        if df is not None and not df.empty:
            return df
        logger.warning("e-Statからの取得に失敗。サンプルデータにフォールバックします。")

    logger.info(f"サンプルデータを生成: {start_year}年〜")
    return _generate_sample_data(start_year)
