from ..utils import _load_index_data, _log_debug


def get_index_stock_info(
index_name: str, info_type: str
) -> str:
    """
    根据指数的中文名称, 从本地CSV文件获取其代码或发布日期。
    
    Returns:
        str: 成功时返回找到的信息 (代码或日期), 失败时返回一个错误信息字符串。
    """
    df_or_error = _load_index_data()
    if isinstance(df_or_error, str):
        _log_debug(f"--- [索引查询] 内部数据加载失败: {df_or_error} ---")
        return df_or_error  
    df_cache = df_or_error
    target_column = ""
    if info_type == "code":
        target_column = "index_code"
    elif info_type == "publish_date":
        target_column = "publish_date"
    else:
        error_message = f"错误: 无效的 info_type '{info_type}'. 必须是 'code' 或 'publish_date'。"
        _log_debug(f"--- [索引查询] {error_message} ---")
        return error_message 
    try:
        result = df_cache.loc[index_name, target_column]
        return str(result) 
    except KeyError:
        error_message = f"错误: 未能在本地文件中找到名称为 '{index_name}' 的指数。"
        _log_debug(f"--- [索引查询] {error_message} ---")
        return error_message
    except Exception as e:
        error_message = f"查找 '{index_name}' 数据时发生未知错误: {e}"
        _log_debug(f"--- [索引查询] {error_message} ---")
        return error_message
