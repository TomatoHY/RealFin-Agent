import re

import akshare as ak
import pandas as pd

from typing import Optional, Any

from ..get_code_from_name.code import get_code_from_name
from ..utils import _log_debug, _earnings_report_cache


def get_earnings_report_summary(
date: str, column_label: str, name: Optional[str] = None, code: Optional[str] = None
) -> Optional[Any]:
    """
    查询A股公司在特定报告期的业绩报表摘要。
    
    :param date: 要查询的财报报告期，格式 'YYYY-MM-DD' 或 'YYYYMMDD'。
    :param column_label: 要查询的指标名称，例如 "营业总收入-同比增长"。
    :param name: [可选] 股票的中文名称。
    :param code: [可选] 股票的6位数字代码。
    :return: 返回查询到的具体数值或错误信息。
    """
    global _earnings_report_cache
    symbol = code if code else get_code_from_name(name, market='a')
    if not symbol: return f"错误: 无法找到代码 for '{name or code}'."
    symbol = re.sub(r'\D', '', str(symbol))
    if not (isinstance(symbol, str) and len(symbol) == 6):
        return f"错误: 股票标识 '{symbol}' 非标准A股代码格式。"
    formatted_date = date.replace('-', '')
    try:
        if formatted_date not in _earnings_report_cache:
            _log_debug(f"缓存未命中，为报告期'{formatted_date}'下载业绩报表...")
            df = ak.stock_yjbb_em(date=formatted_date)
            if df is None or df.empty:
                return f"错误: 未能获取报告期'{formatted_date}'的业绩报表数据。该日期可能非有效财报日。"
            _earnings_report_cache[formatted_date] = df 
            _log_debug("数据缓存成功。")
        df = _earnings_report_cache[formatted_date]
        stock_row = df[df['股票代码'] == symbol]
        if stock_row.empty: 
            return f"查询失败: 在报告期'{formatted_date}'的业绩报表中未找到股票'{symbol}'的数据。"
        if column_label not in stock_row.columns:
            available_cols_sample = ", ".join(stock_row.columns.tolist())
            return f"错误: 指标 '{column_label}' 不存在。可用指标包括: {available_cols_sample}。"
        value = float(stock_row.iloc[0][column_label])
        stock_name_from_data = stock_row.iloc[0].get("股票简称", name)
        if pd.isna(value):
            value_display = None
        else:
            if '同比增长' in column_label or '增长率' in column_label:
                value_display = f"{value:.2f}%"
            else:
                value_display = value
        result_json = {
            "stock_code": symbol,
            "stock_name": stock_name_from_data,
            "report_date": date,
            "financial_statement": "Earnings Report Summary",
            "item_name": column_label,
            "value": value_display
        }
        return result_json
    except Exception as e:
        return f"查询业绩报表时出错: {e}"
