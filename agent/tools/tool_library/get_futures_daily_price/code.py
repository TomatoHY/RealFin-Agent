import re

import akshare as ak
import pandas as pd

from datetime import datetime
from typing import Optional


def get_futures_daily_price(
symbol: str, 
    start_date: str, 
    end_date: Optional[str] = None
) -> str:
    """
    获取指定期货合约在特定日期范围内的日线行情数据。
    在查询前会严格校验日期是否为有效交易日。
    """
    try:
        if not end_date:
            end_date = start_date
        try:
            recent_trades_df = ak.futures_inventory_em(symbol="螺纹钢")
            if recent_trades_df.empty:
                raise Exception("无法通过东方财富库存接口获取最新的交易日信息。")
            most_recent_trade_date_str = recent_trades_df['日期'].iloc[-1]
            most_recent_trade_date_obj = pd.to_datetime(most_recent_trade_date_str).date()
            request_date_obj = datetime.strptime(start_date, "%Y%m%d").date()
        except ValueError:
            return f"错误：日期格式不正确 '{start_date}'。请使用 'YYYYMMDD' 格式。"
        except Exception as e:
            return f"获取或解析最新交易日时发生错误: {e}"
        if request_date_obj > most_recent_trade_date_obj:
            return (
                f"错误：您请求的日期 '{start_date}' 是一个未来的日期。\n"
                f"指令：请立即放弃当前尝试，并使用已知的最近一个有效交易日 '{most_recent_trade_date_obj.strftime('%Y%m%d')}' 重新发起一次新的查询。"
            )
        markets = ["CFFEX", "SHFE", "DCE", "CZCE", "GFEX", "INE"]
        all_dfs = []
        for market in markets:
            try:
                df_market = ak.get_futures_daily(start_date=start_date, end_date=end_date, market=market)
                all_dfs.append(df_market)
            except Exception:
                continue
        if not all_dfs or pd.concat(all_dfs).empty:
            return f"错误：在有效的日期 '{start_date}' 无法获取任何期货数据。这很可能是一个节假日。\n指令：请更换一个有效的交易日重试。"
        df_all_markets = pd.concat(all_dfs)
        df = df_all_markets[df_all_markets['symbol'] == symbol]
        if not df.empty:
            df_copy = df.copy()
            for col in ['open', 'high', 'low', 'close', 'volume', 'open_interest', 'turnover', 'settle', 'pre_settle']:
                if col in df_copy.columns:
                    df_copy[col] = pd.to_numeric(df_copy[col], errors='coerce')
            
            df_copy['date'] = pd.to_datetime(df_copy['date']).dt.strftime('%Y-%m-%d')
            json_result = df_copy.to_json(orient="records", force_ascii=False, indent=2)
            return json_result
        else:
            match = re.match(r'([a-zA-Z]+)', symbol.lower())
            if not match: 
                return f"查询成功，但在有效交易日 '{start_date}' 未找到合约 '{symbol}' 的数据。"
            base_symbol = match.group(1)
            master_list_df = ak.futures_comm_info(symbol="所有")
            commodity_df = master_list_df[master_list_df['合约代码'].str.lower().str.startswith(base_symbol)]
            if commodity_df.empty:
                return f"查询成功，但未找到合约 '{symbol}' 的数据，也未在当前市场中找到任何与品种 '{base_symbol}' 相关的合约。"
            else:
                available_codes = commodity_df['合约代码'].unique().tolist()
                if available_codes:
                    probe_symbol = available_codes[0]
                    probe_df = df_all_markets[df_all_markets['symbol'] == probe_symbol]
                    if probe_df.empty:
                        return (
                            f"错误：在日期 '{start_date}'，您查询的品种 '{base_symbol}' (包括合约 {symbol}, {probe_symbol} 等) 似乎整体休市或所有合约均未开始交易。\n"
                            f"指令：请更换一个有效的交易日重试，或者更换一个商品品种进行查询。"
                        )
                return (
                    f"错误：合约代码 '{symbol}' 在有效的交易日 '{start_date}' 内没有数据。\n"
                    f"原因可能是该合约已退市或尚未上市。指令：请从以下 '{base_symbol}' 品种的可用合约列表中选择一个，并使用相同的有效日期 '{start_date}' 重试本函数。\n"
                    f"可用合约列表: {available_codes}"
                )
    except Exception as e:
        import traceback
        return f"获取期货日线数据时发生未知错误: {e}\n{traceback.format_exc()}"
