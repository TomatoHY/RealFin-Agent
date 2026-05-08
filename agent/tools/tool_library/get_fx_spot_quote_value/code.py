import time

import akshare as ak

from typing import Optional

from ..utils import CACHE_TTL_SECONDS, _log_debug, _fx_spot_quote_cache


def get_fx_spot_quote_value(
currency_pair: str,
    metric_name: str
) -> Optional[float]:
    """
    获取外汇即期报价，支持交叉汇率计算。
    """
    global _fx_spot_quote_cache
    current_time = time.time()
    if (current_time - _fx_spot_quote_cache["timestamp"]) > CACHE_TTL_SECONDS:
        _log_debug("缓存已过期或首次查询，正在下载最新的外汇即期报价...")
        try:
            df = ak.fx_spot_quote()
            if df is not None and not df.empty:
                df.set_index('货币对', inplace=True)
                _fx_spot_quote_cache["data"] = df
                _fx_spot_quote_cache["timestamp"] = current_time
        except Exception as e:
            _log_debug(f"下载: {e}")
            _fx_spot_quote_cache["timestamp"] = current_time
            return None
    df = _fx_spot_quote_cache["data"]
    if df is None:
        return None
    try:
        row_data = df.loc[currency_pair]
        value = float(row_data[metric_name])
        result_json = {
            "query_type": "direct_quote",
            "currency_pair": currency_pair,
            "requested_metric": {
                "name": metric_name,
                "value": value
            },
            "full_quote": {
                "bid_price": float(row_data.get('买报价')),
                "ask_price": float(row_data.get('卖报价')),
                "high_price": float(row_data.get('最高')),
                "low_price": float(row_data.get('最低')),
                "open_price": float(row_data.get('今开')),
                "previous_close": float(row_data.get('昨收'))
            }
        }
        return result_json
    except KeyError:
        _log_debug(f"直接查询 '{currency_pair}' 失败，尝试计算交叉汇率...")
    try:
        curr1, curr2 = currency_pair.upper().split('/')
        pair1_buy = df.loc[f'{curr1}/CNY', '买报价']
        pair1_sell = df.loc[f'{curr1}/CNY', '卖报价']
        try:
            pair2_buy = df.loc[f'CNY/{curr2}', '买报价']
            pair2_sell = df.loc[f'CNY/{curr2}', '卖报价']
        except KeyError:
            pair2_inverted_buy = df.loc[f'{curr2}/CNY', '买报价']
            pair2_inverted_sell = df.loc[f'{curr2}/CNY', '卖报价']
            pair2_buy = 1 / pair2_inverted_sell
            pair2_sell = 1 / pair2_inverted_buy
        cross_rate_buy = pair1_buy * pair2_buy
        cross_rate_sell = pair1_sell * pair2_sell
        _log_debug(f"成功计算交叉汇率 {currency_pair}: 买价={cross_rate_buy}, 卖价={cross_rate_sell}")
        requested_value = None
        if metric_name == '买报价':
            requested_value = float(cross_rate_buy)
        elif metric_name == '卖报价':
            requested_value = float(cross_rate_sell)
        else:
            return f"注意：交叉汇率计算仅支持 '买报价' 和 '卖报价'，不支持 '{metric_name}'。"
        result_json = {
            "query_type": "cross_rate_calculation",
            "currency_pair": currency_pair,
            "requested_metric": {
                "name": metric_name,
                "value": requested_value
            },
            "full_quote": {
                "bid_price": float(cross_rate_buy),
                "ask_price": float(cross_rate_sell)
            }
        }
        return result_json
    except Exception as e:
        return f"计算交叉汇率 '{currency_pair}' 失败: {e},可用货币对包括: {df.index.tolist()}."
