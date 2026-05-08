import akshare as ak

from typing import Any, Dict

from ..get_code_from_name import get_code_from_name
from ..utils import _log_debug


def get_stock_individual_basic_info_xq_value(
    row_label: str = "",
    name: str = "",
    code: str = ""
) -> Dict[str, Any]:
    symbol = None
    if code:
        symbol = code
    elif name:
        symbol = get_code_from_name(name)
    else:
        raise ValueError("必须提供 stock code ('code') 或 stock name ('name') 中的一个。")
    if not symbol:
        _log_debug(f"错误: 无法找到与输入相关的有效股票代码。")
        return None
    if symbol.startswith('6'):
        symbol = f"SH{symbol}"
    elif symbol.startswith(('0', '3')):
        symbol = f"SZ{symbol}"
    elif symbol.startswith(('4', '8')):
        symbol = f"BJ{symbol}"
    else:
        symbol = symbol 
    try:
        df = ak.stock_individual_basic_info_xq(symbol=symbol)
        df.set_index('item', inplace=True)
        if row_label not in df.index:
            raise KeyError
        value = df.loc[row_label, 'value']
        stock_code_from_data = df.loc['代码', 'value']
        stock_name_from_data = df.loc['名称', 'value']
        result_json = {
            "stock_code": stock_code_from_data,
            "stock_name": stock_name_from_data,
            "data_source": "雪球(Xueqiu) - Basic Info",
            "requested_item": {
                "name": row_label,
                "value": value
            }
        }
        return result_json
    except KeyError:
        _log_debug(f"错误: 无法在股票 '{symbol}' 的信息中找到项目 '{row_label}'。")
        if 'df' in locals():
            _log_debug(f"该股票可查询的项目有: {df.index.tolist()}")
        return None
    except Exception as e:
        _log_debug(f"获取未知错误: {e}")
        return None
