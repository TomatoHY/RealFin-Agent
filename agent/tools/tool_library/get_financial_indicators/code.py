import re

import akshare as ak
import pandas as pd

from typing import Optional, Any

from ..get_code_from_name.code import get_code_from_name
from ..utils import _log_debug, _financial_indicators_cache


def get_financial_indicators(
report_date: str,
    item_name: str,
    name: Optional[str] = None,
    code: Optional[str] = None
) -> Optional[Any]:
    symbol_from_input = code if code else get_code_from_name(name)
    if not symbol_from_input: return f"错误: 无法找到代码 for '{name or code}'."
    
    symbol = re.sub(r'\D', '', str(symbol_from_input))
    if re.match(r'^6', symbol): prefixed_symbol = f"{symbol}.SH"
    elif re.match(r'^[03]', symbol): prefixed_symbol = f"{symbol}.SZ"
    elif re.match(r'^[48]', symbol): prefixed_symbol = f"{symbol}.BJ"
    else: prefixed_symbol = symbol 
    try:
        if prefixed_symbol not in _financial_indicators_cache:
            _log_debug(f"缓存未命中，为代码'{prefixed_symbol}'下载所有历史财务指标...")
            df = ak.stock_financial_analysis_indicator_em(symbol=prefixed_symbol, indicator="按报告期")
            _financial_indicators_cache[prefixed_symbol] = df if isinstance(df, pd.DataFrame) else None
            _log_debug("数据缓存成功。")
        df = _financial_indicators_cache[prefixed_symbol]
        if df is None: return f"错误: 未能获取代码'{prefixed_symbol}'的财务指标数据。"
        df_copy = df.copy()
        df_copy['REPORT_DATE'] = pd.to_datetime(df_copy['REPORT_DATE']).dt.strftime('%Y-%-m-%d')
        result_row = df_copy[df_copy['REPORT_DATE'] == report_date]
        if result_row.empty:
            available_dates = df_copy['REPORT_DATE'].unique().tolist()
            return f"查询失败: 未找到报告期为 '{report_date}' 的财务指标数据。可用报告期示例: {available_dates[:5]}..."
        if item_name not in result_row.columns:
            available_items = result_row.columns.tolist()
            return f"查询失败: 指标 '{item_name}' 不存在。可用指标示例: {available_items[:10]}..."
        value = result_row.iloc[0][item_name]
        if pd.isna(value):
            value_display = None
        else:
            value_display = value
        result_json = {
            "stock_identifier": name or symbol_from_input,
            "report_date": report_date,
            "data_source": "Financial Indicators",
            "item_name": item_name,
            "value": value_display
        }
        return result_json
    except Exception as e:
        return f"查询财务指标时出错: {e}"
