import akshare as ak
import pandas as pd

from typing import Optional, Literal

from ..utils import _log_debug, _car_market_cache


def get_china_car_sales_cpca(
market_type: Literal["new_energy_vehicle", "passenger_car", "commercial_vehicle"],
    metric_type: Literal["sales", "production", "wholesale", "export"],
    query_month: str,
    query_year: Optional[int] = None
) -> str:
    """
    从乘联会(CPCA)查询中国汽车市场的月度销量/产量数据。
    可查询新能源市场或乘用车/商用车市场的具体指标。
    """
    global _car_market_cache
    cache_key = (market_type, metric_type)
    ak_params = {}
    api_func = None
    market_display_name = ""
    if market_type == "new_energy_vehicle":
        if metric_type != "sales":
            return f"错误: 当 market_type 为 'new_energy_vehicle' 时，metric_type 只能是 'sales'。"
        api_func = ak.car_market_fuel_cpca
        ak_params['symbol'] = "整体市场"
        market_display_name = "新能源汽车"
    else:
        api_func = ak.car_market_total_cpca
        symbol_map = {"passenger_car": "狭义乘用车", "commercial_vehicle": "广义乘用车"}
        indicator_map = {"sales": "零售", "production": "产量", "wholesale": "批发", "export": "出口"}
        ak_params['symbol'] = symbol_map.get(market_type)
        ak_params['indicator'] = indicator_map.get(metric_type)
        market_display_name = ak_params['symbol']
    try:
        if cache_key in _car_market_cache:
            df = _car_market_cache[cache_key]
            _log_debug(f"--- [函数缓存] 成功从缓存中读取数据: {cache_key} ---")
        else:
            _log_debug(f"--- [API 调用] 缓存未命中，正在下载数据: {cache_key} ---")
            df = api_func(**ak_params)
            if df.empty:
                return f"错误: 从接口获取 {cache_key} 数据失败，返回为空。"
            _car_market_cache[cache_key] = df
    except Exception as e:
        return f"错误: 调用 akshare 接口或处理数据时失败: {e}"
    try:
        year_columns = [col for col in df.columns if '年' in col]
        if not year_columns:
            return "错误: 未在返回的数据中找到年份列。"
        target_year_col = ""
        if query_year:
            target_year_col = f"{query_year}年"
        else:
            year_columns.sort()
            target_year_col = year_columns[-1]
        if target_year_col not in df.columns:
            return f"错误: 未找到年份 '{query_year}' 的数据。可用年份: {[col.replace('年','') for col in year_columns]}"
        month_match_str = query_month.replace('份', '').replace('月', '') + '月'
        target_row = df[df['月份'] == month_match_str]
        if target_row.empty:
            available_months = df['月份'].unique().tolist()
            return f"错误: 未找到月份 '{query_month}'。可用月份: {available_months}"
        value = target_row.iloc[0][target_year_col]
        if pd.isna(value):
            return f"在 {target_year_col} {month_match_str} 找到了记录，但数值为空（可能尚未公布）。"
        result_json = {
            "source": "乘联会(CPCA)",
            "market_type": market_display_name,
            "metric_type": metric_type,
            "time_period": {
                "year": int(target_year_col.replace('年','')),
                "month": month_match_str
            },
            "value": f"{value:,.2f}",
            "unit": "万辆"
        }
        return result_json
    except Exception as e:
        return f"查询时发生未知错误: {e}"
