import time

import akshare as ak
import pandas as pd

from datetime import datetime, timedelta
from typing import Optional, Any, Dict

from ..utils import _COLUMN_MAP_AK_TO_STD, _log_debug


def get_index_history(
identifier: str, 
    column_label: str,
    query_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    market: Optional[str] = None,
    original_query: Optional[str] = None
) -> Dict[str, Any]:
    """
    获取指数的【历史】行情数据。
    """
    def _fail_hist(error_msg: str) -> Dict[str, Any]:
        return {
            "value": f"错误: {error_msg}", 
            "date": datetime.now().strftime('%Y-%m-%d')
        }
    if not query_date:
        return _fail_hist("错误: 历史查询必须提供 `query_date` (单点查询)。")
    if start_date or end_date:
        return _fail_hist("错误: 此函数只支持 `query_date` (单点查询)。请移除 `start_date` 和 `end_date`。")
    entity_info = find_index_code_and_market(identifier=identifier, market_hint=market) 
    if not entity_info:
        return _fail_hist(f"实体链接失败，未能找到与 '{identifier}' 相关的信息。")
    code_for_api, name_for_api, identified_market = entity_info
    market_for_api = identified_market.replace("_index", "")
    effective_query_date_str = query_date
    try:
        for i in range(7): # 7 天回溯
            current_date = datetime.strptime(effective_query_date_str, '%Y-%m-%d') - timedelta(days=i)
            target_date_pd = pd.to_datetime(current_date.strftime('%Y-%m-%d'))
            api_sources = []
            if market_for_api == 'us':
                api_sources = [
                    ("ak.index_us_stock_sina (Sina)", lambda: ak.index_us_stock_sina(symbol=code_for_api))
                ]
            elif market_for_api == 'a':
                api_sources = [
                    ("ak.stock_zh_index_daily_em (Eastmoney)", lambda: ak.stock_zh_index_daily_em(symbol=code_for_api)),
                    ("ak.stock_zh_index_daily (Sina)", lambda: ak.stock_zh_index_daily(symbol=code_for_api)),
                    ("ak.stock_zh_index_daily_tx (Tencent)", lambda: ak.stock_zh_index_daily_tx(symbol=code_for_api))
                ]
            elif market_for_api == 'hk':
                api_sources = [
                    ("ak.stock_hk_index_daily_em (Eastmoney)", lambda: ak.stock_hk_index_daily_em(symbol=code_for_api)),
                    ("ak.stock_hk_index_daily_sina (Sina)", lambda: ak.stock_hk_index_daily_sina(symbol=code_for_api))
                ]
            elif market_for_api == 'global':
                api_sources = [
                    ("ak.index_global_hist_em (Eastmoney)", lambda: ak.index_global_hist_em(symbol=name_for_api)),
                    ("ak.index_global_hist_sina (Sina)", lambda: ak.index_global_hist_sina(symbol=name_for_api))
                ]
            else:
                return _fail_hist(f"未知的市场类型 '{market_for_api}'。")
            all_history_df = None
            source_succeeded = ""
            for source_name, source_func in api_sources:
                try:
                    time.sleep(30)
                    all_history_df = source_func()
                    if all_history_df is not None and not all_history_df.empty:
                        source_succeeded = source_name
                        _log_debug(f"--- [历史API] 成功从 {source_name} 获取数据。")
                        break
                except Exception as api_e:
                    _log_debug(f"--- [历史API] {source_name} 调用失败: {api_e}")
                    pass
            if all_history_df is not None and not all_history_df.empty:
                all_history_df.rename(columns={
                    'date': 'date', 'open': 'open', 'high': 'high', 'low': 'low', 'close': 'close',
                    **_COLUMN_MAP_AK_TO_STD
                }, inplace=True, errors='ignore')
                if 'date' not in all_history_df.columns: 
                    _log_debug(f"--- [历史API] 错误: {source_succeeded} 返回的数据缺少 'date' 列。")
                    continue
                all_history_df['date'] = pd.to_datetime(all_history_df['date'], errors='coerce')
                all_history_df.dropna(subset=['date'], inplace=True)
                hist_df = all_history_df[all_history_df['date'] == target_date_pd]
                if not hist_df.empty:
                    stock_row = hist_df.iloc[0]
                    clean_column_label = column_label.lower().strip() if column_label else 'close'
                    hist_col = clean_column_label
                    if hist_col in stock_row and pd.notna(stock_row[hist_col]):
                            value = stock_row[hist_col]
                            if isinstance(value, str):
                                try:
                                    s_value = value.strip().rstrip('%').replace('+', '').replace(',', '')
                                    value = float(s_value)
                                except (ValueError, TypeError):
                                    return _fail_hist(f"历史数据 '{value}' 无法转换为数字。")
                            actual_date = stock_row.get('date').strftime('%Y-%m-%d')
                            return {
                                "source": "akshare_history_api", 
                                "identifier": name_for_api, 
                                "column": clean_column_label, 
                                "value": float(value),
                                "date": actual_date
                            }
                    else:
                        _log_debug(f"--- [历史API] 在 {target_date_pd} 找到了数据，但 '{hist_col}' 列无效或为空。正在回溯...")
                        continue 
        return _fail_hist(f"在日期 '{effective_query_date_str}' 及其前7天内，均未找到 '{identifier}' 的有效历史数据。")
    except Exception as e:
        return _fail_hist(f"在为'{identifier}'获取'{query_date}'的历史数据时发生意外的程序错误: {e}")
    return _fail_hist("未知的函数逻辑错误。")
