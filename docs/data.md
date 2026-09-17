# Dataset card

[← Back to the project](../README.md)

RealFin pairs Chinese financial-analysis questions with reference program bodies and workflow metadata. Each reference describes **one valid solution path**; other workflows can be valid when they satisfy the same task constraints. The two JSONL files can be inspected without installing the agent or calling any APIs.

## Files and scope

| File | Records | Templates | Use |
|---|---:|---:|---|
| [`realfin_data.jsonl`](../data/realfin_data.jsonl) | 1,524 | 108 | Full benchmark for dataset analysis and evaluation |
| [`subset_128.jsonl`](../data/subset_128.jsonl) | 128 | 44 | Diagnostic core used for the paper's main model comparison |

The 128-task core intentionally oversamples Compare and Realtime tasks to probe tool ambiguity and temporal grounding. It is not a random, distribution-matched sample of the full benchmark, and results on it should be identified as diagnostic-core results. Use the records in the selected file as the evaluation inputs; some reference values and annotations differ between the two files.

## Composition

Counts below are computed directly from the checked-in files.

| Task type | Full benchmark | Diagnostic core |
|---|---:|---:|
| `T1_Snapshot` | 412 | 45 |
| `T2_Compare` | 107 | 24 |
| `T3_Aggregate` | 677 | 49 |
| `T4_Fundamentals` | 328 | 10 |

| Temporal regime | Meaning | Full benchmark | Diagnostic core |
|---|---|---:|---:|
| `Fixed` | Explicit historical dates or periods | 794 | 51 |
| `Relative` | Relative dates, windows, or trading-calendar references | 629 | 41 |
| `Realtime` | Current or near-current values | 101 | 36 |

| Reference-workflow statistic | Full benchmark | Diagnostic core |
|---|---:|---:|
| Mean `ref_tool_count` | 3.78 | 4.00 |
| Mean `ref_execution_depth` | 2.12 | 1.93 |

## Record schema

Each non-empty line is a JSON object with these fields:

| Field | JSON type | Description |
|---|---|---|
| `question` | string | Financial-analysis question, in Chinese |
| `code` | string | Reference Python function body, using the benchmark's tool functions |
| `golden_result` | string, number, or array | Stored reference answer, or the live-resolution marker described below |
| `type` | string | One of the four task types above |
| `time_sensitivity` | string | `Fixed`, `Relative`, or `Realtime` |
| `ref_tool_count` | integer | Annotated reference-workflow tool count |
| `ref_execution_depth` | integer | Annotated reference-workflow execution depth |
| `ref_tool_coverage` | integer | Annotated reference-workflow tool coverage count |
| `template` | string | Workflow-template identifier |

The reference counts describe the annotated workflow and should not be inferred by counting function names in the compact `code` string.

### Live reference answers

`golden_result: "实时获取"` means **resolve the reference answer at execution time**. It is a marker, not a reference answer to compare literally against model output. The current runner executes the record's reference code to resolve it; this requires working tool dependencies and access to the underlying APIs.

The marker appears in 733 full-benchmark records and 81 diagnostic-core records. It also occurs in a few `Fixed` records, so a `Fixed` label alone does not guarantee that a stored answer is available. Live values and API availability may change between runs; preserve the resolved references with results when making comparisons.

## Example record

The first record in both files asks:

> 光正眼科7个交易日之前的最高价是多少？

Its metadata is:

```json
{
  "golden_result": "实时获取",
  "type": "T3_Aggregate",
  "time_sensitivity": "Relative",
  "ref_tool_count": 2,
  "ref_execution_depth": 2,
  "ref_tool_coverage": 1,
  "template": "lookup_nth_previous_trading_day_price"
}
```

The stored reference body, expanded into a function for readability, is:

```python
def reference_workflow():
    result = get_last_n_trading_days(
        name="光正眼科", n=7, column_label="high", adjust=""
    )
    return (
        result.get("trading_days", [])[-1].get("value")
        if isinstance(result, dict)
        and "trading_days" in result
        and len(result.get("trading_days", [])) >= 7
        else None
    )
```

Executing this body requires the benchmark's `get_last_n_trading_days` tool. Reading the JSONL itself does not execute it.

## Inspect offline

Run from the repository root with Python 3. This uses only the standard library, prints the dataset counts and first record, and makes no model or financial-data requests.

```bash
python - <<'PY'
import json
from collections import Counter
from pathlib import Path

for name in ("realfin_data.jsonl", "subset_128.jsonl"):
    path = Path("data") / name
    with path.open(encoding="utf-8") as source:
        records = [json.loads(line) for line in source if line.strip()]
    print(f"\n{name}: {len(records):,} records")
    print("Templates:", len({row["template"] for row in records}))
    print("Task types:", dict(Counter(row["type"] for row in records)))
    print("Temporal regimes:", dict(Counter(
        row["time_sensitivity"] for row in records
    )))
    print(json.dumps(records[0], ensure_ascii=False, indent=2))
PY
```
