#!/bin/bash
# vLLM Local LLM Server for Scripture RAG Evaluation
#
# Starts vLLM with OpenAI-compatible API on port 8004
# Uses Qwen2.5-7B-Instruct as LLM-as-judge
#
# Requirements:
# - CUDA 12.8+
# - RTX 5090 (32GB VRAM) or similar
# - vLLM installed in virtualenv
#
# Usage:
#   ./start.sh              # Start with default settings
#   ./start.sh --quantized  # Use AWQ quantized model (faster, less VRAM)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[vLLM]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[vLLM]${NC} $1"; }

# Default settings
# Use local model path if available, otherwise download from HuggingFace
LOCAL_MODEL_PATH_7B="$SCRIPT_DIR/models/Qwen2.5-7B-Instruct"
LOCAL_MODEL_PATH_14B="$SCRIPT_DIR/models/Qwen2.5-14B-Instruct"
if [ -d "$LOCAL_MODEL_PATH_7B" ]; then
    MODEL="${JUDGE_LLM_MODEL:-$LOCAL_MODEL_PATH_7B}"
elif [ -d "$LOCAL_MODEL_PATH_14B" ]; then
    MODEL="${JUDGE_LLM_MODEL:-$LOCAL_MODEL_PATH_14B}"
else
    MODEL="${JUDGE_LLM_MODEL:-Qwen/Qwen2.5-7B-Instruct}"
fi
PORT="${JUDGE_LLM_PORT:-8004}"
MAX_MODEL_LEN="${JUDGE_LLM_MAX_LEN:-32768}"
GPU_MEMORY_UTILIZATION="${JUDGE_LLM_GPU_MEM:-0.9}"

# Check for quantized flag
if [[ "$1" == "--quantized" ]]; then
    MODEL="Qwen/Qwen2.5-14B-Instruct-AWQ"
    log_info "Using quantized model: $MODEL"
fi

# Set CUDA 12.8 paths
export PATH=/usr/local/cuda-12.8/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda-12.8/lib64:$LD_LIBRARY_PATH

# Find vLLM - check common locations
VLLM_PYTHON=""

# 1. Check for local .venv in llm_local directory (preferred)
if [ -d "$SCRIPT_DIR/.venv" ]; then
    source "$SCRIPT_DIR/.venv/bin/activate"
    VLLM_PYTHON="python"
    log_info "Using local .venv: $SCRIPT_DIR/.venv"
# 2. Check for dedicated vLLM venv in home
elif [ -d "$HOME/.venvs/vllm" ]; then
    source "$HOME/.venvs/vllm/bin/activate"
    VLLM_PYTHON="python"
    log_info "Using vLLM venv: $HOME/.venvs/vllm"
# 3. Check if vllm is in system path
elif command -v vllm &> /dev/null; then
    VLLM_PYTHON="python3"
    log_info "Using system vLLM"
fi

if [ -z "$VLLM_PYTHON" ]; then
    log_warn "vLLM not found! Install it with:"
    log_warn "  cd $SCRIPT_DIR"
    log_warn "  python3 -m venv .venv"
    log_warn "  source .venv/bin/activate"
    log_warn "  pip install -r requirements.txt"
    exit 1
fi

log_info "Starting vLLM server for Scripture RAG evaluation..."
log_info "  Model: $MODEL"
log_info "  Port: $PORT"
log_info "  Max context: $MAX_MODEL_LEN tokens"
log_info "  GPU memory utilization: $GPU_MEMORY_UTILIZATION"

# For Blackwell (SM120), may need FA2 fallback
# Uncomment if you see Flash Attention errors:
# export VLLM_FLASH_ATTN_VERSION=2

exec $VLLM_PYTHON -m vllm.entrypoints.openai.api_server \
    --model "$MODEL" \
    --host 0.0.0.0 \
    --port "$PORT" \
    --max-model-len "$MAX_MODEL_LEN" \
    --gpu-memory-utilization "$GPU_MEMORY_UTILIZATION" \
    --trust-remote-code
