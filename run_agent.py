import argparse
import os

import numpy as np

from agent import RealFinAgent


def parse_args():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--model", type=str, required=True)
    argparser.add_argument("--model_kwargs", type=str, required=True)
    argparser.add_argument("--output_path", type=str, required=True)
    args = argparser.parse_args()
    return args


def read_test_data():
    pass


def run_agent(agent: RealFinAgent, user_input: str):
    return agent.run(user_input)


def main():
    args = parse_args()
    agent = RealFinAgent(args)
    test_data = read_test_data()
    for user_input in test_data:
        output = run_agent(agent, user_input)
        # 匹配答案，记录
    # 输出


if __name__ == "__main__":
    main()