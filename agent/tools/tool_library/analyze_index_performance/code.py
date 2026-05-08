from typing import Optional, Dict, Union, List

from ..get_multiple_index_history_df import get_multiple_index_history_df
from ..utils import _log_debug


def analyze_index_performance(
identifiers: List[str],
    start_date: str,
    end_date: str,
    pct_change_threshold_percent: Optional[float] = None,
    turnover_threshold_yuan: Optional[float] = None
) -> Union[Dict, str]:
    """
    分析一个或多个指数在指定时间段内的表现。
    此工具能获取原始数据，计算每日涨跌幅，并根据给定的阈值进行筛选，最终返回满足所有条件的天数和具体日期。
    
    :param identifiers: 指数名称或代码的列表。
    :param start_date: 开始日期, 格式 'YYYY-MM-DD'.
    :param end_date: 结束日期, 格式 'YYYY-MM-DD'.
    :param pct_change_threshold_percent: (可选) 日涨跌幅筛选阈值(%)。例如，输入1.0代表筛选出涨幅 > 1% 的天数。
    :param turnover_threshold_yuan: (可选) 日成交金额筛选阈值(元)。例如，输入5000e8代表筛选出成交金额 > 5000亿元的天数。
    :return: 一个包含分析结果的字典，或描述错误的字符串。
    """
    _log_debug(f"--- [高级分析任务] 开始分析 {identifiers} 从 {start_date} 到 {end_date} 的表现... ---")
    required_columns = ['close', 'turnover']
    history_df = get_multiple_index_history_df(
        identifiers=identifiers,
        start_date=start_date,
        end_date=end_date,
        columns_to_include=required_columns
    )
    if history_df.empty:
        return "错误：未能获取到用于分析的基础行情数据，无法继续。"
    results = {}
    for identifier in identifiers:
        if ('close', identifier) not in history_df.columns:
            results[identifier] = {"status": "error", "message": "缺少收盘价数据，无法分析。"}
            continue
        index_df = history_df[[col for col in history_df.columns if col[1] == identifier]].copy()
        index_df.columns = index_df.columns.droplevel(1)
        index_df['pct_change'] = index_df['close'].pct_change() * 100
        conditions = pd.Series(True, index=index_df.index) 
        if pct_change_threshold_percent is not None:
            conditions &= index_df['pct_change'] > pct_change_threshold_percent
        if turnover_threshold_yuan is not None:
            if 'turnover' in index_df.columns:
                conditions &= index_df['turnover'] > turnover_threshold_yuan
            else:
                results[identifier] = {"status": "error", "message": "数据源未提供成交金额(turnover)，无法按此条件筛选。"}
                continue
        filtered_days = index_df[conditions]
        results[identifier] = {
            "status": "success",
            "count_of_matching_days": len(filtered_days),
            "matching_days_details": [
                {
                    "date": day.strftime('%Y-%m-%d'),
                    "pct_change": round(row.pct_change, 2) if pd.notna(row.pct_change) else None,
                    "turnover_yuan": int(row.turnover) if 'turnover' in row and pd.notna(row.turnover) else None
                }
                for day, row in filtered_days.iterrows()
            ]
        }
    return results
