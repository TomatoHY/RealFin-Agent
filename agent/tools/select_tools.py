from typing import Callable, Dict
from .tool_selectors import NecessaryToolSelector


tool_selection_funcs: Dict[str, Callable] = {
    "necessary": NecessaryToolSelector(),
}
