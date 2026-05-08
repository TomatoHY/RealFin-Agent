import argparse
import importlib
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent import AgentConfig, RealFinAgent
from agent.tools.select_tools import tool_selection_funcs
from agent.tools.tool_selectors import OracKToolSelector


def parse_args():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--model", type=str, default="gpt-5-chat")
    argparser.add_argument("--model_kwargs", type=str, default="{\"temperature\": 0.8, \"max_tokens\": 2048}")
    argparser.add_argument("--output_path", type=str, default="output")
    argparser.add_argument("--tool_filter_strategy", type=str, default="necessary")
    argparser.add_argument("--limit", type=int, default=1)
    argparser.add_argument("--test_data_path", type=str, default="data/realfin_data.jsonl")
    argparser.add_argument("--location", type=str, choices=["realfin", "openai"], default="realfin")

    argparser.add_argument("--k", type=int, default=5, help="Number of random distractor tools for orac_k strategy")
    argparser.add_argument("--log_level", type=str, choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], default="INFO")
    argparser.add_argument("--log_file", type=str, default="agent_log.log")

    args = argparser.parse_args()
    return args


def initialize(args):
    os.makedirs(args.output_path, exist_ok=True)

    log_level = getattr(logging, args.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(
                os.path.join(args.output_path, args.log_file),
                mode="w",
            ),
        ],
    )

    try:
        model_kwargs = json.loads(args.model_kwargs)
    except json.JSONDecodeError:
        logging.error("Invalid JSON format for model_kwargs.")
        exit(1)

    config = AgentConfig(
        model=args.model,
        model_kwargs=model_kwargs,
        tool_filter_strategy=args.tool_filter_strategy,
        location=args.location,
    )

    if args.tool_filter_strategy == "orac_k":
        tool_selection_funcs["orac_k"] = OracKToolSelector(k=args.k)

    config_file = os.path.join(args.output_path, "config.json")
    with open(config_file, "w") as f:
        json.dump({
            "args": {**vars(args)},
            "agent_config": config.model_dump(),
        }, f, indent=4)
    return config


_tool_funcs_cache: Optional[Dict[str, Any]] = None


def _load_all_tools() -> Dict[str, Any]:
    """加载所有工具函数（全量，工具已修复无ImportError）"""
    global _tool_funcs_cache
    if _tool_funcs_cache is not None:
        return _tool_funcs_cache
    tool_lib_dir = Path(__file__).parent / "agent" / "tools" / "tool_library"
    tool_funcs = {}
    for tool_dir in tool_lib_dir.iterdir():
        if not tool_dir.is_dir() or not (tool_dir / "code.py").exists():
            continue
        tool_name = tool_dir.name
        module = importlib.import_module(f"agent.tools.tool_library.{tool_name}.code")
        if hasattr(module, tool_name):
            tool_funcs[tool_name] = getattr(module, tool_name)
    _tool_funcs_cache = tool_funcs
    return tool_funcs


def _resolve_golden_result(code: str) -> Any:
    """执行code字段得出实时golden_result，失败时返回None"""
    try:
        exec_globals = {**_load_all_tools()}
        wrapped = "def _golden_fn():\n" + "\n".join(f"    {line}" for line in code.splitlines())
        exec(wrapped, exec_globals)
        return exec_globals["_golden_fn"]()
    except Exception as e:
        logging.warning(f"Failed to resolve golden_result: {e}")
        return None


def _extract_tool_calls_from_output(output: Any) -> List[Dict[str, Any]]:
    """从所有AI消息的<tool_use>标签里提取工具调用列表"""
    if not isinstance(output, dict):
        return []
    tool_calls = []
    pattern = re.compile(r"<tool_use>\s*(.*?)\s*</tool_use>", re.DOTALL)
    for msg in output.get("messages", []):
        role = msg.get("type") if isinstance(msg, dict) else getattr(msg, "type", None)
        if role != "ai":
            continue
        content = msg.get("data", {}).get("content") if isinstance(msg, dict) else getattr(msg, "content", None)
        if not content:
            continue
        match = pattern.search(content)
        if not match:
            continue
        try:
            parsed = json.loads(match.group(1).strip())
            calls = parsed if isinstance(parsed, list) else [parsed]
            for call in calls:
                tool_calls.append({
                    "name": call.get("function") or call.get("name"),
                    "arguments": call.get("arguments", {}),
                })
        except json.JSONDecodeError:
            pass
    return tool_calls


def _get_last_ai_content(output: Any) -> Optional[str]:
    """从agent返回的state dict中取最后一条AI消息的content"""
    if isinstance(output, str):
        return output
    if not isinstance(output, dict):
        return None
    messages = output.get("messages", [])
    for msg in reversed(messages):
        role = msg.get("type") if isinstance(msg, dict) else getattr(msg, "type", None)
        if role == "ai":
            content = msg.get("data", {}).get("content") if isinstance(msg, dict) else getattr(msg, "content", None)
            if content:
                return content
    return None


def _extract_model_answer(output: Any) -> Optional[str]:
    """从模型回答的\\boxed{}中提取答案"""
    content = _get_last_ai_content(output)
    if not content:
        return None
    matches = re.findall(r"\\boxed\{([^}]*)\}", content)
    return matches[-1].strip() if matches else None


def _compute_eval_score(model_answer: Optional[str], golden_result: Any) -> int:
    """model_answer与golden_result相等时返回1，否则返回0"""
    if model_answer is None or golden_result is None:
        return 0
    # 统一转字符串比较，兼容数值型golden_result
    def _normalize(v: Any) -> str:
        try:
            return str(float(v))
        except (TypeError, ValueError):
            return str(v).strip()
    return 1 if _normalize(model_answer) == _normalize(golden_result) else 0


def read_test_data(test_data_path: str = "data/realfin_data.jsonl", limit: int = None):
    with open(test_data_path, "r") as f:
        lines = f.readlines()
    test_data = [json.loads(line) for line in lines]
    if limit:
        test_data = test_data[:limit]
    for item in test_data:
        if item.get("golden_result") == "实时获取":
            item["golden_result"] = _resolve_golden_result(item.get("code", ""))
    return test_data


def run_test(agent: RealFinAgent, test_data: List[Dict[str, Any]]):
    results = []
    for test_case in test_data:
        user_input = test_case["question"]
        metadata = test_case
        metadata.pop("question")
        output = agent.run(user_input, metadata)
        model_answer = _extract_model_answer(output)
        eval_score = _compute_eval_score(model_answer, metadata.get("golden_result"))
        tool_calls = _extract_tool_calls_from_output(output)
        results.append({
            "metadata": metadata,
            "output": output,
            "tool_calls": tool_calls,
            "model_answer": model_answer,
            "eval_score": eval_score,
        })
    return results


def main():
    args = parse_args()
    config = initialize(args)
    test_data = read_test_data(test_data_path=args.test_data_path, limit=args.limit)
    agent = RealFinAgent(config)
    results = run_test(agent, test_data)
    with open(os.path.join(args.output_path, "test_results.jsonl"), "w") as f:
        for result in results:
            f.write(json.dumps(result, ensure_ascii=False, indent=4) + "\n")


if __name__ == "__main__":
    main()