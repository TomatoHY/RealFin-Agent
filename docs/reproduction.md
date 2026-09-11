# Running RealFin

[Back to the project](../README.md)

This guide describes the runner included in this repository and distinguishes its outputs from the full evaluation reported in the [paper](paper/realfin.pdf).

## Environment

From the repository root, create a Python 3.11+ virtual environment and install the runtime dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

`requirements.txt` is derived from the source imports. A locked environment from the paper's experiments is not included. Record your installed versions alongside any results:

```bash
python -m pip freeze > output-environment.txt
```

## Model and API configuration

The model client uses the aliases in [`MODEL_REGISTRY`](../agent/models/model_factory.py). The selected endpoint must support the corresponding request name. This registry describes the harness configuration, not current model availability at any provider.

| `--location` | API key | Base URL |
| :--- | :--- | :--- |
| `openai` | `OPENAI_API_KEY` | `OPENAI_API_BASE` |
| `realfin` | `REALFIN_API_KEY` | `REALFIN_API_BASE` |

These settings are loaded from `.env` or the shell environment. Set the base URL explicitly to an endpoint you have access to. The name `openai` selects an OpenAI-compatible client configuration; the `realfin` option selects a separate gateway configuration.

For example, edit `.env`:

```dotenv
OPENAI_API_KEY=your-api-key
OPENAI_API_BASE=https://your-model-endpoint.example/v1
```

Currency conversion tools additionally read `CURRENCY_API_KEY` directly from the process environment. If you use those tools, export the key in your shell; setting it only in `.env` does not populate `os.environ` for those tools.

```bash
export CURRENCY_API_KEY='your-currency-api-key'
```

Live runs invoke model and financial-data services. Reference programs are also executed for records whose `golden_result` is `"实时获取"`, before the agent starts. Some data requests retry with long delays. For an offline look at the benchmark, use the inspection example in the [data card](data.md#inspect-offline).

## Run the diagnostic core

The following commands use the same 128-task file and explicit model configuration. Run them from the repository root after configuring your endpoint. Start with `--limit 1` to check the setup; `--limit 0` processes all records in the selected file.

```bash
# Full: all 85 tool definitions
python run_agent.py \
  --model gpt-5.1 --location openai \
  --tool_filter_strategy full \
  --test_data_path data/subset_128.jsonl --limit 0 \
  --output_path output/core_full

# BM25: the top 20 retrieved tools
python run_agent.py \
  --model gpt-5.1 --location openai \
  --tool_filter_strategy bm25 \
  --test_data_path data/subset_128.jsonl --limit 0 \
  --output_path output/core_bm25

# Oracle: tools referenced in the reference program
python run_agent.py \
  --model gpt-5.1 --location openai \
  --tool_filter_strategy oracle \
  --test_data_path data/subset_128.jsonl --limit 0 \
  --output_path output/core_oracle

# OraA-3: Oracle + alternatives + three random distractors
python run_agent.py \
  --model gpt-5.1 --location openai \
  --tool_filter_strategy orac_k --k 3 \
  --test_data_path data/subset_128.jsonl --limit 0 \
  --output_path output/core_oraa3

# OraA-10: Oracle + alternatives + ten random distractors
python run_agent.py \
  --model gpt-5.1 --location openai \
  --tool_filter_strategy orac_k --k 10 \
  --test_data_path data/subset_128.jsonl --limit 0 \
  --output_path output/core_oraa10
```

For the full benchmark, use `--test_data_path data/realfin_data.jsonl --limit 0` and a separate output directory. Rerunning with an existing output path overwrites that run's files.

### Implementation details that affect comparisons

- **Model parameters.** The CLI defaults to `{"temperature": 0.8, "max_tokens": 2048}`. Override these with `--model_kwargs '{"temperature": 0.0, "max_tokens": 2048}'` if supported by your endpoint. Changing sampling settings changes the experimental configuration.
- **BM25.** The current implementation tokenizes tool names, descriptions, and queries using whitespace splitting. It has no dedicated Chinese tokenizer.
- **Oracle.** Selection matches callable tool names in the reference `code`; it does not recursively expand internal helper calls.
- **OraA-k.** Alternatives are added from `tool_alternative`. Distractors are sampled from the remaining definitions, up to the requested `k`; the CLI does not expose a random-seed option.
- **Temporal references.** Relative and Realtime tasks can change across run dates. A `Fixed` label alone does not guarantee a frozen reference value; inspect `golden_result` as well.

## Read the outputs

Each run writes:

| File | Contents |
| :--- | :--- |
| `config.json` | CLI arguments and agent configuration |
| `agent_log.log` | Runtime log; use `--log_level DEBUG` for more detail |
| `test_results.jsonl` | One JSON object per task, one object per line |

Each result includes `metadata`, `output`, `tool_calls`, `model_answer`, and `eval_score`. The trajectory is stored in `output`; the input question remains in its messages.

`model_answer` is extracted from the final `\boxed{...}` answer. The current `eval_score` is binary: values are converted to float strings when possible, otherwise stripped strings, and then compared for equality. Missing answers or missing reference values receive 0. There is no numerical-tolerance or process-metric calculation in this scorer.

Summarize the runner's answer score using only the Python standard library:

```bash
python - <<'PY'
import json
from pathlib import Path

path = Path("output/core_full/test_results.jsonl")
rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
if not rows:
    raise SystemExit("No results found")
correct = sum(row["eval_score"] for row in rows)
missing = sum(row["metadata"].get("golden_result") is None for row in rows)
print(f"Tasks: {len(rows)}")
print(f"Runner answer score: {correct / len(rows):.2%}")
print(f"Missing reference values: {missing}")
PY
```

## Reproduction scope

| Component | Included in this checkout |
| :--- | :--- |
| Full dataset and 128-task diagnostic core | Yes |
| Reference programs and tool descriptions | Yes, stored with the records and tool definitions |
| ReAct-style harness, Full / BM25 / Oracle / OraA-k selectors | Yes |
| Prompts, traces, extracted tool calls, basic answer scorer | Yes |
| Paper process metrics: ESR, TSR, OA, EGA, TGA, PPS, OSR, RSS | No standalone evaluator included |
| Progressive package-routing and unfair oracle-guided experiments | No experiment entry point included |
| Frozen API snapshots and paper environment lockfile | No complete replay bundle included |

The tool library contains a local data archive, but that is not a complete snapshot/replay system for all financial APIs. The helper tools `read_tool_description` and `read_package_description` also reference `realfin_toolkit.json` and `tool_package.json`, respectively; these files are absent from their expected directories in this checkout, so those helpers return a file-not-found error.

The README's result table is transcribed from the manuscript. Running the commands above produces new trajectories and runner answer scores; reproducing all paper metrics also requires the missing evaluation components, matching model configurations, and controlled data access.

## Offline regression checks

The startup and output-format regression checks run without model credentials, third-party runtime dependencies, or financial API requests:

```bash
python -m unittest discover -s tests -v
```

These checks validate the patched runner behavior. They do not validate live endpoint availability or reproduce the paper's experimental results.
