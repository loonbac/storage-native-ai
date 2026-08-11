# E001 — Baseline convencional en VRAM

**Fecha:** 2026-08-11
**Objetivo:** medir el rendimiento de referencia de inferencia 100% en VRAM (sin offloading)
para calibrar la escalera experimental y fijar el techo de generación de la RTX 3060.

## Configuración

### Hardware
| Componente | Valor |
|---|---|
| GPU | NVIDIA RTX 3060 12 GB (GA106 LHR, sm_86), driver 610.57.04 |
| CPU | AMD Ryzen 7 5700X, 8C/16T |
| RAM | 32 GB DDR4-3200 (dual channel) |
| Disco | NVMe SK Hynix 238G (modelos en /home/loonbac/Projects/models) |

### Software
| Componente | Versión |
|---|---|
| OS | Arch Linux |
| llama.cpp | b10333 (8dc0728), CUDA build (llama.cpp-cuda, sm_86) |
| CUDA | 13.3.73 (toolkit), driver runtime 610.57.04 |

### Modelo
| Campo | Valor |
|---|---|
| Modelo | Qwen2.5-7B-Instruct (bartowski GGUF) |
| Quant | Q4_K_M |
| Parámetros | 7.62 B |
| Tamaño | 4.36 GiB (4.68 GB) |
| Bytes/parámetro | 4.36 GiB / 7.62 B = 0.572 B/param |
| Contexto | 32768 (default del modelo) |

### Flags de ejecución
- `-ngl 99` — todos los layers en GPU (baseline 100% VRAM)
- `-t 8` — 8 hilos CPU (para ops no-CUDA)
- llama-bench: `-p 128,512 -n 128,256 -r 2`
- llama-cli: `-st -no-cnv -n 200 --no-display-prompt`

## Comandos reproducibles

```bash
# Benchmark
llama-bench -m models/Qwen2.5-7B-Instruct-Q4_K_M.gguf -ngl 99 -p 128,512 -n 128,256 -t 8 -r 2

# TTFT + generación real
llama-cli -m models/Qwen2.5-7B-Instruct-Q4_K_M.gguf -ngl 99 -st -no-cnv \
  -p "Escribe una breve explicación de qué es un modelo de lenguaje grande." \
  -n 200 -t 8 --no-display-prompt

# Script reproducible
research/experiments/E001/run_benchmark.sh
```

## Logs

- `logs/run-20260811-124233.log` — salida completa de llama-bench
- `logs/e001_gen.txt` — generación real (200 tokens) con métricas
- `logs/gen-20260811-124233.txt`, `logs/ttft-20260811-124233.err` — run inicial

## Métricas

Ver `metrics.md`. Resumen: pp512 = 2411 t/s, generación = 68.8 t/s, TTFT ≈ 0.08 s,
VRAM pico = 4781 MiB.

## Análisis

Ver `analysis.md`. Conclusión clave: el baseline 7B Q4_K_M está **limitado por ancho de
banda de VRAM** (~89% del techo teórico), no por cómputo — el techo de generación de
cualquier modelo denso en esta GPU es ~360 GB/s ÷ bytes-por-token.
