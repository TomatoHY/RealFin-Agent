import re

import akshare as ak

from typing import Optional, Any

from ..utils import _log_debug


def get_stock_basic_info_a(
symbol: str, item_name: str
) -> Optional[Any]:
    """
    从东方财富获取指定A股股票的基础信息中的单个字段值。

    Args:
        symbol (str): 要查询的A股代码。支持两种格式: 
                    1. 纯6位数字代码, 如 '000001'。
                    2. 带交易所前缀的代码, 如 'SZ000001', 'SH600519'。
        item_name (str): 需要查询的信息项（字段名），必须是中文，例如 '公司名称', '总市值', '行业'。

    Returns:
        Optional[Any]: 查询到的具体数值，或在失败时返回 None。
    """
    _log_debug(f"--- 正在为 A股代码 '{symbol}' 查询基础信息: '{item_name}' ---")
    info_df = None
    try:
        if not re.search(r'(\d{6})', symbol):
            return f"错误：输入的 symbol '{symbol}' 格式不正确，无法提取6位数字代码。"
        market_code = re.search(r'(\d{6})', symbol).group(1)
        _log_debug(f"  -> 标准化代码为 '{market_code}'，使用东方财富接口查询...")
        info_df = ak.stock_individual_info_em(symbol=market_code)
        if info_df is None or info_df.empty:
            _log_debug(f"错误：未能获取到代码 '{market_code}' 的基础信息。请检查代码是否有效。")
            return None
        info_df.set_index("item", inplace=True)
        if item_name not in info_df.index:
            raise KeyError
        value = info_df.loc[item_name, 'value']
        stock_code_from_data = info_df.loc['代码', 'value']
        stock_name_from_data = info_df.loc['公司名称', 'value']
        result_json = {
            "stock_code": stock_code_from_data,
            "stock_name": stock_name_from_data,
            "market": "A-Share",
            "data_source": "Basic Info (Eastmoney)",
            "requested_item": {
                "name": item_name,
                "value": value
            }
        }
        return result_json
    except KeyError:
        _log_debug(f"错误：在 '{symbol}' 的信息中未找到名为 '{item_name}' 的字段。")
        if info_df is not None:
            _log_debug(f"可用字段包括: {info_df.index.tolist()}")
        return f"可用字段包括: {info_df.index.tolist()}"
    except Exception as e:
        return f"获取或处理 '{symbol}' 数据时发生严重错误: {e}"
