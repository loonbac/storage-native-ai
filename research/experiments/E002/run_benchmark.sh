#!/bin/bash
# E002 — Modelo fuera de VRAM (Nivel 0-1): Qwen3-235B-A22B Q4_K_M desde NVMe
# Mide: tokens/s, TTFT, VRAM, RAM, I/O real del NVMe durante generación.
# Uso: ./run_benchmark.sh [ngl]
set -euo pipefail

MODEL_DIR="/home/loonbac/Projects/models/Q4_K_M"
MODEL="$MODEL_DIR/Qwen3-235B-A22B-Q4_K_M-00001-of-00005.gguf"
NGL="${1:-0}"
OUTDIR="$(dirname "$0")/logs"
mkdir -p "$OUTDIR"
TS=$(date +%Y%m%d-%H%M%S)
LOG="$OUTDIR/run-ngl$NGL-$TS.log"

echo "=== E002 ngl=$NGL ($(date +%H:%M:%S)) ===" | tee "$LOG"
echo "Modelo: Qwen3-235B-A22B Q4_K_M (142 GB, 5 shards)" | tee -a "$LOG"
echo "Hardware: $(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader)" | tee -a "$LOG"
echo "llama.cpp: $(llama-cli --version 2>&1 | head -1)" | tee -a "$LOG"

# Muestreo de I/O NVMe + VRAM en background durante la generación
(
  for i in $(seq 1 240); do
    read0=$(awk '$3=="nvme1n1" {print $6}' /proc/diskstats)
    vram0=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)
    sleep 2
    read1=$(awk '$3=="nvme1n1" {print $6}' /proc/diskstats)
    delta=$(( (read1 - read0) * 512 ))  # sectores -> bytes
    echo "IO $i: $(awk -v d=$delta 'BEGIN { printf "%.2f", d/2/1048576 }') MiB/s" >> "$LOG.io"
    echo "VRAM $i: $vram0 MiB" >> "$LOG.vram"
  done
) &
IOPID=$!

# Carga + generación con timing (carga incluida en wall; TTFT inferido)
/usr/bin/bash -c "TIMEFORMAT='wall=%3R s'; time llama-cli -m '$MODEL' -ngl $NGL -st -no-cnv \
  -p 'Explica brevemente qué es un modelo de lenguaje grande.' -n 64 -c 4096 -t 8 --no-display-prompt \
  > '$OUTDIR/gen-ngl$NGL-$TS.txt' 2>&1" 2>>"$LOG" | tee -a "$LOG"

# VRAM pico durante el run (del muestreo activo)
[ -f "$LOG.vram" ] && awk '{gsub(/MiB/,"",$3); if($3>max)max=$3; sum+=$3; n++} END {printf "VRAM pico (muestreo): %.0f MiB, media: %.0f MiB\n", max, sum/n}' "$LOG.vram" | tee -a "$LOG"

kill $IOPID 2>/dev/null || true

echo "=== métricas finales ===" | tee -a "$LOG"
grep -E "Prompt:|Generation:|wall=" "$LOG" "$OUTDIR/gen-ngl$NGL-$TS.txt" 2>/dev/null | tail -5 | tee -a "$LOG"
echo "VRAM pico: $(cat "$OUTDIR/vram-ngl$NGL-$TS.txt") MiB" | tee -a "$LOG"
echo "=== I/O promedio NVMe ===" | tee -a "$LOG"
awk '{sum+=$4; n++} END {if(n>0) printf "promedio: %.2f MiB/s (n=%d)\n", sum/n, n}' "$LOG.io" | tee -a "$LOG"
