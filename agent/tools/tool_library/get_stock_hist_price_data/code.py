import akshare as ak

from datetime import datetime
from typing import Optional, Any, Dict, Union

from ..get_code_from_name import get_code_from_name
from ..utils import _log_debug, _stock_zh_a_hist_cache


def get_stock_hist_price_data(
query_date: str,
    period: str,
    start_date: str,
    end_date: str,
    adjust: str,
    code: Optional[str] = None,
    name: Optional[str] = None
) -> Union[Dict[str, Any], str]:
    symbol = code if code else get_code_from_name(name)
    if not symbol:
        error_message = "错误: [get_stock_hist_price_data] 必须提供 'code' 或 'name'。"
        _log_debug(error_message)
        return error_message 
    
    # 检查 query_date 是否为未来日期
    try:
        query_date_obj = None
        for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%Y%m%d']:
            try:
                query_date_obj = datetime.strptime(query_date, fmt).date()
                break
            except ValueError:
                continue
        
        if query_date_obj:
            current_date = datetime.now().date()
            if query_date_obj > current_date:
                error_message = f"错误: [get_stock_hist_price_data] 查询日期 '{query_date}' 是未来日期（当前日期: {current_date.strftime('%Y-%m-%d')}）。无法获取未来日期的股票行情数据。"
                _log_debug(error_message)
                return error_message
    except Exception:
        # 如果日期解析失败，继续执行，让后续逻辑处理
        pass
    
    cache_key = (symbol, period, start_date, end_date, adjust)
    if cache_key not in _stock_zh_a_hist_cache:
        try:
            _log_debug(f"新查询(东方财富)，正在下载股票 {symbol} 的行情数据...")
            df = ak.stock_zh_a_hist(
                symbol=symbol, period=period, start_date=start_date,
                end_date=end_date, adjust=adjust
            )
            if df is not None and not df.empty:
                df.set_index('日期', inplace=True)
                _stock_zh_a_hist_cache[cache_key] = df
            else:
                _stock_zh_a_hist_cache[cache_key] = None
        except Exception as e:
            error_message = f"错误: [get_stock_hist_price_data] 从东方财富下载 {symbol} 行情数据时出错: {e}"
            _log_debug(error_message)
            _stock_zh_a_hist_cache[cache_key] = None
            return error_message 
    df = _stock_zh_a_hist_cache[cache_key]
    if df is None or df.empty:
        error_message = f"错误: [get_stock_hist_price_data] 未能获取到 {symbol} 的数据（API返回为空或缓存失败）。"
        _log_debug(error_message)
        return error_message 
    try:
        data_series = df.loc[query_date]
        daily_data_dict = data_series.to_dict()
        result_json = {
            "stock_identifier": name or symbol,
            "query_date": query_date,
            "adjust_type": adjust if adjust else "non-adjusted",
            "period": period,
            "daily_quote": daily_data_dict 
        }
        return result_json
    except KeyError:
        error_message = f"错误: [get_stock_hist_price_data] 无法在 {symbol} 的数据中找到日期 '{query_date}'。请确认该日期是交易日且格式为 'YYYY-MM-DD'。"
        _log_debug(error_message)
        return error_message 
    except Exception as e:
        error_message = f"错误: [get_stock_hist_price_data] 处理 {symbol} 的行情数据时发生未知错误: {e}"
        _log_debug(error_message)
        return error_message
