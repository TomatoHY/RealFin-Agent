import re

import akshare as ak
import pandas as pd

from typing import Optional, Any

from ..get_code_from_name.code import get_code_from_name
from ..utils import _log_debug, _balance_sheet_cache


def get_balance_sheet(
date: str, item_name: str, name: Optional[str] = None, code: Optional[str] = None
) -> Optional[Any]:
    """
    查询A股公司资产负债表数据。
    """
    global _balance_sheet_cache
    symbol = code if code else get_code_from_name(name)
    if not symbol: return f"错误: 无法找到代码 for '{name or code}'."
    match = re.search(r'\d{6}', str(symbol))
    if match:
        symbol = match.group(0)
    else:
        symbol = str(symbol)
    if not (isinstance(symbol, str) and symbol.isdigit() and len(symbol) == 6):
        return f"错误: 工具 'get_balance_sheet' 仅适用于中国A股（6位数字代码）。'{symbol}' 似乎不是一个有效的A股代码。"
    formatted_date = date.replace('-', '')
    try:
        if formatted_date not in _balance_sheet_cache:
            _log_debug(f"缓存未命中，为报告期'{formatted_date}'下载资产负债表...")
            df = None 
            try:
                if re.match(r'^[48]', symbol):
                    df = ak.stock_zcfz_bj_em(date=formatted_date)
                else:
                    df = ak.stock_zcfz_em(date=formatted_date)
            except Exception as ak_error:
                _log_debug(f"警告: 调用akshare接口时直接发生错误: {ak_error}")
            if df is None or df.empty or '股票代码' not in df.columns:
                _log_debug(f"警告: akshare接口在查询日期'{formatted_date}'时返回了无效数据(None, empty, or missing key columns)。")
            else:
                _balance_sheet_cache[formatted_date] = df
                _log_debug("数据缓存成功。")
        df = _balance_sheet_cache[formatted_date]
        if df.empty:
            return f"错误: 未能获取报告期'{formatted_date}'的资产负债表数据，该日期可能非财报日或无数据。"
        stock_row = df[df['股票代码'] == symbol]
        if stock_row.empty:
            return f"查询失败: 在报告期'{formatted_date}'内未找到股票'{symbol}'的数据。"
        if item_name not in stock_row.columns:
            available_cols_sample = ", ".join(stock_row.columns[:5].tolist())
            return f"错误: 指标 '{item_name}' 不存在于财报中。可用指标示例: {available_cols_sample}..."
        value = stock_row.iloc[0][item_name]
        if pd.isna(value):
            value_display = None
        else:
            value_display = value
        result_json = {
            "stock_code": symbol,
            "stock_name": str(stock_row.iloc[0].get("股票简称", name)), 
            "report_date": date, 
            "financial_statement": "Balance Sheet",
            "item_name": item_name,
            "value": value_display,
            "unit": "元"
        }
        return result_json
    except Exception as e:
        return f"查询资产负债表时发生意外错误: {e}"
