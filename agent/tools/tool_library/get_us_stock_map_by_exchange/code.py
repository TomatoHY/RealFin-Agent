from typing import Dict, Union, List

from ..utils import _create_map_from_df, _load_us_stock_data, _log_debug


def get_us_stock_map_by_exchange(
    exchange_name: str,
    output_format: str = "dict"
) -> Union[Dict[str, str], List[str], str]:
    """
    返回指定美股市场（例如 'NASDAQ', 'NYSE'）的所有股票 {name: symbol} 字典
    或所有股票代码 (symbol) 的列表。
    
    Args:
        exchange_name (str): 交易所的准确名称 (区分大小写)。
        output_format (str, optional): 
            返回的格式。默认为 "dict" ({name: symbol})。
            - "dict": 返回 {name: symbol} 的字典。
            - "code_list": 返回所有股票代码 (symbol) 的列表 [代码1, 代码2, ...]。

    Returns:
        Union[Dict[str, str], List[str], str]: 
            - 成功 (dict): 返回 {name: symbol} 的字典。
            - 成功 (code_list): 返回所有股票代码的列表。
            - 失败: 返回一个描述错误的字符串。
    """
    _log_debug(f"--- 正在为美股交易所 '{exchange_name}' 获取股票地图 (格式: {output_format})... ---")
    VALID_FORMATS = ["dict", "code_list"]
    if output_format not in VALID_FORMATS:
        return f"错误：无效的 'output_format' 参数 '{output_format}'。有效选项为 {VALID_FORMATS}。"
    df_or_error = _load_us_stock_data()
    if isinstance(df_or_error, str):
        return df_or_error 
    df = df_or_error
    if 'market' not in df.columns:
        return "错误: 美股CSV中缺少 'market' 列, 无法按交易所筛选。"
    try:
        filtered_df = df[df['market'] == exchange_name]
        if filtered_df.empty:
            available_markets = df['market'].unique().tolist()
            return (f"错误：在美股数据中未找到交易所 '{exchange_name}'。\n"
                    f"    - (请注意：此筛选区分大小写)\n"
                    f"    - 可用的市场示例: {available_markets[:10]}...")
        _log_debug(f"--- 筛选到 {len(filtered_df)} 只 '{exchange_name}' 市场的股票。 ---")
        if output_format == "dict":
            return _create_map_from_df(filtered_df, name_col='name', code_col='symbol')
        elif output_format == "code_list":
            code_list = filtered_df['symbol'].drop_duplicates().tolist()
            _log_debug(f"--- 市场 '{exchange_name}' 加载成功，返回 {len(code_list)} 个独特的代码。 ---")
            return code_list
    except KeyError as e:
        return f"错误：在处理DataFrame时缺少关键列 (name, symbol): {e}。"
    except Exception as e:
        return f"错误: 筛选交易所 '{exchange_name}' 时出错: {e}"
    return "错误：未知的内部错误。"
