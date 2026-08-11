#!/bin/bash
# E001 — Baseline convencional en VRAM (Qwen2.5-7B Q4_K_M, -ngl 99)
# Reproducible: mismo hardware, mismas versiones, mismos flags.
set -euo pipefail

MODEL="/home/loonbac/Projects/models/Qwen2.5-7B-Instruct-Q4_K_M.gguf"
OUTDIR="$(dirname "$0")"
TS=$(date +%Y%m%d-%H%M%S)

echo "=== E001 baseline ===" | tee "$OUTDIR/logs/run-$TS.log"
echo "Inicio: $TS" | tee -a "$OUTDIR/logs/run-$TS.log"
echo "Hardware: $(nvidia-smi --query-gpu=name --format=csv,noheader)" | tee -a "$OUTDIR/logs/run-$TS.log"
echo "llama.cpp: $(llama-cli --version 2>&1 | head -1)" | tee -a "$OUTDIR/logs/run-$TS.log"

# 1) Benchmark llama-bench: prompt processing (pp) y generation (tg)
echo "--- llama-bench ---" | tee -a "$OUTDIR/logs/run-$TS.log"
llama-bench -m "$MODEL" -ngl 99 -p 128,512 -n 128,256 -t 8 -r 2 2>&1 | tee -a "$OUTDIR/logs/run-$TS.log"

# 2) TTFT y generación real con llama-cli (single turn)
# Nota: Arch no trae /usr/bin/time; se usa el builtin de bash con TIMEFORMAT
echo "--- llama-cli TTFT ---" | tee -a "$OUTDIR/logs/run-$TS.log"
/usr/bin/bash -c "TIMEFORMAT='wall=%3R s'; time llama-cli -m '$MODEL' -ngl 99 -st -no-cnv \
  -p 'Escribe una breve explicación de qué es un modelo de lenguaje grande.' \
  -n 200 -t 8 --no-display-prompt \
  > '$OUTDIR/logs/gen-$TS.txt' 2>&1" 2>>"$OUTDIR/logs/ttft-$TS.txt" | tee -a "$OUTDIR/logs/run-$TS.log"
echo "(métricas en logs/ttft-$TS.txt; stderr con métricas)" | tee -a "$OUTDIR/logs/run-$TS.log"

echo "Fin: $(date +%Y%m%d-%H%M%S)" | tee -a "$OUTDIR/logs/run-$TS.log"
