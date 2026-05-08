import akshare as ak
import pandas as pd

from typing import Optional

from ..utils import _log_debug, _long_stock_financial_cache


def get_stock_long_short_term_investment(
symbol: str, 
    query_date: str,
    investment_type: str = "long",  
    name: Optional[str] = None
) -> str:
    """
    查询A股公司在指定报告期的【长期股票投资】或【短期股票投资】金额（单位：元）。
    数据来源于新浪财经-财务指标接口（ak.stock_financial_analysis_indicator）。
    
    :param symbol: 股票代码（6位数字），例如 '600048'。
    :param query_date: 要查询的具体报告期，格式 'YYYY-MM-DD'。函数将返回该报告期的值。
    :param investment_type: 查询的投资类型。必须是 "long"（长期）或 "short"（短期），默认为 "long"。
    :param name: [可选] 股票的中文名称。
    :return: 返回查询到的具体数值（元）或错误信息。
    """
    global _long_stock_financial_cache
    if not symbol and name:
        return f"错误：请直接提供股票代码，或确保 get_code_from_name 函数可用。"
    if not symbol:
        return f"错误：未能找到股票 '{name}' 的A股代码。"
    if investment_type.lower() == "long":
        TARGET_COLUMN = "长期股票投资(元)"
    elif investment_type.lower() == "short":
        TARGET_COLUMN = "短期股票投资(元)"
    else:
        return f"错误：投资类型 '{investment_type}' 无效，请使用 'long' 或 'short'。"
    try:
        query_date_dt = pd.to_datetime(query_date)
        start_year = str(query_date_dt.year - 5) 
    except ValueError:
        return f"错误：日期格式 '{query_date}' 无效，请使用 'YYYY-MM-DD' 格式。"
    cache_key = (symbol, start_year)
    try:
        if cache_key in _long_stock_financial_cache:
            df = _long_stock_financial_cache[cache_key]
            _log_debug(f"缓存命中，使用股票 {symbol} 从 {start_year} 以来已缓存的财务指标数据。")
        else:
            _log_debug(f"缓存未命中，正在下载股票 {symbol} 从 {start_year} 以来的财务指标历史数据...")
            df = ak.stock_financial_analysis_indicator(symbol=symbol, start_year=start_year)
            if df is None or df.empty or '日期' not in df.columns:
                return f"错误：未能获取股票 {symbol} 从 {start_year} 以来的财务指标数据。"
            _long_stock_financial_cache[cache_key] = df
            _log_debug("数据缓存成功。")
        df['日期'] = pd.to_datetime(df['日期'])
        if TARGET_COLUMN not in df.columns:
            return f"错误：接口返回的数据中不包含指标 '{TARGET_COLUMN}'。请检查接口文档。"
        target_row = df[df['日期'] == query_date_dt]
        if target_row.empty: 
            return f"查询失败: 股票 {symbol} 在报告期 {query_date} 未找到 {TARGET_COLUMN} 的数据。"
        value = target_row.iloc[0][TARGET_COLUMN]
        if pd.isna(value):
            return f"股票 {symbol} 在 {query_date} 报告期的 {TARGET_COLUMN} 值为: 无数据 (NaN)。"
        result_json = {
            "stock_identifier": name or symbol,
            "report_date": query_date,
            "data_source": "Financial Analysis Indicators",
            "item_name": TARGET_COLUMN,
            "value": float(value),
            "unit": "元"
        }
        return result_json
    except Exception as e:
        return f"查询 {TARGET_COLUMN} 数据时出错: {e}"
