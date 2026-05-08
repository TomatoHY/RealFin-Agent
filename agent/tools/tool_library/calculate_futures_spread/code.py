import akshare as ak
import pandas as pd

from datetime import datetime

from ..utils import _log_debug


def calculate_futures_spread(
symbol1: str,
    symbol2: str,
    start_date: str,
    end_date: str
) -> str:
    """
    计算两种期货合约在指定时间段内的【每日价差 (symbol2 - symbol1)】，
    并找出价差的最大值、最小值及其对应的日期。
    """
    try:
        _log_debug(f"--- 正在获取大连商品交易所(DCE)从 {start_date} 到 {end_date} 的全部日线数据... ---")
        market_df = ak.get_futures_daily(start_date=start_date, end_date=end_date, market="DCE")
        if market_df.empty:
            return f"错误: 未能获取到在 {start_date} 到 {end_date} 期间大连商品交易所的任何数据。"
        df1 = market_df[market_df['symbol'] == symbol1].copy()
        if df1.empty:
            return f"错误: 在获取到的市场数据中，未能找到合约 '{symbol1}' 的记录。"
        df2 = market_df[market_df['symbol'] == symbol2].copy()
        if df2.empty:
            return f"错误: 在获取到的市场数据中，未能找到合约 '{symbol2}' 的记录。"
        df1['date'] = pd.to_datetime(df1['date'])
        df2['date'] = pd.to_datetime(df2['date'])
        df1.set_index('date', inplace=True)
        df2.set_index('date', inplace=True)
        df1_close = df1[['close']].rename(columns={'close': f'close_{symbol1}'})
        df2_close = df2[['close']].rename(columns={'close': f'close_{symbol2}'})
        merged_df = pd.merge(df1_close, df2_close, left_index=True, right_index=True, how='inner')
        if merged_df.empty:
            return "错误: 两种合约在指定时间段内没有共同的交易日，无法计算价差。"
        merged_df['spread'] = merged_df[f'close_{symbol2}'] - merged_df[f'close_{symbol1}']
        max_spread_row = merged_df.loc[merged_df['spread'].idxmax()]
        max_spread_value = max_spread_row['spread']
        max_spread_date = max_spread_row.name.strftime('%Y-%m-%d')
        min_spread_row = merged_df.loc[merged_df['spread'].idxmin()]
        min_spread_value = min_spread_row['spread']
        min_spread_date = min_spread_row.name.strftime('%Y-%m-%d')
        start_date_display = datetime.strptime(start_date, '%Y%m%d').strftime('%Y-%m-%d')
        end_date_display = datetime.strptime(end_date, '%Y%m%d').strftime('%Y-%m-%d')
        result_json = {
            "analysis_type": "futures_spread",
            "symbol_base": symbol1,
            "symbol_target": symbol2,
            "calculation_formula": f"{symbol2} - {symbol1}",
            "query_period_start": start_date_display,
            "query_period_end": end_date_display,
            "max_spread": {
                "value": f"{max_spread_value:.2f}",
                "date": max_spread_date
            },
            "min_spread": {
                "value": f"{min_spread_value:.2f}",
                "date": min_spread_date
            }
        }
        return result_json
    except Exception as e:
        import traceback
        return f"计算期货价差时发生未知错误: {e}\n{traceback.format_exc()}"
