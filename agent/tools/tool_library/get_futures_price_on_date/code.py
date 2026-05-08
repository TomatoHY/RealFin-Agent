import re
import traceback

import akshare as ak
import pandas as pd

from datetime import datetime
from typing import Any, Dict, Union

from ..utils import _log_debug


def get_futures_price_on_date(
    symbol: str, 
    query_date: str
) -> Union[Dict[str, Any], str]:
    """
    获取指定期货合约在【某一个指定日期】的日线行情数据。
    
    :param symbol: 要查询的期货合约代码, 例如 "rb2401"。
    :param query_date: 要查询的日期, 格式 'YYYYMMDD' (注意: 与其他工具不同, 此处遵循akshare API)。
    :return: 一个包含该日所有行情数据的字典, 或一个错误信息字符串。
    """
    _log_debug(f"--- [期货单日查询] 正在获取 '{symbol}' 在 {query_date} 的数据... ---")
    try:
        try:
            recent_trades_df = ak.futures_inventory_em(symbol="螺纹钢") 
            if recent_trades_df.empty:
                raise Exception("无法通过东方财富库存接口获取最新的交易日信息。")
            most_recent_trade_date_str = recent_trades_df['日期'].iloc[-1]
            most_recent_trade_date_obj = pd.to_datetime(most_recent_trade_date_str).date()
            request_date_obj = datetime.strptime(query_date, "%Y%m%d").date()
        except ValueError:
            return f"错误：日期格式不正确 '{query_date}'。请使用 'YYYYMMDD' 格式。"
        except Exception as e:
            return f"获取或解析最新交易日时发生错误: {e}"
        if request_date_obj > most_recent_trade_date_obj:
            return (
                f"错误：您请求的日期 '{query_date}' 是一个未来的日期。\n"
                f"指令：请立即放弃当前尝试，并使用已知的最近一个有效交易日 '{most_recent_trade_date_obj.strftime('%Y%m%d')}' 重新发起一次新的查询。"
            )
        markets = ["CFFEX", "SHFE", "DCE", "CZCE", "GFEX", "INE"]
        all_dfs = []
        for market in markets:
            try:
                df_market = ak.get_futures_daily(start_date=query_date, end_date=query_date, market=market)
                all_dfs.append(df_market)
            except Exception:
                continue
        if not all_dfs or pd.concat(all_dfs).empty:
            return f"错误：在有效的日期 '{query_date}' 无法获取任何期货数据。这很可能是一个节假日。\n指令：请更换一个有效的交易日重试。"
        df_all_markets = pd.concat(all_dfs)
        df = df_all_markets[df_all_markets['symbol'] == symbol]
        if not df.empty:
            data_series = df.iloc[0]
            result_dict = data_series.to_dict()
            for col in ['open', 'high', 'low', 'close', 'volume', 'open_interest', 'turnover', 'settle', 'pre_settle']:
                if col in result_dict:
                    result_dict[col] = pd.to_numeric(result_dict[col], errors='coerce')
            result_dict['date'] = pd.to_datetime(result_dict['date']).dt.strftime('%Y-%m-%d')
            return result_dict
        else:
            match = re.match(r'([a-zA-Z]+)', symbol.lower())
            if not match: 
                return f"查询成功，但在有效交易日 '{query_date}' 未找到合约 '{symbol}' 的数据。"
            base_symbol = match.group(1)
            master_list_df = ak.futures_comm_info(symbol="所有")
            commodity_df = master_list_df[master_list_df['合约代码'].str.lower().str.startswith(base_symbol)]
            if commodity_df.empty:
                return f"查询成功，但未找到合约 '{symbol}' 的数据，也未在当前市场中找到任何与品种 '{base_symbol}' 相关的合约。"
            else:
                available_codes = commodity_df['合约代码'].unique().tolist()
                return (
                    f"错误：合约代码 '{symbol}' 在有效的交易日 '{query_date}' 内没有数据。\n"
                    f"原因可能是该合约已退市或尚未上市。指令：请从以下 '{base_symbol}' 品种的可用合约列表中选择一个，并使用相同的有效日期 '{query_date}' 重试本函数。\n"
                    f"可用合约列表: {available_codes}"
                )
    except Exception as e:
        return f"获取期货日线数据时发生未知错误: {e}\n{traceback.format_exc()}"
