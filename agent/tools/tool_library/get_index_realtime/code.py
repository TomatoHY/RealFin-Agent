import time

import akshare as ak
import pandas as pd

from datetime import datetime
from typing import Optional, Any, Dict

from ..utils import _fetch_index_spot_api, _log_debug

def find_index_code_and_market(identifier, market_hint=None):
    return None


def get_index_realtime(
    identifier: str,
    column_label: str,
    market: Optional[str] = None
) -> Dict[str, Any]:
    """
    获取指数的【实时】行情数据。
    """
    _log_debug(f"--- [本地实时查询] 正在为 '{identifier}' 查找 '{column_label}'... ---")
    entity_info = find_index_code_and_market(identifier=identifier, market_hint=market)
    if not entity_info:
        return {"value": f"错误: 实体链接失败，未能找到与 '{identifier}' 相关的信息。"}
    target_code, original_name, market_key = entity_info
    clean_column_label = column_label.lower().strip()
    value = None
    date_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    found_col_name = "N/A"
    try:
        if market_key == 'us_index':
            us_api_func = lambda: ak.index_us_stock_sina(symbol=target_code)
            _log_debug(f"--- [US实时] 正在通过 ak.index_us_stock_sina(symbol='{target_code}') 获取数据... ---")
            time.sleep(30)
            df_raw = us_api_func()
            if df_raw is None or df_raw.empty:
                raise ValueError(f"无法从 {target_code} API 获取实时数据。")
            df_raw.rename(columns={'close': '最新价', 'preclose': '昨收价'}, inplace=True)
            stock_row = df_raw.iloc[-1]
            date_time_str = stock_row.get('date', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            if clean_column_label == 'pct_change':
                latest_close = stock_row.get('最新价')
                prev_close = stock_row.get('昨收价')
                if pd.isna(latest_close) or pd.isna(prev_close) or prev_close == 0:
                    raise ValueError(f"无法计算涨跌幅，缺少最新价/昨收价。")
                value = ((latest_close - prev_close) / prev_close) * 100.0 # Guaranteed float
                found_col_name = '计算涨跌幅'
            else:
                COLUMN_MAP_US_SEARCH = {'open': 'open', 'high': 'high', 'low': 'low', 'close': '最新价', 'prev_close': '昨收价'}
                search_col = COLUMN_MAP_US_SEARCH.get(clean_column_label)
                if not search_col or search_col not in stock_row:
                    raise ValueError(f"US指数不支持查询 '{column_label}'，或缺少数据。")
                value = stock_row[search_col]
                found_col_name = search_col
        else:
            df_realtime = _fetch_index_spot_api(market_key, INDEX_API_MAP[market_key])
            if df_realtime is None:
                raise ValueError(f"无法从 API 获取 {market_key} 市场的实时数据快照。")
            code_col_name = '代码' if market_key in ['a_index', 'hk_index'] else 'symbol' 
            if code_col_name not in df_realtime.columns:
                code_col_name = 'code' 
                if code_col_name not in df_realtime.columns:
                    raise ValueError(f"实时数据 API 结构异常，缺少代码列。")
            match = df_realtime[df_realtime[code_col_name].astype(str).str.lower() == target_code.lower()]
            if match.empty:
                raise ValueError(f"在实时 API 数据中未能找到代码为 '{target_code}' 的记录。")
            stock_row = match.iloc[0]
            COLUMN_MAP_STD_TO_LOCAL = {
                'open': ['今开', '开盘', '开盘价'], 'high': ['最高', '最高价'],
                'low': ['最低', '最低价'], 'close': ['最新价'],
                'prev_close': ['昨收', '昨收价'], 'change': ['涨跌额'],
                'pct_change': ['涨跌幅'], 'volume': ['成交量'],
                'amount': ['成交额'], 'amplitude': ['振幅'],
                'time': ['时间', '最新行情时间', '日期'] 
            }
            local_col_names = COLUMN_MAP_STD_TO_LOCAL.get(clean_column_label)
            if not local_col_names:
                raise ValueError(f"查询的列标签 '{column_label}' 不受支持。")
            for col in local_col_names:
                if col in stock_row and pd.notna(stock_row[col]):
                    found_col_name = col
                    value = stock_row[found_col_name]
                    break
            if found_col_name == "N/A":
                raise ValueError(f"在记录中缺少或 '{column_label}' 的有效数据。")
            date_time_str = stock_row.get(COLUMN_MAP_STD_TO_LOCAL['time'][0], datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    except Exception as e:
        error_msg = str(e).replace('\n', ' ')
        return {"value": f"错误: {market_key} 实时查询失败。 {error_msg}"}
    if clean_column_label in ['pct_change', 'change', 'close', 'open', 'high', 'low']:
        if not isinstance(value, (float, int)):
            value = str(value)
        if isinstance(value, str):
            try:
                s_value = value.strip().rstrip('%').replace('+', '').replace(',', '')
                if not s_value or s_value == '—': 
                    value = 0.0
                else:
                    value = float(s_value)
            except ValueError:
                return {"value": f"错误: '{original_name}' 的数据 '{value}' 无法转换为数字进行比较。"}
    if pd.isna(value):
        return {"value": f"错误: '{original_name}' 的数据为空 (NaN)。"}
    _log_debug(f"--- [实时命中] 成功从 {market_key} 的 '{found_col_name}' 列获取到数据！---")
    return {
        "source": "akshare_spot_api", 
        "identifier": original_name,
        "column": column_label,
        "value": value, 
        "datetime": str(date_time_str)
    }
