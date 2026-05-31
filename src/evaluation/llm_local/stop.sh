#!/bin/bash
# Stop vLLM Local LLM Server
#
# Stops the vLLM server running on port 8004 (or JUDGE_LLM_PORT)
#
# Usage:
#   ./stop.sh         # Graceful stop (SIGTERM)
#   ./stop.sh -f      # Force stop (SIGKILL)

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[vLLM]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[vLLM]${NC} $1"; }
log_error() { echo -e "${RED}[vLLM]${NC} $1"; }

PORT="${JUDGE_LLM_PORT:-8004}"
FORCE=false

if [[ "$1" == "-f" || "$1" == "--force" ]]; then
    FORCE=true
fi

# Find process listening on the port
PID=$(lsof -ti :$PORT 2>/dev/null || true)

if [ -z "$PID" ]; then
    log_info "No vLLM server running on port $PORT"
    exit 0
fi

log_info "Found vLLM server (PID: $PID) on port $PORT"

if [ "$FORCE" = true ]; then
    log_warn "Force stopping vLLM server..."
    kill -9 $PID 2>/dev/null || true
else
    log_info "Stopping vLLM server gracefully..."
    kill $PID 2>/dev/null || true

    # Wait up to 10 seconds for graceful shutdown
    for i in {1..10}; do
        if ! kill -0 $PID 2>/dev/null; then
            break
        fi
        sleep 1
    done

    # Force kill if still running
    if kill -0 $PID 2>/dev/null; then
        log_warn "Server still running, force stopping..."
        kill -9 $PID 2>/dev/null || true
    fi
fi

# Verify stopped
sleep 1
if lsof -ti :$PORT >/dev/null 2>&1; then
    log_error "Failed to stop vLLM server"
    exit 1
else
    log_info "vLLM server stopped successfully"
fi
