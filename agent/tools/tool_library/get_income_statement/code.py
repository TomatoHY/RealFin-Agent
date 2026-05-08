import re

import akshare as ak
import pandas as pd

from typing import Optional, Any

from ..get_code_from_name import get_code_from_name
from ..utils import _log_debug, _income_statement_cache


def get_income_statement(
date: str, item_name: str, name: Optional[str] = None, code: Optional[str] = None
) -> Optional[Any]:
    """查询A股公司在特定报告期的【利润表】中的单个科目金额。"""
    global _income_statement_cache
    symbol = code if code else get_code_from_name(name)
    if not symbol: return f"错误: 无法找到代码 for '{name or code}'."
    symbol = re.sub(r'\D', '', str(symbol))
    formatted_date = date.replace('-', '')
    try:
        if formatted_date not in _income_statement_cache:
            _log_debug(f"缓存未命中，为报告期'{formatted_date}'下载利润表...")
            df = ak.stock_lrb_em(date=formatted_date)
            _income_statement_cache[formatted_date] = df if not df.empty else pd.DataFrame()
            _log_debug("数据缓存成功。")
        df = _income_statement_cache[formatted_date]
        if df.empty: return f"错误: 未能获取报告期'{formatted_date}'的利润表数据。"
        stock_row = df[df['股票代码'] == symbol]
        if stock_row.empty: return f"查询失败: 在该报告期未找到股票'{symbol}'的数据。"
        if item_name not in stock_row.columns:
            available_items = stock_row.columns.tolist()
            return f"查询失败: 指标 '{item_name}' 不存在。可用指标示例: {available_items[:10]}..."
        value = stock_row.iloc[0][item_name]
        stock_name_from_data = stock_row.iloc[0].get("股票简称", name)
        if pd.isna(value):
            value_display = None
        else:
            value_display = value
        result_json = {
            "stock_code": symbol,
            "stock_name": stock_name_from_data,
            "report_date": date,
            "financial_statement": "Income Statement",
            "item_name": item_name,
            "value": value_display,
            "unit": "元" 
        }
        return result_json
    except Exception as e:
        return f"查询利润表时出错: {e}"
