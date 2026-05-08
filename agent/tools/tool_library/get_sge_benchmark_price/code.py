import akshare as ak
import pandas as pd

from typing import Literal

from ..utils import _log_debug, _benchmark_cache


def get_sge_benchmark_price(
    metal: Literal["gold", "silver"],
    session: Literal["morning", "evening"],
    query_date: str = "latest"
) -> str:
    """
    查询上海黄金交易所(SGE)的【上海金】或【上海银】在特定日期的基准价。
    可指定查询早盘价(morning session)或晚盘价(evening session)。
    默认查询最新(latest)的交易日数据。
    """
    global _benchmark_cache
    api_map = {
        "gold": ak.spot_golden_benchmark_sge,
        "silver": ak.spot_silver_benchmark_sge
    }
    column_map = {
        "morning": "早盘价", # 午盘价，即早盘价
        "evening": "晚盘价"
    }
    metal_display_name = "上海金" if metal == "gold" else "上海银"
    session_display_name = "早盘(午盘)" if session == "morning" else "晚盘"
    try:
        if metal not in _benchmark_cache:
            _log_debug(f"--- [API 调用] 缓存未命中，正在通过 akshare 下载【{metal_display_name}】的全部历史基准价数据... ---")
            df = api_map[metal]()
            if df.empty:
                return f"错误: 从接口获取 '{metal_display_name}' 数据失败，返回为空。"
            df['交易时间'] = pd.to_datetime(df['交易时间'])
            df.set_index('交易时间', inplace=True)
            df.sort_index(ascending=True, inplace=True) 
            _benchmark_cache[metal] = df
        df = _benchmark_cache[metal]
        _log_debug(f"--- [函数缓存] 成功从缓存中读取【{metal_display_name}】数据。 ---")
    except Exception as e:
        return f"错误: 调用 akshare 接口或处理数据时失败: {e}"
    target_column = column_map[session]
    try:
        if query_date.lower() == "latest":
            latest_data = df.iloc[-1]
            price = latest_data[target_column]
            actual_date = latest_data.name.strftime('%Y-%m-%d')
        else:
            try:
                target_date = pd.to_datetime(query_date)
            except ValueError:
                return f"错误: 日期格式 '{query_date}' 无效。请使用 'YYYY-MM-DD' 格式或 'latest'。"
            closest_data = df.asof(target_date)
            if closest_data is None:
                min_date = df.index.min().strftime('%Y-%m-%d')
                return f"错误: 未能找到在 '{query_date}' 或此日期之前的任何有效数据。最早可用数据日期为 {min_date}。"
            price = closest_data[target_column]
            actual_date = closest_data.name.strftime('%Y-%m-%d')
        if pd.isna(price):
            return f"在 {actual_date} 找到了 {metal_display_name} 的记录，但其【{session_display_name}价】为空值。"
        result_json = {
            "source": "上海黄金交易所(SGE)",
            "benchmark_type": metal_display_name,
            "session": session_display_name,
            "date": actual_date,
            "price": float(price)
        }
        return result_json
    except KeyError:
        return f"错误: 数据源中缺少必需的列 '{target_column}'。"
    except Exception as e:
        return f"查询价格时发生未知错误: {e}"
