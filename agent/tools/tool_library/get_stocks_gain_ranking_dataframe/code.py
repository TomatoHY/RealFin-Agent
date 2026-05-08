import pandas as pd

from typing import List

from ..get_stocks_history_dataframe import get_stocks_history_dataframe
from ..utils import _log_debug


def get_stocks_gain_ranking_dataframe(
codes: List[str],
    start_date: str,
    end_date: str,
    adjust: str = ""
) -> pd.DataFrame:
    """
    【批量分析工具】计算【多只股票】在指定时间段内的区间涨跌幅，并按涨幅从高到低进行排名。
    直接返回一个包含排名结果的 DataFrame。

    Args:
        codes (List[str]): 股票代码的列表 (例如: ["sh600519", "sz300750"]).
        start_date (str): 开始日期, 格式 'YYYY-MM-DD'.
        end_date (str): 结束日期, 格式 'YYYY-MM-DD'.
        adjust (str, optional): 复权类型. "", "qfq", "hfq". 默认为 "".

    Returns:
        pd.DataFrame: 一个包含排名结果的 DataFrame，列包括 'rank', 'code', 'name', 'gain_percentage'。
    """
    _log_debug(f"--- [批量排名分析] 正在为 {len(codes)} 只股票计算从 {start_date} 到 {end_date} 的涨跌幅排名... ---")
    history_df = get_stocks_history_dataframe(
        codes=codes,
        start_date=start_date,
        end_date=end_date,
        adjust=adjust
    )
    if history_df.empty:
        _log_debug("--- [批量排名分析] 未能获取到任何历史数据，返回空排名。 ---")
        return pd.DataFrame(columns=['rank', 'code', 'name', 'gain_percentage'])
    def calculate_gain(group):
        group = group.sort_values('date')
        start_price = group.iloc[0]['close']
        end_price = group.iloc[-1]['close']
        if start_price is None or pd.isna(start_price) or start_price == 0:
            return None 
        gain = ((end_price - start_price) / start_price) * 100
        return gain
    ranking_series = history_df.groupby('code').apply(calculate_gain)
    ranking_df = ranking_series.reset_index(name='gain_percentage')
    ranking_df.dropna(inplace=True)
    if ranking_df.empty:
        return pd.DataFrame(columns=['rank', 'code', 'name', 'gain_percentage'])
    ranking_df.sort_values('gain_percentage', ascending=False, inplace=True)
    ranking_df.reset_index(drop=True, inplace=True)
    ranking_df['rank'] = ranking_df.index + 1
    code_to_name_map = dict(zip(history_df['code'], history_df.get('name', history_df['code'])))
    ranking_df['name'] = ranking_df['code'].map(code_to_name_map)
    ranking_df['gain_percentage'] = ranking_df['gain_percentage'].round(2)
    final_columns = ['rank', 'code', 'name', 'gain_percentage']
    final_df = ranking_df[[col for col in final_columns if col in ranking_df.columns]]
    _log_debug(f"--- [批量排名分析] 完成！成功计算并排名了 {len(final_df)} 只股票。 ---")
    return final_df
