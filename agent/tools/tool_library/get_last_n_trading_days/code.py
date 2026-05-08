import pandas as pd

from datetime import datetime
from typing import Optional, Any, Dict

from ..get_code_from_name import get_code_from_name
from ..utils import _fetch_a_history_hybrid, _log_debug


def get_last_n_trading_days(
    code: Optional[str] = None,
    name: Optional[str] = None,
    n: int = 3,
    adjust: str = "",
    column_label: str = "close",
    select_index: Optional[int] = None
) -> Dict[str, Any]:
    """
    获取最近 n 个交易日的日期及对应的指定列值（例如收盘价）。

    参数:
    - code: 股票代码，优先使用
    - name: 股票名称
    - n: 返回最近 n 个交易日
    - adjust: 复权类型 '', 'qfq', 'hfq'
    - column_label: 要查询的列名，例如 'close' 或 '收盘'
    - select_index: [可选] 若提供，则在获取最近 n 个交易日后，
    按日期从新到旧排序，并仅返回 trading_days[select_index]
    对应的单个数值（索引从 0 开始，0 表示最新交易日）。
    若不提供该参数，则保持原有行为，返回完整 trading_days 列表。
    表示“前 N 个交易日”（最新交易日不计入），
    内部将自动映射为 trading_days[N-1]（0-based）。


    返回:
    {
        "trading_days": [
            {"date": "2025-12-12", "value": 15.23},
            {"date": "2025-12-11", "value": 15.10},
            {"date": "2025-12-10", "value": 14.98}
        ],
        "stock_identifier": "000001"
    }
    """
    # 列名映射（与 get_a_stock_daily_price 保持一致）
    COLUMN_MAPPING = {
        'open': '开盘', 'high': '最高', 'low': '最低', 'close': '收盘',
        'volume': '成交量', 'amount': '成交额',
        '开盘': '开盘', '最高': '最高', '最低': '最低',
        '收盘': '收盘', '最新价': '收盘', 
        '成交量': '成交量', '成交额': '成交额',
    }
    
    def _fail(error_msg: str) -> Dict[str, Any]:
        return {"error": error_msg}
    
    if adjust not in ['', 'qfq', 'hfq']:
        return _fail(f"错误: 'adjust' 参数 '{adjust}' 无效。")
    if not code and not name:
        return _fail("错误: 必须提供股票代码 (code) 或股票名称 (name)。")
    
    identifier = name if name else code
    resolved_symbol = None
    resolved_ts_code = None
    resolved_ak_code = None
    
    try:
        if code:
            resolved_symbol = str(code)
        elif name:
            _log_debug(f"--- [最近N交易日] 'code' 未提供, 正在使用 'name' ({name}) 从 [本地缓存] 查找代码... ---")
            found_code = get_code_from_name(name=name, market='a')
            if not found_code or "--- [LocalSearch] 查找" in str(found_code):
                return _fail(f"错误: 无法通过名称 '{name}' 从 [本地缓存] 找到对应的股票代码。{found_code}")
            resolved_symbol = str(found_code)
        if not resolved_symbol:
            return _fail(f"错误: 无法解析 '{identifier}' 为有效的股票代码。")
        if resolved_symbol.startswith('sh'):
            resolved_ak_code = resolved_symbol[2:]
            resolved_ts_code = resolved_ak_code + ".SH"
        elif resolved_symbol.startswith('sz'):
            resolved_ak_code = resolved_symbol[2:]
            resolved_ts_code = resolved_ak_code + ".SZ"
        elif resolved_symbol.startswith('bj'):
            resolved_ak_code = resolved_symbol[2:]
            resolved_ts_code = resolved_ak_code + ".BJ"
        else:
            return _fail(f"错误: 解析的代码 '{resolved_symbol}' 缺少 'sh', 'sz' 或 'bj' 前缀。")
    except Exception as e:
        return _fail(f"在为 '{identifier}' 解析代码时失败: {e}")
    
    # 映射列名
    clean_column_label = column_label.lower().strip()
    hist_col = COLUMN_MAPPING.get(clean_column_label)
    if not hist_col:
        return _fail(f"错误: 列名 '{column_label}' 无效。支持的列名: open, close, high, low, volume, amount 或对应的中文名称")
    
    # 获取历史数据（使用 "19700101" 作为 start_date 以确保备用源可用）
    # 注意：_fetch_a_history 只有在 start_date == "19700101" 时才会尝试备用源
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = "19700101"  # 使用这个值以确保备用源可用
    
    try:
        # 直接调用 _fetch_a_history_hybrid 获取 DataFrame（与 get_a_stock_daily_price 内部逻辑一致）
        # 注意：_fetch_a_history_hybrid 内部会处理日期格式，可以接受 'YYYY-MM-DD' 或 'YYYYMMDD'
        # 但 _fetch_a_history 需要 start_date == "19700101" 才会尝试备用源
        end_date_fmt = end_date.replace("-", "") if "-" in end_date else end_date
        
        _log_debug(f"--- [最近N交易日] 正在获取 '{resolved_symbol}' 的历史数据（到 {end_date}）... ---")
        df_hist, source = _fetch_a_history_hybrid(
            resolved_symbol=resolved_symbol,
            resolved_ts_code=resolved_ts_code,
            resolved_ak_code=resolved_ak_code,
            adjust=adjust,
            start_date=start_date,      # 使用 "19700101" 以确保备用源可用
            end_date=end_date_fmt       # 传入 'YYYYMMDD' 格式
        )
        
        if df_hist is None or df_hist.empty:
            return _fail(f"错误: 所有历史源均无法获取 '{identifier}' (代码: {resolved_symbol}) 的历史数据。请检查股票代码是否正确。")
        
        # 检查列是否存在
        if hist_col not in df_hist.columns:
            valid_cols = [col for col in ['开盘','收盘','最高','最低','成交量','成交额'] if col in df_hist.columns]
            return _fail(f"错误: 指定列 '{hist_col}' 不存在于历史数据中。可用列: {valid_cols}")
        
        # 处理日期列（_fetch_a_history_hybrid 返回的日期已经是字符串格式 'YYYY-MM-DD'）
        if '日期' not in df_hist.columns:
            return _fail("错误: 历史数据中缺少 '日期' 列")
        
        # 转换日期为 datetime 以便排序
        df_hist['日期_dt'] = pd.to_datetime(df_hist['日期'])
        df_hist[hist_col] = pd.to_numeric(df_hist[hist_col], errors='coerce')
        df_hist = df_hist.dropna(subset=[hist_col, '日期_dt'])
        
        if df_hist.empty:
            return _fail("错误: 历史数据中没有有效记录")
        
        # 按日期排序，取最近 n 个交易日
        df_hist = df_hist.sort_values('日期_dt', ascending=False)
        last_n_rows = df_hist.head(n)
        
        trading_days = [
            {"date": row['日期'], "value": float(row[hist_col])}
            for _, row in last_n_rows.iterrows()
        ]

        if select_index is not None:
            if not isinstance(select_index, int):
                return _fail("错误: 'select_index' 必须是非负整数。")
            if select_index < 0 or select_index >= len(trading_days):
                return _fail(
                    f"错误: 'select_index'={select_index} 超出范围。"
                    f"当前可用范围是 [0, {len(trading_days) - 1}]。"
                )
            selected = trading_days[select_index]
            return {
                "selected": {
                    "index": select_index,
                    "date": selected["date"],
                    "value": selected["value"]
                },
                "stock_identifier": resolved_symbol
            }
        
        return {
            "trading_days": trading_days,
            "stock_identifier": resolved_symbol
        }
    except Exception as e:
        return _fail(f"错误: 获取最近 {n} 个交易日数据时发生异常: {e}")
