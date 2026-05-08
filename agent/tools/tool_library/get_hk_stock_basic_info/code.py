import akshare as ak

from typing import Optional, Any

from ..get_code_from_name import get_code_from_name
from ..utils import _log_debug


def get_hk_stock_basic_info(
item_name: str, 
    name: Optional[str] = None, 
    code: Optional[str] = None
) -> Optional[Any]:
    """获取港股基本信息"""
    if not code and not name:
        return None
    symbol = code if code else get_code_from_name(name)
    if not symbol:
        _log_debug(f"错误：未能通过名称 '{name}' 找到对应的股票代码。")
        return None
    try:
        _log_debug(f"  -> 正在为代码 '{symbol}' 从雪球查询公司概况...")
        info_df = ak.stock_individual_basic_info_hk_xq(symbol=symbol)
        if info_df is None or info_df.empty:
            _log_debug(f"错误：未能获取到代码 '{symbol}' 的基础信息。请检查代码是否有效。")
            return None
        info_df.set_index("item", inplace=True)
        try:
            value = info_df.loc[item_name, 'value']
            stock_code_from_data = info_df.loc['代码', 'value']
            stock_name_from_data = info_df.loc['名称', 'value']
            result_json = {
                "stock_code": stock_code_from_data,
                "stock_name": stock_name_from_data,
                "data_source": "Hong Kong Stock Basic Info",
                "requested_item": {
                    "name": item_name,
                    "value": value
                }
            }
            return result_json
        except KeyError:
            _log_debug(f"错误：在 '{symbol}' 的信息中未找到名为 '{item_name}' 的字段。")
            _log_debug(f"可用字段包括: {info_df.index.tolist()}") # 打印所有可用的字段名
            return None
    except Exception as e:
        _log_debug(f"获取或处理数据时发生严重错误: {e}")
        return None
