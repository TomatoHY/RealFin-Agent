import re

import akshare as ak
import pandas as pd

from typing import Optional, Any

from ..get_code_from_name import get_code_from_name
from ..utils import _log_debug, _ths_forecast_cache


def get_stock_consensus_forecast(
    metric: str,
    value_type: str,
    year: int,
    name: Optional[str] = None,
    code: Optional[str] = None,
) -> Any:
    """
    从同花顺查询指定A股在特定年度的【盈利预测】汇总数据。
    支持通过股票名称或代码查询，并使用缓存。
    """
    global _ths_forecast_cache
    if not code and not name: return "错误: 必须提供股票代码或名称。"
    symbol_from_input = code if code else get_code_from_name(name)
    if not symbol_from_input: return f"错误: 无法找到代码 for '{name or code}'."
    symbol = re.sub(r'\D', '', str(symbol_from_input))
    indicator_map = {"每股收益": "预测年报每股收益", "净利润": "预测年报净利润"}
    if metric not in indicator_map: return f"错误: 指标'{metric}'不受支持。"
    indicator = indicator_map[metric]
    try:
        cache_key = (symbol, indicator)
        if cache_key not in _ths_forecast_cache:
            _log_debug(f"缓存未命中，为代码'{symbol}'下载'{metric}'预测数据...")
            df = ak.stock_profit_forecast_ths(symbol=symbol, indicator=indicator)
            if isinstance(df, pd.DataFrame) and not df.empty:
                df['年度'] = pd.to_numeric(df['年度'], errors='coerce')
                df.set_index('年度', inplace=True)
                _ths_forecast_cache[cache_key] = df
            else: _ths_forecast_cache[cache_key] = None
            _log_debug("数据缓存成功。")
        df = _ths_forecast_cache[cache_key]
        if df is None: return f"错误: 未能获取代码'{symbol}'的'{metric}'预测数据。"
        if year not in df.index:
            raise KeyError(f"年份 '{year}'")
        if value_type not in df.columns:
            raise KeyError(f"数值类型 '{value_type}'")
        result = df.loc[year, value_type]
        unit = ""
        final_value = result
        if metric == "净利润":
            final_value = result * 100000000 
            unit = "元"
        elif metric == "每股收益":
            unit = "元/股"
        result_json = {
            "stock_identifier": name or symbol_from_input,
            "forecast_year": year,
            "data_source": "盈利预测 (同花顺)",
            "requested_metric": {
                "metric_type": metric,
                "value_type": value_type,
                "value": final_value,
                "unit": unit
            }
        }
        return result_json
    except KeyError: return f"查询失败: 未找到'{year}'年度的预测记录。"
    except Exception as e: return f"查询盈利预测时出错: {e}"
