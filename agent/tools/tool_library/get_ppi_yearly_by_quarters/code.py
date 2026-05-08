import pandas as pd

from typing import Union, List

from ..utils import _get_and_clean_ppi_data, _log_debug


def get_ppi_yearly_by_quarters(
quarters: List[str]
) -> Union[pd.DataFrame, str]:
    """
    获取中国PPI年率在【一个或多个指定季度】内的【月度同比】数据。
    
    :param quarters: 一个包含一个或多个季度字符串的列表。格式必须是 'YYYYQX'，例如 ['2023Q1', '2023Q4']。
    :return: 一个包含'月份'和'ppi_yoy'(PPI月度同比)列的DataFrame, 或一个错误信息字符串。
    """
    _log_debug(f"--- [PPI查询] 正在获取 {quarters} 季度的月度PPI数据... ---")
    if not quarters:
        error_message = "错误: 'quarters' 列表不能为空。"
        _log_debug(f"--- [PPI查询] {error_message} ---")
        return error_message # <-- 3. 修改点
    try:
        start_month = "9999-99"
        end_month = "0000-00"
        for q in quarters:
            if not (isinstance(q, str) and len(q) == 6 and q[4] == 'Q' and q[5] in '1234'):
                raise ValueError(f"季度格式错误: '{q}' (必须是 'YYYYQX' 格式的字符串)")
            year = q[:4]
            quarter_num = int(q[5])
            q_start_month = f"{year}-{((quarter_num-1)*3)+1:02d}"
            q_end_month = f"{year}-{quarter_num*3:02d}"
            if q_start_month < start_month:
                start_month = q_start_month
            if q_end_month > end_month:
                end_month = q_end_month
    except (ValueError, TypeError, AttributeError) as e:
        error_message = f"错误: 解析季度列表时出错。请确保格式为 'YYYYQX'。错误详情: {e}"
        _log_debug(f"--- [PPI查询] {error_message} ---")
        return error_message 
    df_or_error = _get_and_clean_ppi_data()
    if isinstance(df_or_error, str):
        _log_debug(f"--- [PPI查询] 内部函数返回错误: {df_or_error} ---")
        return df_or_error  
    df = df_or_error
    if df.empty:
        error_message = "错误：PPI数据获取成功，但未返回任何数据。"
        _log_debug(f"--- [PPI查询] {error_message} ---")
        return error_message
    try:
        mask = (df['date'] >= start_month) & (df['date'] <= end_month)
        result_df = df.loc[mask].copy()
    except Exception as e:
        error_message = f"错误：在筛选日期 {start_month} 到 {end_month} 时发生错误: {e}。请检查日期格式是否为 YYYY-MM。"
        _log_debug(f"--- [PPI查询] {error_message} ---")
        return error_message
    if result_df.empty:
        error_message = f"错误：在 {start_month} 到 {end_month} 的总时间范围内没有找到任何PPI数据。"
        _log_debug(f"--- [PPI查询] {error_message} ---")
        return error_message
    def get_quarter(date_str):
        month = int(date_str.split('-')[1])
        return f"Q{ (month - 1) // 3 + 1 }"
    result_df['quarter'] = result_df['date'].apply(lambda x: f"{x[:4]}{get_quarter(x)}")
    final_df = result_df[result_df['quarter'].isin(quarters)]
    if final_df.empty:
        error_message = f"错误：在指定的季度 {quarters} 中未找到任何PPI数据（可能数据只存在于总范围内的其他月份）。"
        _log_debug(f"--- [PPI查询] {error_message} ---")
        return error_message
    return final_df[['date', 'ppi_yoy']].reset_index(drop=True)
