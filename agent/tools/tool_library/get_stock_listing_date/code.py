import akshare as ak
import pandas as pd

from typing import Optional

from ..get_code_from_name import get_code_from_name
from ..utils import _log_debug


def get_stock_listing_date(
    name: Optional[str] = None,
    code: Optional[str] = None
) -> str:
    """
    【信息检索工具】查询单只A股股票的上市时间。
    函数既可以接收股票代码(code)，也可以接收股票名称(name)作为输入。

    :param name: (可选) 股票的中文名称, 例如 "万科A"。
    :param code: (可选) 股票的代码, 例如 "000002"。name和code至少需要提供一个。
    :return: 股票的上市日期(格式 'YYYY-MM-DD'), 或者一个描述性的错误信息字符串。
    """
    _log_debug(f"--- [上市日期查询] 正在查询 '{name or code}' 的上市时间... ---")
    if not code and not name:
        error_message = "错误：必须提供股票代码 (code) 或股票名称 (name)。"
        _log_debug(f"--- [上市日期查询] {error_message} ---")
        return error_message # <-- 2. 修改点
    symbol = code
    if not symbol and name:
        _log_debug(f"--- [上市日期查询] 代码缺失, 正在通过名称 '{name}' 查找A股代码... ---")
        symbol = get_code_from_name(name=name, market='a') 
        if not symbol:
            error_message = f"错误：未能通过名称 '{name}' 找到对应的A股股票代码。"
            _log_debug(f"--- [上市日期查询] {error_message} ---")
            return error_message 
    symbol_cleaned = ''.join(filter(str.isdigit, str(symbol)))
    if not symbol_cleaned:
        error_message = f"错误：提供的代码 '{symbol}' 无效。"
        _log_debug(f"--- [上市日期查询] {error_message} ---")
        return error_message
    try:
        _log_debug(f"--- [上市日期查询] 正在调用API获取代码 '{symbol_cleaned}' 的详细信息... ---")
        info_df = ak.stock_individual_info_em(symbol=symbol_cleaned)
        if info_df.empty:
            error_message = f"错误：API未能返回代码 '{symbol_cleaned}' 的任何信息（可能是无效代码）。"
            _log_debug(f"--- [上市日期查询] {error_message} ---")
            return error_message
        info_dict = dict(zip(info_df['item'], info_df['value']))
        listing_date_str = info_dict.get('上市时间')
        if listing_date_str:
            listing_date = pd.to_datetime(str(listing_date_str), format='%Y%m%d').strftime('%Y-%m-%d')
            _log_debug(f"--- [上市日期查询] 成功找到 '{name or code}' 的上市时间: {listing_date} ---")
            return listing_date
        else:
            error_message = f"错误：在返回的数据中未能找到 '{name or code}' (代码: {symbol_cleaned}) 的上市时间字段。"
            _log_debug(f"--- [上市日期查询] {error_message} ---")
            return error_message 
    except Exception as e:
        error_message = f"错误：在为 '{name or code}' (代码: {symbol_cleaned}) 查询上市时间时发生API或处理错误: {e}"
        _log_debug(f"--- [上市日期查询] {error_message} ---")
        return error_message
