import pandas as pd

from typing import Union, List

from ..get_multiple_index_history_df import get_multiple_index_history_df
from ..utils import _log_debug


def get_indices_gain_ranking_dataframe(
identifiers: List[str],
    start_date: str,
    end_date: str
) -> Union[pd.DataFrame, str]:
    """
    【批量分析工具】计算【多只指数】在指定时间段内的区间涨跌幅，并按涨幅从高到低进行排名。
    严格按照要求，在成功时直接返回一个 pandas.DataFrame 对象。

    :param identifiers: 指数名称或代码的列表 (例如: ["沪深300", "纳斯达克"])。
    :param start_date: 开始日期, 格式 'YYYY-MM-DD'.
    :param end_date: 结束日期, 格式 'YYYY-MM-DD'.
    :return: 一个包含排名结果的 pandas.DataFrame 对象，或描述错误的字符串。
    """
    _log_debug(f"--- [批量排名分析] 正在为 {len(identifiers)} 只指数计算从 {start_date} 到 {end_date} 的涨跌幅排名... ---")
    history_df_wide = get_multiple_index_history_df(
        identifiers=identifiers,
        start_date=start_date,
        end_date=end_date,
        columns_to_include=['close']
    )
    if isinstance(history_df_wide, str):
        return f"错误：在获取批量历史数据时失败: {history_df_wide}"
    if history_df_wide.empty:
        return "错误：未能获取到任何指数在指定时间段内的历史数据。"
    history_df_long = history_df_wide.stack().reset_index()
    history_df_long.columns = ['date', 'identifier', 'close']
    history_df_long['date'] = pd.to_datetime(history_df_long['date'])
    def calculate_gain(group):
        group = group.sort_values('date')
        if len(group) < 2: return None
        start_price = group.iloc[0]['close']
        end_price = group.iloc[-1]['close']
        if pd.isna(start_price) or start_price == 0: return None
        return ((end_price - start_price) / start_price) * 100
    ranking_series = history_df_long.groupby('identifier').apply(calculate_gain)
    ranking_df = ranking_series.reset_index(name='gain_percentage')
    ranking_df.dropna(inplace=True)
    if ranking_df.empty:
        return "信息：所有指数都因数据不足而无法计算涨跌幅。"
    ranking_df.sort_values('gain_percentage', ascending=False, inplace=True)
    ranking_df.reset_index(drop=True, inplace=True)
    ranking_df['rank'] = ranking_df.index + 1
    ranking_df['gain_percentage'] = ranking_df['gain_percentage'].round(2)
    final_df = ranking_df[['rank', 'identifier', 'gain_percentage']]
    _log_debug(f"--- [批量排名分析] 完成！成功计算并排名了 {len(final_df)} 只指数。 ---")
    return final_df
