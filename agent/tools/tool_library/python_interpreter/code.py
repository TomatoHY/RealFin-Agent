import pandas as pd

from typing import Any

from ..utils import _log_debug


def python_interpreter(
code: str
) -> Any:
    """
    执行一段 Python 代码字符串并返回其最终表达式的结果。
    代码可以访问 pandas 库 (别名为 pd) 以及已在此环境中定义的其他变量。
    
    Args:
        code (str): 一段有效的 Python 代码字符串。为了返回值，代码的最后一行
                    必须是一个可以被 'eval()' 求值的表达式。

    Returns:
        Any: 代码最后一行表达式的执行结果。
    """
    _log_debug(f"--- [Python Interpreter] 正在执行以下代码 ---\n{code}\n---------------------------------------------")
    local_scope = {
        'pd': pd
    }
    try:
        lines = code.strip().split('\n')
        if len(lines) > 1:
            exec('\n'.join(lines[:-1]), globals(), local_scope)
        result = eval(lines[-1], globals(), local_scope)
        _log_debug(f"--- [Python Interpreter] 执行成功，返回类型: {type(result)} ---")
        return result
    except Exception as e:
        import traceback
        error_message = f"Python代码执行失败: {e}\n{traceback.format_exc()}"
        _log_debug(f"--- [Python Interpreter] {error_message} ---")
        return {"error": error_message}
