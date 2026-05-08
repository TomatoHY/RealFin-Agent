# RealFin-Agent

# full（全量85个工具）
python run_agent.py \
  --tool_filter_strategy full \
  --output_path output/eval_full \
  --test_data_path data/realfin_data.jsonl \
  --location realfin \
  --model kimi-k2

# bm25（top-20筛选）
python run_agent.py \
  --tool_filter_strategy bm25 \
  --output_path output/eval_bm25 \
  --test_data_path data/realfin_data.jsonl \
  --location realfin \
  --model kimi-k2

# orac-k
python run_agent.py \
  --tool_filter_strategy orac_k \
  --k 3 \
  --output_path output/eval_orac_k \
  --test_data_path data/realfin_data.jsonl \
  --location realfin \
  --model kimi-k2