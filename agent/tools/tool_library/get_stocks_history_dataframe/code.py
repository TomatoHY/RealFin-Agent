import pandas as pd

from typing import Union, List

from ..utils import _log_debug


def get_stocks_history_dataframe(
codes: List[str], 
    start_date: str, 
    end_date: str, 
    adjust: str = ""
) -> Union[pd.DataFrame, str]:
    """
    一次性获取【多只股票】在一段时间内的历史行情数据。
    该函数通过在日期范围内循环调用单点查询工具 (如 get_a_stock_daily_price) 来构建 DataFrame。

    Args:
        codes (List[str]): 股票代码的列表 (例如: ["sh600519", "sz300750"]).
        start_date (str): 开始日期, 格式 'YYYY-MM-DD'.
        end_date (str): 结束日期, 格式 'YYYY-MM-DD'.
        adjust (str, optional): 复权类型. "", "qfq", "hfq". 默认为 "".

    Returns:
        Union[pd.DataFrame, str]: 
            - 成功: 一个包含所有股票历史数据的、合并好的 DataFrame。
            - 失败: 一个包含错误信息的字符串。
    """
    if not isinstance(codes, list) or not codes:
        error_message = "错误：'codes' 参数必须是一个非空的列表，例如 ['sh600519']。"
        _log_debug(f"--- [批量获取DataFrame v2] {error_message} ---")
        return error_message
    VALID_ADJUSTS = ["", "qfq", "hfq"]
    if adjust not in VALID_ADJUSTS:
        error_message = f"错误：无效的 'adjust' 参数 '{adjust}'。有效选项: {VALID_ADJUSTS}"
        _log_debug(f"--- [批量获取DataFrame v2] {error_message} ---")
        return error_message
    try:
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    except ValueError as e:
        error_message = f"错误：日期格式不正确或范围无效 (start: '{start_date}', end: '{end_date}')。请使用 'YYYY-MM-DD' 格式。错误: {e}"
        _log_debug(f"--- [批量获取DataFrame v2] {error_message} ---")
        return error_message
    all_daily_records = []
    market_dispatch = {}
    
    # --- 修改开始 ---
    # 优先规范化股票代码，确保A股代码有前缀
    processed_codes = []
    for code in codes:
        if code.isdigit() and len(code) == 6: # 假设6位数字是中国A股
            if code.startswith(('60', '00', '30', '68')): # 根据A股代码常见开头判断
                # 尝试自动添加前缀
                if code.startswith('6'): # 沪市A股
                    processed_codes.append(f"sh{code}")
                elif code.startswith(('00', '30', '68')): # 深市A股 (00, 30, 68)
                    processed_codes.append(f"sz{code}")
                else: # 无法确定市场，保留原始，让下面的dispatch处理
                    processed_codes.append(code)
            else: # 纯数字但不是A股的常见开头，保留原始
                processed_codes.append(code)
        else: # 非6位数字的纯数字或已带前缀的，保留原始
            processed_codes.append(code)

    # 重新构建 market_dispatch
    for code in processed_codes: # 使用处理后的代码列表
        if code.startswith('sh') or code.startswith('sz') or code.startswith('bj'):
            market_dispatch[code] = get_a_stock_daily_price
        # 注意：此处要确保纯数字的A股代码已经被上面的逻辑处理成带前缀的了
        # 否则，如果'300750'进来，它会走到get_hk_stock_daily_price (如果 len <= 5 是错的)
        # 或者 get_us_stock_daily_price (如果上面A股识别不够全面)
        elif code.isdigit() and (len(code) == 4 or len(code) == 5): # 港股通常4-5位数字
            market_dispatch[code] = get_hk_stock_daily_price
        else: # 假设其他都是美股或未能识别
            market_dispatch[code] = get_us_stock_daily_price
            
    _log_debug(f"--- [批量获取DataFrame v2] 将为 {len(processed_codes)} 只股票查询 {len(date_range)} 天的数据... ---")
    
    # 修改循环，使用 processed_codes
    for code in processed_codes:
    # --- 修改结束 ---
        price_fetcher = market_dispatch.get(code)
        if not price_fetcher:
            _log_debug(f"    [警告] 无法为代码 '{code}' 确定市场类型，已跳过。")
            continue
        # ... (其余代码不变) ...
        columns_to_fetch = ['open', 'high', 'low', 'close', 'amount'] 
        for current_date in date_range:
            date_str = current_date.strftime('%Y-%m-%d')
            daily_data = {'code': code, 'date': date_str}
            is_successful_day = True
            for col in columns_to_fetch:
                try:
                    result_dict = price_fetcher(
                        code=code, 
                        query_date=date_str, 
                        column_label=col, 
                        adjust=adjust
                    )
                    if isinstance(result_dict, dict) and 'requested_item' in result_dict:
                        if result_dict.get('date') == date_str:
                            daily_data[col] = result_dict['requested_item']['value']
                        else:
                            is_successful_day = False
                            break 
                    else:
                        is_successful_day = False
                        break
                except Exception as e:
                    _log_debug(f"    [警告] 在为 {code} 获取 {date_str} 的 '{col}' 数据时发生内部错误: {e}")
                    is_successful_day = False
                    break
            if is_successful_day:
                all_daily_records.append(daily_data)
    if not all_daily_records:
        error_message = f"错误：在为股票 {codes} 查询 {start_date} 到 {end_date} 期间的数据时，未能收集到任何有效的交易日记录。"
        _log_debug(f"--- [批量获取DataFrame v2] {error_message} ---")
        return error_message 
    final_df = pd.DataFrame(all_daily_records)
    final_df['date'] = pd.to_datetime(final_df['date'])
    if 'amount' in final_df.columns:
        final_df.rename(columns={'amount': 'volume'}, inplace=True)
    _log_debug(f"--- [批量获取DataFrame v2] 完成！成功构建了包含 {len(final_df)} 条记录的 DataFrame。 ---")
    return final_df
