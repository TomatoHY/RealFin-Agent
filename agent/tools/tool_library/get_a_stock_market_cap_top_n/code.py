import akshare as ak
import pandas as pd

from typing import Literal

from ..utils import CACHE_TTL_SECONDS, _log_debug, _spot_market_cache


def get_a_stock_market_cap_top_n(
market: Literal["all", "sh", "sz", "bj"],
    n: int,
    cap_type: Literal["total", "circulating"],
    include_prices: bool = False
) -> str:
    """
    查询A股指定市场中，按市值排名前 N 的股票列表。
    可选择性地在结果中包含最新价和开盘价。
    """
    global _spot_market_cache
    if not isinstance(n, int) or n <= 0: return f"错误: 'n' 参数必须是一个正整数。"
    api_map = {"all": ak.stock_zh_a_spot_em, "sh": ak.stock_sh_a_spot_em, "sz": ak.stock_sz_a_spot_em, "bj": ak.stock_bj_a_spot_em}
    cap_column_map = {"total": "总市值", "circulating": "流通市值"}
    sort_column = cap_column_map[cap_type]
    market_name_map = {"all": "沪深京A股", "sh": "沪市", "sz": "深市", "bj": "京市"}
    market_display_name = market_name_map[market]
    df = pd.DataFrame()
    current_time = pd.Timestamp.now().timestamp()
    if market in _spot_market_cache and (current_time - _spot_market_cache[market][1]) < CACHE_TTL_SECONDS:
        df = _spot_market_cache[market][0]
        _log_debug(f"--- [函数缓存] 成功从缓存中读取 '{market_display_name}' 实时数据。 ---")
    else:
        _log_debug(f"--- [API 调用] 正在通过 akshare 下载 '{market_display_name}' 实时数据... ---")
        try:
            df = api_map[market]()
            if df.empty: return f"错误: 从接口获取 '{market_display_name}' 数据失败，返回为空。"
            _spot_market_cache[market] = (df, current_time)
        except Exception as e: return f"错误: 调用 akshare 接口获取 '{market_display_name}' 数据时失败: {e}"
    try:
        if sort_column not in df.columns: return f"错误: 数据源中缺少用于排序的列 '{sort_column}'。"
        top_n_df = df.sort_values(by=sort_column, ascending=False, na_position='last').head(n)
        if top_n_df.empty: return f"在 '{market_display_name}' 市场中未能找到任何有效的股票数据进行排名。"
    except Exception as e: return f"处理数据排序时发生错误: {e}"
    top_stocks_list = []
    for index, row in top_n_df.iterrows():
        market_value = row[sort_column]
        market_value_in_billion = market_value / 1_0000_0000
        stock_info = {
            "rank": index + 1,
            "code": row.get('代码'),
            "name": row.get('名称'),
            "market_cap": f"{market_value_in_billion:,.2f} 亿元"
        }
        if include_prices:
            stock_info["latest_price"] = row.get('最新价', 'N/A')
            stock_info["open_price"] = row.get('今开', 'N/A')
            
        top_stocks_list.append(stock_info)
    result_json = {
        "analysis_type": "market_cap_ranking",
        "market": market_display_name,
        "ranking_basis": sort_column,
        "top_n": n,
        "ranking_results": top_stocks_list 
    }
    return result_json
