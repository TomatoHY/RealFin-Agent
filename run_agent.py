import argparse
import json
import logging
import os
from typing import Dict, List

from agent import AgentConfig, RealFinAgent


def parse_args():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--model", type=str, default="gpt-3.5-turbo")
    argparser.add_argument("--model_kwargs", type=str, default="{\"temperature\": 0.8, \"top_p\": 0.7, \"top_k\": 50}")
    argparser.add_argument("--output_path", type=str, default="output")
    argparser.add_argument("--max_tool_call", type=int, default=5)
    argparser.add_argument("--tool_filter_strategy", type=str, default="necessary")
    argparser.add_argument("--limit", type=int, default=None)

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
            logging.FileHandler(os.path.join(args.output_path, args.log_file)),
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
        max_tool_call=args.max_tool_call,
        tool_filter_strategy=args.tool_filter_strategy,
    )

    config_file = os.path.join(args.output_path, "config.json")
    with open(config_file, "w") as f:
        json.dump({
            "args": {**vars(args)},
            "agent_config": config,
        }, f, indent=4)
    return config


def read_test_data(test_data_path: str = "data/realfin_data.jsonl", limit=None):
    with open(test_data_path, "r") as f:
        lines = f.readlines()
    test_data = [json.loads(line) for line in lines]
    if limit:
        test_data = test_data[:limit]
    return test_data


def run_test(agent: RealFinAgent, test_data: List[dict]):
    results = []
    for test_case in test_data:
        user_input = test_case["question"]
        output = run_agent(agent, user_input)
        results.append({
            "output": output,
        })
    return results


def main():
    args = parse_args()
    config = initialize(args)
    test_data = read_test_data(limit=args.limit)
    agent = RealFinAgent(config)
    results = run_test(agent, test_data)
    with open(os.path.join(args.output_path, "test_results.jsonl"), "w") as f:
        for result in results:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()