import re

import akshare as ak
import pandas as pd

from typing import Optional, Literal

from ..utils import _log_debug, _api_cache


def get_china_macro_pro(
indicator_name: Literal[
        "cpi", "fiscal_revenue", "money_supply", 
        "gold_forex_reserves", "central_bank_balance_sheet"
    ],
    target_time: Optional[str] = None,
    target_metric: Optional[str] = None
) -> str:
    """
    获取中国的核心宏观经济指标。
    """
    global _api_cache
    
    try:
        if indicator_name in _api_cache:
            df = _api_cache[indicator_name]
            _log_debug(f"--- [函数缓存] 成功从缓存中读取 '{indicator_name}' 数据。 ---")
        else:
            api_map = {
                "cpi": ak.macro_china_cpi,
                "fiscal_revenue": ak.macro_china_czsr,
                "money_supply": ak.macro_china_money_supply,
                "gold_forex_reserves": ak.macro_china_foreign_exchange_gold,
                "central_bank_balance_sheet": ak.macro_china_central_bank_balance,
            }
            if indicator_name not in api_map:
                return f"错误：无效的指标名称 '{indicator_name}'。可用选项为: {list(api_map.keys())}"
            _log_debug(f"--- [API 调用] 缓存未命中，正在通过 akshare 下载 '{indicator_name}' 数据... ---")
            df: pd.DataFrame = api_map[indicator_name]()
            if df.empty:
                return f"查询 '{indicator_name}' 成功，但接口未返回任何数据。"
            _api_cache[indicator_name] = df # 存入缓存
        time_col = '月份' if '月份' in df.columns else '统计时间'
        df_indexed = df.set_index(time_col, inplace=False)
        if not target_time and not target_metric:
            latest_time = df_indexed.index[0]
            available_metrics = df_indexed.columns.tolist()
            summary_json = {
                "summary": f"'{indicator_name}' 数据查询成功。",
                "latest_data_time": latest_time,
                "available_metrics": available_metrics,
                "guidance": "请提供 'target_time' 和 'target_metric' 以获取具体数值。"
            }
            return summary_json
        if not target_time or not target_metric:
            return "错误：当查询具体数值时，必须同时提供 'target_time' 和 'target_metric' 两个参数。"
        clean_time_input = target_time.strip().lower()
        query_time_str = None
        if clean_time_input == 'latest':
            query_time_str = df_indexed.index[0]
        else:
            match = re.match(r"(\d{4})[-年]?(\d{1,2})", clean_time_input)
            if match:
                year, month = int(match.group(1)), int(match.group(2))
                index_example = df_indexed.index[0]
                if '月份' in index_example:
                    query_time_str = f"{year}年{month:02d}月份"
                elif '.' in index_example:
                    query_time_str = f"{year}.{month:02d}"
                else: query_time_str = f"{year}-{month:02d}"
        if not query_time_str:
            query_time_str = target_time
        try:
            clean_metric = target_metric.strip()
            
            if query_time_str not in df_indexed.index:
                raise KeyError(f"时间点 '{query_time_str}' 不存在。")
            if clean_metric not in df_indexed.columns:
                raise KeyError(f"指标 '{clean_metric}' 无效。")
            value = df_indexed.loc[query_time_str, clean_metric]
            if pd.isna(value):
                return f"在 '{query_time_str}' 找到了指标 '{clean_metric}'，但其数值为空。"
            final_value = value.item() if hasattr(value, 'item') else value
            result_json = {
                "indicator_name": indicator_name,
                "time_period": query_time_str,
                "metric_name": clean_metric,
                "value": final_value
            }
            return result_json
        except KeyError as e:
            available_times = df_indexed.index[:5].tolist()
            available_metrics = df_indexed.columns.tolist()
            return (
                f"错误: {e}\n"
                f"请检查您的输入。\n"
                f"可用的时间格式示例: {available_times}\n"
                f"可用的指标: {available_metrics}"
            )
    except Exception as e:
        return f"查询 '{indicator_name}' 时发生严重错误: {e}"
