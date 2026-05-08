import pandas as pd

from typing import Optional, List

from ..utils import _fetch_single_index_history_range, _log_debug


def get_multiple_index_history_df(
    identifiers: List[str],
    start_date: str,
    end_date: str,
    columns_to_include: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    获取【多个指数】在【指定时间段内】的详细历史行情数据，并以DataFrame对象返回。
    
    :param identifiers: 一个包含多个指数名称或代码的列表。
    :param start_date: 开始日期 (格式 'YYYY-MM-DD')。
    :param end_date: 结束日期 (格式 'YYYY-MM-DD')。
    :param columns_to_include: (可选) 一个包含所需数据列名的列表。
    :return: 一个包含历史数据的 pandas.DataFrame 对象。如果发生错误，则返回一个空的DataFrame。
    """
    _log_debug(f"--- [批量获取任务] 开始获取 {identifiers} 从 {start_date} 到 {end_date} 的历史数据... ---")
    VALID_COLUMNS = {'open', 'high', 'low', 'close', 'volume', 'turnover'}
    if columns_to_include:
        invalid_columns = [col for col in columns_to_include if col not in VALID_COLUMNS]
        if invalid_columns:
            error_message = f"错误：请求了无效的列名 {invalid_columns}。有效的列名包括: {list(VALID_COLUMNS)}。"
            _log_debug(f"--- [批量获取任务] {error_message}")
            return error_message
    else:
        columns_to_include = ['open', 'high', 'low', 'close', 'volume', 'turnover']
    all_dfs = []
    errors = []
    for identifier in identifiers:
        result = _fetch_single_index_history_range(identifier, start_date, end_date)
        if isinstance(result, pd.DataFrame):
            all_dfs.append(result)
        else:
            errors.append(f"'{identifier}': {result}")
    if not all_dfs:
        if not all_dfs:
            error_message = f"错误：未能成功获取任何一个指数的数据。详情: {'; '.join(errors)}"
            _log_debug(f"--- [批量获取任务] {error_message} ---")
            return error_message
    if errors:
        error_message = f"错误：部分指数获取失败: {'; '.join(errors)} ---"
        _log_debug(f"--- [批量获取任务] {error_message}")
        return error_message
    try:
        combined_df = pd.concat(all_dfs, ignore_index=True)
        required_cols = ['date', 'identifier'] + columns_to_include
        final_cols_to_use = [col for col in required_cols if col in combined_df.columns]
        filtered_df = combined_df[final_cols_to_use]
        value_columns = [col for col in final_cols_to_use if col not in ['date', 'identifier']]
        if not value_columns:
            error_message = f"错误：请求的列 {columns_to_include} 在获取到的数据中均不存在。---"
            _log_debug(f"--- [批量获取任务] 警告：请求的列 {columns_to_include} 在获取到的数据中均不存在。---")
            return error_message
        pivot_df = filtered_df.pivot_table(
            index='date', 
            columns='identifier', 
            values=value_columns
        )
        return pivot_df
    except Exception as e:
        error_message = f"错误：在合并和处理数据时发生异常: {e} ---"
        _log_debug(f"--- [批量获取任务] 错误：在合并和处理数据时发生异常: {e} ---")
        return error_message
