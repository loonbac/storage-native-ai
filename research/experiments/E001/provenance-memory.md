# E001 — Proveniencia de mediciones de memoria

Registro crudo de las mediciones de VRAM/RSS/RAM del baseline (complementa metrics.md).
Fecha: 2026-08-11. Método: muestreo activo durante generación.

## VRAM durante generación (Qwen2.5-7B Q4_K_M, -ngl 99)

```
Muestreo nvidia-smi (memory.used) durante benchmark llama-bench (ctx ≤ 256): 4781 MiB
Muestreo nvidia-smi durante generación 512 tokens (ctx default 32K):       6573 MiB
VRAM total: 11906 MiB
```

Interpretación: 6573 − 4470 (pesos) = ~2.1 GiB de KV cache preasignada (ctx 32K,
24 layers, GQA 4 KV heads, FP16).

## RSS del proceso llama-cli

```
$ pgrep -x llama-cli → pid; grep VmRSS /proc/$pid/status → 803 MiB
(muestreo a los 2 s de una generación de 512 tokens; 3 muestras estables en 803 MiB)
```

## BW de RAM (S2, medido para bottleneck-analysis)

```
numpy copy 1 GB (float32, read+write): 58.1 ms → 36.94 GB/s
numpy sum 1 GB (read-only):            38.0 ms → 28.29 GB/s
(referencia: DDR4-3200 dual channel teórico 51.2 GB/s → 72% eficiencia)
```

## TTFT

No medido directamente (el flag -no-display-prompt del primer intento falló por guion
simple). El wall de la generación (4.393 s para carga + 200 tokens a 68.7 t/s ≈ 2.9 s)
implica carga ≈ 1.5 s y TTFT ≈ 0.08 s (marcado como INFERENCIA en metrics.md).

## Comandos reproducibles

```bash
# VRAM
nvidia-smi --query-gpu=memory.used --format=csv,noheader
# RSS
pgrep -x llama-cli && grep VmRSS /proc/$(pgrep -x llama-cli)/status
# RAM BW
python3 -c "import numpy as np,time; a=np.ones(256*1024*1024,np.float32); b=np.zeros_like(a); t=time.perf_counter(); [b.__setitem__(slice(None),a) for _ in range(5)]; print(1*2/((time.perf_counter()-t)/5))"
```
