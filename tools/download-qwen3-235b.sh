#!/bin/bash
# Descarga de Qwen3-235B-A22B Q4_K_M (5 shards, ~142 GB) desde el repo oficial de Qwen.
# Con resume (-C -) por si se interrumpe. Log en download-qwen3-235b.log
set -u
cd /home/loonbac/Projects/models || exit 1
BASE="https://huggingface.co/Qwen/Qwen3-235B-A22B-GGUF/resolve/main/Q4_K_M"
for n in 00001 00002 00003 00004 00005; do
  out="Qwen3-235B-A22B-Q4_K_M-${n}-of-00005.gguf"
  if [ -s "$out" ]; then
    sz=$(stat -c%s "$out")
    echo "$(date +%H:%M:%S) $out ya existe ($sz bytes)" | tee -a download-qwen3-235b.log
    continue
  fi
  echo "$(date +%H:%M:%S) descargando $out ..." | tee -a download-qwen3-235b.log
  curl -sL -C - -o "$out" "$BASE/$out" 2>&1 | tee -a download-qwen3-235b.log
  echo "$(date +%H:%M:%S) $out: $(stat -c%s "$out") bytes" | tee -a download-qwen3-235b.log
done
echo "$(date +%H:%M:%S) DESCARGAS COMPLETAS" | tee -a download-qwen3-235b.log
