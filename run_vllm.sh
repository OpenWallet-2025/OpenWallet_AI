#!/usr/bin/env bash
set -euo pipefail

# Qwen2.5-7B-Instruct를 OpenAI 호환 엔드포인트로 서빙
# --dtype, --max-model-len 등은 환경에 맞춰 조정


MODEL="Qwen/Qwen2.5-7B-Instruct"
PORT=8000


echo "Starting vLLM with $MODEL on :$PORT"
python -m vllm.entrypoints.openai.api_server \
    --model "$MODEL" \
    --port $PORT \
    --dtype bfloat16 \
    --max-model-len 8192 \
    --trust-remote-code