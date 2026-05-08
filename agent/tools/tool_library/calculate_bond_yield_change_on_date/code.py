import akshare as ak
import pandas as pd

from datetime import timedelta
from typing import Optional, Union, List

from ..utils import _log_debug


def calculate_bond_yield_change_on_date(
target_date: str,
    curve_name: str = "中债国债收益率曲线",
    terms: Optional[List[str]] = None
) -> Union[pd.DataFrame, str]:
    """
    【分析工具】计算并统计在【某一个指定日期】或【其后的首个交易日】，特定债券收益率曲线上多个期限的收益率及其相比上一交易日的变化幅度（单位：基点BP）。
    [最终修正版] 如果用户未指定期限(terms)，函数将自动分析所有可用的期限。
    
    :param target_date: 要查询的目标日期, 格式 'YYYY-MM-DD'.
    :param curve_name: (可选) 要查询的曲线名称。默认为 "中债国债收益率曲线"。
    :param terms: (可选) 一个包含所需期限的列表。如果未提供，则自动分析所有可用期限。
    :return: 一个包含各期限收益率及变化幅度的DataFrame, 或一个错误信息字符串。
    """
    _log_debug(f"--- [收益率变化分析] 正在分析 '{curve_name}' 在 {target_date} 附近的变化... ---")
    try:
        base_dt = pd.to_datetime(target_date)
        start_dt, end_dt = base_dt - timedelta(days=10), base_dt + timedelta(days=7)
        start_date_fmt, end_date_fmt = start_dt.strftime('%Y%m%d'), end_dt.strftime('%Y%m%d')
        _log_debug(f"--- [数据接口] 正在获取 {start_date_fmt} 到 {end_date_fmt} 的债券收益率数据... ---")
        df = ak.bond_china_yield(start_date=start_date_fmt, end_date=end_date_fmt)
        if df.empty:
            error_message = f"错误：API (ak.bond_china_yield) 在 {start_date_fmt} 到 {end_date_fmt} 范围内未返回任何数据。"
            _log_debug(f"--- [数据接口] {error_message} ---")
            return error_message
        df_filtered = df[df['曲线名称'] == curve_name].copy()
        if df_filtered.empty:
            error_message = f"错误: 未能找到曲线名称为 '{curve_name}' 的数据。"
            _log_debug(f"--- [收益率变化分析] {error_message} ---")
            return error_message 
        df_filtered['日期'] = pd.to_datetime(df_filtered['日期'])
        df_filtered.sort_values('日期', inplace=True)
        today_or_next_trade_day = df_filtered[df_filtered['日期'] >= base_dt]
        if today_or_next_trade_day.empty:
            error_message = f"错误: 未能找到 {target_date} 或其后的任何交易日数据。"
            _log_debug(f"--- [收益率变化分析] {error_message} ---")
            return error_message 
        actual_today_series = today_or_next_trade_day.iloc[0]
        actual_today_date = actual_today_series['日期']
        prev_trade_days = df_filtered[df_filtered['日期'] < actual_today_date]
        if prev_trade_days.empty:
            error_message = f"错误: 未能找到 {actual_today_date.strftime('%Y-%m-%d')} 之前的交易日数据，无法计算变化。"
            _log_debug(f"--- [收益率变化分析] {error_message} ---")
            return error_message 
        prev_series = prev_trade_days.iloc[-1]
        _log_debug(f"--- [智能日期定位] 使用实际交易日: {actual_today_date.strftime('%Y-%m-%d')} 与其上一个交易日: {prev_series['日期'].strftime('%Y-%m-%d')} 进行比较。 ---")
        all_possible_terms = ['3月', '6月', '1年', '3年', '5年', '7年', '10年', '30年']
        terms_to_analyze = []
        if terms: 
            terms_to_analyze = terms
        else: 
            _log_debug("--- [期限分析] 用户未指定期限，将自动分析所有可用期限。 ---")
            terms_to_analyze = [term for term in all_possible_terms if term in df_filtered.columns]
        if not terms_to_analyze:
            error_message = "错误：未能确定任何要分析的期限。用户未指定，且自动检测也未发现任何标准期限。"
            _log_debug(f"--- [收益率变化分析] {error_message} ---")
            return error_message
        results = []
        for term in terms_to_analyze:
            if term not in df_filtered.columns:
                _log_debug(f"警告: 请求的期限 '{term}' 不存在于数据中，已跳过。")
                continue
            today_yield = actual_today_series[term]
            prev_yield = prev_series[term]
            change_in_bp = (today_yield - prev_yield) * 100 if pd.notna(today_yield) and pd.notna(prev_yield) else None
            results.append({
                "期限": term,
                f"{actual_today_date.strftime('%Y-%m-%d')}收益率(%)": today_yield,
                f"{prev_series['日期'].strftime('%Y-%m-%d')}收益率(%)": prev_yield,
                "变化幅度(基点)": change_in_bp
            })
        if not results:
            error_message = f"错误：分析完成，但未生成任何有效结果。请检查请求的期限 {terms} 是否有效。"
            _log_debug(f"--- [收益率变化分析] {error_message} ---")
            return error_message
        return pd.DataFrame(results)
    except Exception as e:
        error_message = f"错误：[收益率变化分析] 执行过程中发生未知错误: {e}"
        _log_debug(error_message)
        return error_message
