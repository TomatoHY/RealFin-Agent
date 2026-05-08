import akshare as ak
import pandas as pd

from typing import Any, Dict, Union, List

from ..utils import _log_debug


def get_index_components(
    symbol: str, 
    include_weights: bool = False
) -> Union[List[Dict[str, Any]], str]:
    """
    根据中证指数代码, 获取其所有成分股列表, 并可选择性地包含其权重。

    Args:
        symbol (str): 指数代码, 例如 "000300" (沪深300) 或 "000688.SH" (科创50)。
                    函数会自动处理 .SH 或 .SZ 等后缀。
        include_weights (bool, optional): 是否获取权重。
                                        True: 返回包含权重的列表 (调用 index_stock_cons_weight_csindex)。
                                        False: 仅返回成分股列表 (调用 index_stock_cons_csindex)。
                                        默Renault 为 False。

    Returns:
        Union[List[Dict[str, Any]], str]: 
            - 成功: 返回一个列表, 每个元素是一个字典。
            - if include_weights=False: [{"stock_code": "...", "stock_name": "..."}]
            - if include_weights=True: [{"stock_code": "...", "stock_name": "...", "weight": 0.52}]
            - 失败: (例如代码无效或网络问题) 返回一个错误信息字符串。
    """
    if not symbol:
        error_message = "错误：'symbol' 参数不能为空。"
        _log_debug(f"--- [成分股查询] {error_message} ---")
        return error_message
    try:
        clean_symbol = str(symbol).split('.')[0]
        if not clean_symbol:
            error_message = f"错误：提供的 'symbol' ('{symbol}') 无效。"
            _log_debug(f"--- [成分股查询] {error_message} ---")
            return error_message
        result_df = pd.DataFrame()
        output_columns = []
        if include_weights:
            _log_debug(f"Tool call: calling ak.index_stock_cons_weight_csindex(symbol='{clean_symbol}')")
            df = ak.index_stock_cons_weight_csindex(symbol=clean_symbol)
            if df.empty or "成分券代码" not in df.columns or "权重" not in df.columns:
                error_message = f"错误：权重接口 (ak.index_stock_cons_weight_csindex) 为 '{clean_symbol}' 返回了空数据或无效数据（缺少'成分券代码'或'权重'列）。"
                _log_debug(f"--- [成分股查询] {error_message} ---")
                return error_message 
            df_renamed = df.rename(columns={
                "成分券代码": "stock_code",
                "成分券名称": "stock_name",
                "权重": "weight"
            })
            output_columns = ["stock_code", "stock_name", "weight"]
            result_df = df_renamed[output_columns]
        else:
            _log_debug(f"Tool call: calling ak.index_stock_cons_csindex(symbol='{clean_symbol}')")
            df = ak.index_stock_cons_csindex(symbol=clean_symbol)
            if df.empty or "成分券代码" not in df.columns:
                error_message = f"错误：成分股接口 (ak.index_stock_cons_csindex) 为 '{clean_symbol}' 返回了空数据或无效数据（缺少'成分券代码'列）。"
                _log_debug(f"--- [成分股查询] {error_message} ---")
                return error_message 
            df_renamed = df.rename(columns={
                "成分券代码": "stock_code",
                "成分券名称": "stock_name"
            })
            output_columns = ["stock_code", "stock_name"]
            result_df = df_renamed[output_columns]
        if result_df.empty:
            error_message = f"错误：数据在重命名的过程中丢失，'{clean_symbol}' 未返回有效成分股。"
            _log_debug(f"--- [成分股查询] {error_message} ---")
            return error_message
        return result_df.to_dict('records') 
    except Exception as e:
        error_message = f"错误: 在为 '{symbol}' (clean: '{clean_symbol}') 调用 akshare 接口时发生异常: {e}"
        _log_debug(f"--- [成分股查询] {error_message} ---")
        return error_message
