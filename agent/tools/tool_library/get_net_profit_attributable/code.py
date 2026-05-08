import re

import akshare as ak
import pandas as pd

from typing import Optional

from ..get_code_from_name import get_code_from_name
from ..utils import _log_debug, _financial_abstract_cache


def get_net_profit_attributable(
    date: str,
    name: Optional[str] = None,
    code: Optional[str] = None
) -> Optional[float]:
    """
    查询指定公司在特定报告期的【归母净利润】（单位：元）。
    数据来源于新浪财经-财务报表-关键指标。

    Args:
        date (str): 要查询的具体报告期，格式应为 'YYYY-MM-DD'，例如 '2022-09-30'。
        name (Optional[str]): 股票的中文名称，例如 '白云机场'。
        code (Optional[str]): 股票的6位数字代码，例如 '600004'。

    Returns:
        Optional[float]: 查询到的归母净利润金额（元）。如果查询失败则返回 None。
    """
    global _financial_abstract_cache
    if not code and not name:
        _log_debug(f"错误：必须提供股票代码 (code) 或股票名称 (name)。")
        return None
    symbol_with_prefix = code if code else get_code_from_name(name)
    if not symbol_with_prefix:
        _log_debug(f"错误：未能通过名称 '{name}' 找到对应的股票代码。")
        return None
    symbol = re.sub(r'^[a-zA-Z]+', '', symbol_with_prefix)
    try:
        if symbol not in _financial_abstract_cache:
            _log_debug(f"缓存未命中，为代码'{symbol}'下载关键指标全量数据...")
            abstract_df = ak.stock_financial_abstract(symbol=symbol)
            if abstract_df is None or abstract_df.empty:
                _log_debug(f"错误：未能获取到代码 '{symbol}' 的关键指标数据。")
                _financial_abstract_cache[symbol] = pd.DataFrame()
                return None
            _financial_abstract_cache[symbol] = abstract_df
            _log_debug("数据下载并缓存成功。")
        df = _financial_abstract_cache[symbol]
        if df.empty:
            return None
        column_date = date.replace('-', '')
        if column_date not in df.columns:
            return f"查询失败：数据源中不存在报告期为 '{date}' ({column_date}) 的数据列。"
        profit_row = df[df['指标'] == '归母净利润']
        if profit_row.empty:
            return "查询失败：在返回的数据中未找到 '归母净利润' 这一指标。"
        value = profit_row.iloc[0][column_date]
        if pd.isna(value):
            return f"数据缺失：'{symbol}' 在 '{date}' 的归母净利润数据为空。"
        result_json = {
            "stock_identifier": name or symbol_with_prefix,
            "report_date": date,
            "financial_statement": "Financial Abstract",
            "item_name": "归母净利润",
            "value": float(value),
            "unit": "元"
        }
        return result_json
    except Exception as e:
        return f"处理数据时发生未知错误: {e}"
