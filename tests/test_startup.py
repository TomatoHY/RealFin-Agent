"""Offline regression checks for CLI setup and result serialization.

Provider and graph adapters are stubbed at import boundaries; no API requests
or optional runtime dependencies are needed to run these checks.
"""

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import random
import sys
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[1]


def module(name, **attributes):
    result = ModuleType(name)
    result.__dict__.update(attributes)
    return result


def load_source(relative_path, name, dependencies):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    result = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, dependencies):
        spec.loader.exec_module(result)
    return result


def load_runner():
    factory = load_source(
        "agent/models/model_factory.py", "agent.models.model_factory", {
            "langchain_anthropic": module("langchain_anthropic", ChatAnthropic=Mock()),
            "langchain_core.language_models.chat_models": module(
                "langchain_core.language_models.chat_models", BaseChatModel=object),
            "langchain_community.chat_models.tongyi": module(
                "langchain_community.chat_models.tongyi", ChatTongyi=Mock()),
            "langchain_openai": module("langchain_openai", AzureChatOpenAI=Mock(), ChatOpenAI=Mock()),
            "agent.utils": module("agent.utils", get_api_settings=Mock()),
        })
    selectors = module(
        "agent.tools.tool_selectors", AllToolSelector=Mock(), BM25ToolSelector=Mock(),
        OracleToolSelector=Mock(), OracKToolSelector=Mock())
    selection = load_source(
        "agent/tools/select_tools.py", "agent.tools.select_tools",
        {"agent.tools.tool_selectors": selectors})
    return load_source("run_agent.py", "realfin_test_runner", {
        "agent": module("agent", AgentConfig=Mock(), RealFinAgent=Mock()),
        "agent.models.model_factory": factory,
        "agent.tools.select_tools": selection,
        "agent.tools.tool_selectors": selectors,
    })


class StartupTests(unittest.TestCase):
    def test_cli_defaults_are_registered_and_limit_is_explicit(self):
        runner = load_runner()
        with patch.object(sys, "argv", ["run_agent.py"]):
            args = runner.parse_args()
        self.assertEqual(args.model, "gpt-5.1")
        self.assertIn(args.model, runner.MODEL_REGISTRY)
        self.assertEqual(args.tool_filter_strategy, "full")
        self.assertIn(args.tool_filter_strategy, runner.tool_selection_funcs)
        self.assertEqual(args.limit, 1)
        with patch.object(sys, "argv", ["run_agent.py", "--limit", "0"]):
            self.assertEqual(runner.parse_args().limit, 0)

    def test_cli_rejects_unknown_model_or_strategy(self):
        runner = load_runner()
        for flag in ("--model", "--tool_filter_strategy"):
            with self.subTest(flag=flag), patch.object(sys, "argv", ["run_agent.py", flag, "unknown"]):
                with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                    runner.parse_args()
                self.assertEqual(error.exception.code, 2)

    def test_graph_forwards_the_selected_provider_location(self):
        chat = Mock()
        graph = load_source("agent/realfin_agent.py", "agent.realfin_agent", {
            "langchain.messages": module(
                "langchain.messages", AIMessage=object, HumanMessage=object, SystemMessage=object),
            "langgraph.graph": module("langgraph.graph", StateGraph=Mock(), START="start", END="end"),
            "agent.nodes": module("agent.nodes", ChatNode=chat, ToolSelectorNode=Mock(), ToolRunnerNode=Mock()),
            "agent.prompts": module("agent.prompts", SYSTEM_PROMPT=""),
            "agent.utils": module("agent.utils", AgentConfig=object, AgentState=dict, serialize_agent_state=Mock()),
        })
        config = SimpleNamespace(model="gpt-5.1", model_kwargs={}, tool_filter_strategy="full", location="openai")
        graph.build_graph(config)
        chat.assert_called_once_with(model=config.model, model_kwargs={}, location="openai")

    def test_distractors_are_sampled_from_an_ordered_population(self):
        selection = load_source("agent/tools/tool_selectors/utils.py", "realfin_test_selection", {
            "rank_bm25": module("rank_bm25", BM25Okapi=Mock()),
        })
        descriptors = {name: {} for name in ("d", "a", "c", "b")}
        previous_random_state = random.getstate()
        try:
            random.seed(42)
            first = selection._get_distractor_tools(descriptors, {"a"}, sample_count=2)
            random.seed(42)
            second = selection._get_distractor_tools(dict(reversed(list(descriptors.items()))), {"a"}, sample_count=2)
            self.assertEqual(list(first), list(second))
            self.assertEqual(len(first), 2)
            self.assertNotIn("a", first)
            self.assertEqual(set(selection._get_distractor_tools(descriptors, {"a"}, sample_count=10)), {"b", "c", "d"})
        finally:
            random.setstate(previous_random_state)

    def test_main_writes_one_valid_json_record_per_line(self):
        runner = load_runner()
        records = [{"model_answer": "测试", "output": {"messages": ["a\nb"]}}, {"eval_score": 1}]
        with tempfile.TemporaryDirectory() as directory:
            args = SimpleNamespace(output_path=directory, test_data_path="unused", limit=2)
            with patch.object(runner, "parse_args", return_value=args), \
                    patch.object(runner, "initialize"), \
                    patch.object(runner, "read_test_data", return_value=[]), \
                    patch.object(runner, "run_test", return_value=records):
                runner.main()
            lines = (Path(directory) / "test_results.jsonl").read_text().splitlines()
            self.assertEqual(len(lines), 2)
            self.assertEqual([json.loads(line) for line in lines], records)


if __name__ == "__main__":
    unittest.main()
