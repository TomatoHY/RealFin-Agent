import json
import os
import pickle
import re
import time
import traceback
import unicodedata
import unittest

import akshare as ak
import numpy as np
import pandas as pd
import requests

from datetime import datetime, timedelta, date
from functools import lru_cache
from io import StringIO
from typing import Optional, Any, Dict, Callable, Tuple, Union, List, Literal

from ..utils import _fail_minute_spread, _log_debug


def calculate_futures_minute_spread(
symbol1: str,
    symbol2: str,
    period: str = "1"
) -> Dict[str, Any]:
    """
    计算两种期货合约在【当日分钟线】上的价差 (symbol2 - symbol1)，
    并找出价差的最大值、最小值及其对应的分钟。
    """
    try:
        s1_upper = symbol1.upper()
        s2_upper = symbol2.upper()
        _log_debug(f"--- [分钟查询] 正在获取 {s1_upper} (周期: {period}min) 的分时数据... ---")
        df1 = ak.futures_zh_minute_sina(symbol=s1_upper, period=period)
        if df1 is None or df1.empty:
            return _fail_minute_spread(f"错误: 未能获取到 {s1_upper} 的分时数据。")
        time.sleep(30) 
        _log_debug(f"--- [分钟查询] 正在获取 {s2_upper} (周期: {period}min) 的分时数据... ---")
        df2 = ak.futures_zh_minute_sina(symbol=s2_upper, period=period)
        if df2 is None or df2.empty:
            return _fail_minute_spread(f"错误: 未能获取到 {s2_upper} 的分时数据。")
        df1['datetime'] = pd.to_datetime(df1['datetime'])
        df2['datetime'] = pd.to_datetime(df2['datetime'])
        df_merged = pd.merge(
            df1[['datetime', 'close']], 
            df2[['datetime', 'close']], 
            on='datetime', 
            suffixes=(f'_{s1_upper}', f'_{s2_upper}')
        )
        if df_merged.empty:
            return _fail_minute_spread("错误: 两种合约在当日分时数据中没有共同的时间戳，无法计算价差。")
        df_merged['spread'] = df_merged[f'close_{s2_upper}'] - df_merged[f'close_{s1_upper}']
        max_spread_row = df_merged.loc[df_merged['spread'].idxmax()]
        max_spread_value = max_spread_row['spread']
        max_spread_datetime = max_spread_row['datetime'].strftime('%Y-%m-%d %H:%M:%S')
        min_spread_row = df_merged.loc[df_merged['spread'].idxmin()]
        min_spread_value = min_spread_row['spread']
        min_spread_datetime = min_spread_row['datetime'].strftime('%Y-%m-%d %H:%M:%S')
        result_json = {
            "analysis_type": "futures_minute_spread",
            "symbol_base": symbol1,
            "symbol_target": symbol2,
            "calculation_formula": f"{symbol2} - {symbol1}",
            "max_spread": {
                "value": float(max_spread_value),
                "date": max_spread_datetime # [注意] 键是 'date', 但值是 'datetime'
            },
            "min_spread": {
                "value": float(min_spread_value),
                "date": min_spread_datetime
            }
        }
        return result_json
    except Exception as e:
        return _fail_minute_spread(f"计算期货(分钟)价差时发生未知异常: {e}\n{traceback.format_exc()}")
