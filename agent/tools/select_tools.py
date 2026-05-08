from typing import Callable, Dict
from .tool_selectors import (
    AllToolSelector,
    BM25ToolSelector,
    OracleToolSelector,
    OracKToolSelector,
)


tool_selection_funcs: Dict[str, Callable] = {
    "full": AllToolSelector(),
    "bm25": BM25ToolSelector(),
    "oracle": OracleToolSelector(),
    "orac_k": OracKToolSelector()
}
