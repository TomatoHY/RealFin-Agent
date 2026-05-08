import re

import akshare as ak
import pandas as pd

from typing import Optional

from ..get_code_from_name.code import get_code_from_name
from ..utils import _log_debug


def get_a_dividend_payout(
report_date: str,
    name: Optional[str] = None,
    code: Optional[str] = None
) -> Optional[str]:
    """
    查询并获取A股上市公司在特定报告期的【分红方案说明】。

    Args:
        report_date (str): 查询的报告期，格式如 "2023年报", "2024中报"。
        name (Optional[str]): 股票的中文名称。
        code (Optional[str]): 股票的6位数字代码。

    Returns:
        Optional[str]: 查询到的"分红方案说明"文本，如果查询失败则返回 None。
    """
    if not code and not name:
        _log_debug(f"错误：必须提供股票代码 (code) 或股票名称 (name)。")
        return None
    symbol_with_prefix = code if code else get_code_from_name(name)
    if not symbol_with_prefix:
        _log_debug(f"错误：未能通过名称 '{name}' 找到对应的股票代码。")
        return None
    symbol = re.sub(r'^[a-zA-Z]+', '', symbol_with_prefix)
    try:
        if symbol not in _a_dividend_payout_cache:
            _log_debug(f"缓存未命中，为代码'{symbol}'下载分红派息记录...")
            payout_df = ak.stock_fhps_detail_ths(symbol=symbol)
            if payout_df is None or payout_df.empty:
                _log_debug(f"错误：未能获取到代码 '{symbol}' 的分红记录。")
                _a_dividend_payout_cache[symbol] = pd.DataFrame()
                return None
            _a_dividend_payout_cache[symbol] = payout_df
            _log_debug("分红记录缓存成功。")
        df = _a_dividend_payout_cache[symbol]
        if df.empty:
            return None
        result_row = df[df['报告期'] == report_date]
        if result_row.empty:
            _log_debug(f"查询失败: 未找到报告期为 '{report_date}' 的分红记录。")
            return None
        dividend_description = str(result_row.iloc[0]["分红方案说明"])
        implementation_date = str(result_row.iloc[0].get("实施日期", "N/A")) 
        ex_dividend_date = str(result_row.iloc[0].get("除权除息日", "N/A"))
        result_json = {
            "stock_identifier": name or symbol_with_prefix,
            "report_date": report_date,
            "dividend_plan": {
                "description": dividend_description,
                "implementation_date": implementation_date,
                "ex_dividend_date": ex_dividend_date
            }
        }
        return result_json
    except KeyError:
        _log_debug(f"内部错误：预期的列 '分红方案说明' 在数据源中不存在。可用字段: {df.columns.tolist()}")
        return None
    except Exception as e:
        _log_debug(f"获取或处理数据时发生严重错误: {e}")
        return None
