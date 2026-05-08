import akshare as ak

from datetime import datetime, timedelta

from ..utils import _log_debug, _sge_report_cache


def get_sge_daily_data(
product_name: str, query_date: str, column_label: str
) -> str:
    """
    查询上海黄金交易所指定商品在特定日期的指定数据。
    能够处理'latest'等关键词，并自动查找最近的有效交易日数据。

    :param product_name: 要查询的商品名称 (例如 'Au(T+D)', 'Ag(T+D)')。
    :param query_date: 查询日期，格式为 'YYYY-MM-DD' 或 'latest' 等关键词。
    :param column_label: 要查询的数据列名 (例如 '收盘价', '成交量')。
    :return: 包含查询结果和数据日期的字符串，或详细的错误信息。
    """
    global _sge_report_cache
    try:
        if _sge_report_cache is None:
            _log_debug("--- [缓存未命中] 首次调用，正在下载完整的上海黄金交易所报告数据... ---")
            _sge_report_cache = ak.macro_china_au_report()
            _sge_report_cache['日期'] = _sge_report_cache['日期'].astype(str)
            _log_debug("--- [缓存成功] 数据已加载到内存中。 ---")
    except Exception as e:
        return f"错误：下载上海黄金交易所报告数据失败: {e}"
    df = _sge_report_cache
    available_products = df['商品'].unique()
    if product_name not in available_products:
        return f"错误：商品名称 '{product_name}' 无效。可用商品例如: 'Au(T+D)', 'Ag(T+D)', 'Au99.99' 等。"
    available_columns = df.columns.tolist()
    if column_label not in available_columns:
        return f"错误：列名 '{column_label}' 无效。可用列包括: {available_columns}。"
    effective_query_date_str = query_date
    LATEST_KEYWORDS = ['最新', 'latest', 'newest', 'today', '今天', '当前']
    if query_date.lower() in LATEST_KEYWORDS:
        _log_debug(f"--- [关键词识别] 检测到查询日期为 '{query_date}'，将查找最新交易日数据。---")
        effective_query_date_str = datetime.now().strftime('%Y-%m-%d')
    for i in range(7):
        try:
            current_date = datetime.strptime(effective_query_date_str, '%Y-%m-%d') - timedelta(days=i)
            current_date_str = current_date.strftime('%Y-%m-%d')
        except ValueError:
            return f"错误: 日期参数 '{query_date}' 格式无效。请使用 'YYYY-MM-DD' 格式或 'latest' 等关键词。"
        result_row = df[(df['日期'] == current_date_str) & (df['商品'] == product_name)]
        if not result_row.empty:
            try:
                value = result_row.iloc[0][column_label]
                result_json = {
                    "source": "上海黄金交易所(SGE)报告",
                    "product_name": product_name,
                    "date": current_date_str,
                    "metric_name": column_label,
                    "value": value
                }
                return result_json
            except KeyError:
                return f"错误：列名 '{column_label}' 无效。"
        else:
            if i == 0 and query_date.lower() in LATEST_KEYWORDS:
                _log_debug(f"--- 日期 '{current_date_str}' (今天) 无数据或非交易日，开始向前查找... ---")
            else:
                _log_debug(f"--- 日期 '{current_date_str}' 无数据，继续向前查找... ---")
    return f"错误: 在日期 '{effective_query_date_str}' 及其前7天内，均未找到商品 '{product_name}' 的有效交易数据。"
