"""景気動向指数（CI）データ取得モジュール。

現在はサンプルデータを生成して返す。
実際のデータは内閣府 e-Stat API や内閣府公開CSVから取得可能。
参考: https://www.esri.cao.go.jp/jp/stat/di/di.html
"""

import numpy as np
import pandas as pd
from loguru import logger


def _generate_sample_data(start_year: int, end_year: int) -> pd.DataFrame:
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

    # 基準値100を中心とした緩やかなトレンド + 景気循環 + ノイズ
    trend = np.linspace(97.0, 103.0, n)
    cycle = 5.0 * np.sin(np.linspace(0, 10 * np.pi, n))
    noise = rng.normal(0, 0.8, n)
    ci = trend + cycle + noise

    def _apply_shock(
        arr: np.ndarray, year: int, month_start: int, month_end: int, magnitude: float
    ) -> np.ndarray:
        """特定期間に景気後退ショックを適用する。"""
        idx_start = (year - start_year) * 12 + month_start
        idx_end = (year - start_year) * 12 + month_end
        if 0 <= idx_start < n and idx_end <= n:
            arr[idx_start:idx_end] -= magnitude
        return arr

    # ITバブル崩壊 (2001)
    if start_year <= 2001 <= end_year:
        ci = _apply_shock(ci, 2001, 3, 9, 5.0)

    # リーマンショック (2008-2009)
    if start_year <= 2008 <= end_year:
        ci = _apply_shock(ci, 2008, 9, 12, 10.0)
    if start_year <= 2009 <= end_year:
        ci = _apply_shock(ci, 2009, 0, 6, 8.0)

    # コロナショック (2020)
    if start_year <= 2020 <= end_year:
        ci = _apply_shock(ci, 2020, 2, 8, 12.0)

    return pd.DataFrame({"date": dates, "ci": ci.round(1)})


def fetch_business_cycle_data(config: dict) -> pd.DataFrame:
    """景気動向指数（CI）データを取得する。

    Args:
        config: business_cycle設定辞書（source, start_year, end_year を含む）

    Returns:
        date列とci列を持つDataFrame（月次）
    """
    source: str = config.get("source", "sample")
    start_year: int = config.get("start_year", 1990)
    end_year: int = config.get("end_year", 2024)

    if source == "sample":
        logger.info(f"景気動向指数サンプルデータを生成: {start_year}年〜{end_year}年")
        df = _generate_sample_data(start_year, end_year)
        logger.info(f"景気動向指数データ生成完了: {len(df)}件")
        return df

    # 将来的なAPI連携の拡張ポイント
    logger.warning(f"未対応のソース: {source}。サンプルデータにフォールバックします。")
    return _generate_sample_data(start_year, end_year)
