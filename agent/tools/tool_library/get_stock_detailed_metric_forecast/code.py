import re

import akshare as ak
import pandas as pd

from typing import Optional, Any

from ..get_code_from_name import get_code_from_name
from ..utils import _log_debug, _parse_chinese_number_unit, _ths_forecast_cache


def get_stock_detailed_metric_forecast(
metric_name: str,
    year: int,
    name: Optional[str] = None,
    code: Optional[str] = None,
) -> Any:
    """
    从同花顺查询A股未来特定年份的【详细财务指标预测】平均值。
    """
    global _ths_forecast_cache
    if not code and not name: return "错误: 必须提供股票代码或名称。"
    symbol_from_input = code if code else get_code_from_name(name)
    if not symbol_from_input: return f"错误: 无法找到代码 for '{name or code}'."
    symbol = re.sub(r'\D', '', str(symbol_from_input))
    indicator = "业绩预测详表-详细指标预测"
    try:
        cache_key = (symbol, indicator)
        if cache_key not in _ths_forecast_cache:
            _log_debug(f"缓存未命中，为代码'{symbol}'下载详细指标预测数据...")
            df = ak.stock_profit_forecast_ths(symbol=symbol, indicator=indicator)
            if isinstance(df, pd.DataFrame) and not df.empty:
                df.set_index('预测指标', inplace=True)
                _ths_forecast_cache[cache_key] = df
            else: 
                _ths_forecast_cache[cache_key] = None
            _log_debug("数据缓存成功。")
        df = _ths_forecast_cache[cache_key]
        if df is None: return f"错误: 未能获取代码'{symbol}'的详细指标预测数据。"
        column_name = f"预测{year}-平均"
        if metric_name not in df.index or column_name not in df.columns:
            return f"查询失败: 未找到指标'{metric_name}'或年份'{year}'的预测记录。"
        raw_value = df.loc[metric_name, column_name]
        final_value, unit = _parse_chinese_number_unit(raw_value)
        result_json = {
            "stock_identifier": name or symbol_from_input,
            "forecast_year": year,
            "data_source": "详细财务指标预测 (同花顺)",
            "requested_metric": {
                "name": metric_name,
                "value_type": "平均值",
                "value": final_value,
                "unit": unit
            }
        }
        return result_json
    except KeyError: return f"查询失败: 未找到指标'{metric_name}'或年份'{year}'的预测记录。"
    except Exception as e: return f"查询详细指标预测时出错: {e}"
