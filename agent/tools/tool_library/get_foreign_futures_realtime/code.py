import akshare as ak

from ..utils import _log_debug, _normalize_name, FOREIGN_FUTURES_ALIAS_MAP


def get_foreign_futures_realtime(
    commodity_name: str,
    column_label: str
) -> str:
    """
    【国际期货/实时专用】获取指定国际大宗商品的【最新实时行情数据】。
    """
    try:
        normalized_input = _normalize_name(commodity_name)
        target_name = FOREIGN_FUTURES_ALIAS_MAP.get(normalized_input)

        if not target_name:
            return (f"错误：未能识别的国际期货品种 '{commodity_name}'。"
                    f"请尝试使用标准名称，如 'WTI Crude Oil', 'COMEX Gold', 'Brent' 等。")
        _log_debug(f"--- [国际期货] 正在获取所有国际期货的实时快照... ---")
        try:
            all_symbols_list = ak.futures_foreign_commodity_subscribe_exchange_symbol()
            if not all_symbols_list:
                return "错误：无法获取国际期货的商品代码列表。"
            realtime_df = ak.futures_foreign_commodity_realtime(symbol=all_symbols_list)
        except Exception as e:
            return f"错误：调用 akshare 底层接口 'futures_foreign_commodity_realtime' 失败: {e}"
        if realtime_df.empty:
            return "错误：调用 futures_foreign_commodity_realtime 接口未能返回任何数据。"
        match_df = realtime_df[realtime_df['名称'] == target_name]
        if match_df.empty:
            available_commodities = realtime_df['名称'].unique().tolist()
            return (f"错误：在实时数据中未找到 '{target_name}' (您查询的是 '{commodity_name}')。\n"
                    f"当前可用的品种列表为: {available_commodities}")
        column_map = {
            'name': '名称', 'close': '最新价', 'price_cny': '人民币报价',
            'change': '涨跌额', 'change_percent': '涨跌幅', 'open': '开盘价',
            'high': '最高价', 'low': '最低价', 'previous_settle': '昨日结算价',
            'open_interest': '持仓量', 'bid': '买价', 'ask': '卖价',
            'time': '行情时间', 'date': '日期',
        }
        if column_label not in column_map:
            return f"错误：列 '{column_label}' 无效。有效列为: {list(column_map.keys())}"
        actual_column = column_map[column_label]
        if actual_column not in match_df.columns:
            return f"错误：数据源中不存在名为 '{actual_column}' 的列。"
        row_data = match_df.iloc[0]
        value = row_data[actual_column]
        result_json = {
            "commodity_name": row_data.get('名称'),
            "data_type": "latest_realtime",
            "requested_item": {
                "label": column_label,
                "value": value
            },
            "realtime_quote": {
                "latest_price": row_data.get('最新价'),
                "price_cny": row_data.get('人民币报价'),
                "change_value": row_data.get('涨跌额'),
                "change_percent": row_data.get('涨跌幅'),
                "open_price": row_data.get('开盘价'),
                "high_price": row_data.get('最高价'),
                "low_price": row_data.get('最低价'),
                "previous_settle": row_data.get('昨日结算价'),
                "quote_time": f"{row_data.get('日期')} {row_data.get('行情时间')}"
            }
        }
        return result_json
    except Exception as e:
        return f"获取国际期货实时数据时发生未知错误: {e}"
