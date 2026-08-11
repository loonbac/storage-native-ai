#!/bin/bash
# E002d — captura de traces de routing (script reproducible)
# Uso: ./capture_traces.sh <modelo> <prompt-id> <prompt> <n-tokens>
# Ejemplos:
#   ./capture_traces.sh 30b p1 "Prove that sqrt(2) is irrational." 300
#   ./capture_traces.sh 235b p1 "..." 700
set -euo pipefail

BIN=/home/loonbac/Projects/tools/llama.cpp-b10333-fork/build/bin/llama-cli
TRACES=/home/loonbac/Projects/research/experiments/E006/traces
M30=/home/loonbac/Projects/models/Qwen3-30B-A3B-Q4_K_M.gguf
M235=/home/loonbac/Projects/models/Q4_K_M/Qwen3-235B-A22B-Q4_K_M-00001-of-00005.gguf

MODEL_KIND="${1:?modelo: 30b|235b}"
PID="${2:?prompt-id}"
PROMPT="${3:?prompt}"
N="${4:?n-tokens}"

case "$MODEL_KIND" in
  30b)  MODEL="$M30" ;;
  235b) MODEL="$M235" ;;
  *) echo "modelo inválido"; exit 1 ;;
esac

TS=$(date +%Y%m%d-%H%M%S)
NAME="${MODEL_KIND}-${PID}-${TS}"
mkdir -p "$TRACES"

echo "=== E002d capture: $NAME ==="
echo "modelo: $MODEL | n_tokens: $N | inicio: $(date +%H:%M:%S)"
echo "prompt: $PROMPT" | tee "$TRACES/$NAME.prompt.txt"

LLAMA_TRACE_MOE="$TRACES/$NAME.trace" timeout 5400 "$BIN" -m "$MODEL" -ngl 0 -st -no-cnv \
  -p "$PROMPT" -n "$N" -t 8 --no-display-prompt > "$TRACES/$NAME.gen.txt" 2>&1

echo "fin: $(date +%H:%M:%S)"
echo "trace líneas: $(wc -l < "$TRACES/$NAME.trace")"
echo "gen bytes: $(wc -c < "$TRACES/$NAME.gen.txt")"
