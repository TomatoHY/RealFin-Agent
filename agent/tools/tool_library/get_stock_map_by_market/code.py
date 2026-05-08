import pandas as pd

from typing import Dict, Union, List

from ..utils import _create_map_from_df, _load_a_stock_data, _load_hk_stock_data, _load_us_stock_data, _log_debug


def get_stock_map_by_market(
market: str, 
    output_format: str = "dict"
) -> Union[Dict[str, str], List[str], str]:
    """
    根据市场 ('a', 'hk', 'us')，返回 {股票名称: 股票代码} 的字典，或所有股票代码的列表。
    
    Args:
        market (str): 市场代码，必须是 'a' (A股), 'hk' (港股), 或 'us' (美股)。
        output_format (str, optional): 
            返回的格式。默认为 "dict" ({名称: 代码})。
            - "dict": 返回 {股票名称: 股票代码} 的字典。
            - "code_list": 返回所有股票代码的列表 [代码1, 代码2, ...]。

    Returns:
        Union[Dict[str, str], List[str], str]: 
            - 成功 (dict): 返回 {股票名称: 股票代码} 的字典。
            - 成功 (code_list): 返回所有股票代码的列表。
            - 失败: 返回一个描述错误的字符串。
    """
    _log_debug(f"--- 正在为市场 '{market}' 获取股票地图 (格式: {output_format})... ---")
    VALID_FORMATS = ["dict", "code_list"]
    if output_format not in VALID_FORMATS:
        return f"错误：无效的 'output_format' 参数 '{output_format}'。有效选项为 {VALID_FORMATS}。"
    df_or_error: Union[pd.DataFrame, str]
    name_col, code_col = "", ""
    if market == 'a':
        df_or_error = _load_a_stock_data()
        name_col, code_col = '名称', '代码'
    elif market == 'hk':
        df_or_error = _load_hk_stock_data()
        name_col, code_col = '中文名称', '代码'
    elif market == 'us':
        df_or_error = _load_us_stock_data()
        name_col, code_col = 'name', 'symbol'
    else:
        return f"错误：无效的市场代码 '{market}'。有效代码为 'a', 'hk', 'us'。"
    if isinstance(df_or_error, str):
        return df_or_error 
    df = df_or_error 
    try:
        if output_format == "dict":
            return _create_map_from_df(df, name_col=name_col, code_col=code_col)
        elif output_format == "code_list":
            code_list = df[code_col].drop_duplicates().tolist()
            _log_debug(f"--- 市场 '{market}' 加载成功，返回 {len(code_list)} 个独特的代码。 ---")
            return code_list
    except KeyError as e:
        return f"错误：在处理DataFrame时缺少关键列: {e}。请检查CSV文件和列名定义。"
    except Exception as e:
        return f"错误：在格式化输出时发生未知错误: {e}"
    return "错误：未知的内部错误。"
