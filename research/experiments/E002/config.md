# E002 — Modelo fuera de VRAM (Nivel 0-1)

**Fecha:** 2026-08-11
**Objetivo:** demostrar inferencia con un modelo **significativamente mayor que la VRAM**
(Qwen3-235B-A22B: 142 GB Q4_K_M vs 12 GB VRAM = **~12× VRAM**, Nivel 0-1 de la escalera)
ejecutándose con streaming/offloading desde NVMe, y medir qué limita el rendimiento.

## Configuración

### Hardware
| Componente | Valor |
|---|---|
| GPU | NVIDIA RTX 3060 12 GB (GA106 LHR, sm_86), driver 610.57.04 |
| CPU | AMD Ryzen 7 5700X, 8C/16T |
| RAM | 32 GB DDR4-3200 (37 GB/s copy medido, 28 GB/s read) |
| NVMe | SK Hynix 238G — 1.1-1.6 GB/s secuencial, 84 µs random 4K (0001) |
| PCIe H2D | 26.7 GB/s medido (0002) |

### Software
| Componente | Versión |
|---|---|
| OS | Arch Linux |
| llama.cpp | b10333 (8dc0728), CUDA build (llama.cpp-cuda, sm_86) |
| CUDA | 13.3.73, driver 610.57.04 |

### Modelo
| Campo | Valor |
|---|---|
| Modelo | Qwen3-235B-A22B (MoE: 235B totales / 22B activos ≈ 9.4%) |
| Quant | Q4_K_M (repo oficial Qwen) |
| Tamaño | 142.15 GB en 5 shards |
| Params | 235.0 B totales, ~22 B activos por token |
| Bytes/param | ~0.605 B/param |
| Ratio vs VRAM | 142.15 GB / 12 GB ≈ **11.8×** |
| Ruta | `/home/loonbac/Projects/models/Q4_K_M/` |

### Descarga
- Herramienta: `hf download` con Xet (`HF_XET_HIGH_PERFORMANCE=1`) — ~300 MB/s vs ~10 MB/s de curl.
- Repo: `Qwen/Qwen3-235B-A22B-GGUF` (oficial), include `Q4_K_M/*`.
- Checksum: verificado por `hf download` (Xet hace hash-verificación).

## Método

llama.cpp con mmap: los pesos se leen del NVMe bajo demanda y quedan en page cache.
Tres configuraciones de offload:

| Run | `-ngl` | Descripción |
|---|---|---|
| E002a | 0 | Todo CPU (mmap desde NVMe) — streaming puro |
| E002b | 4 | 4 layers en GPU (~9.2 GB, el máximo que cabe en 12 GB con KV) — híbrido |

Nota: se descartaron ngl 20/40 — cada layer del 235B pesa ~2.3 GB; 20 layers ≈ 46 GB
exceden los 12 GB de VRAM. -ngl 4 fue el máximo residente realista.

Métricas por run: tokens/s (pp + tg), TTFT, VRAM pico, RSS, **I/O real del NVMe
durante generación** (iostat via /proc/diskstats), bytes/token efectivos.

### ¿Qué mide esto?

1. **Nivel 0-1 demostrado**: si Qwen3-235B genera texto (aunque sea lento) desde NVMe,
   se demuestra inferencia de un modelo ~12× la VRAM en 1 GPU consumer.
2. **S4 — locality real de routing (variable crítica del North Star)**: el I/O del NVMe
   durante generación revela cuántos bytes de pesos se leen por token. Si el tráfico es
   mucho menor que 142 GB/token (o que 12.3 GB/token de activos sin caché), la locality
   + page cache están funcionando (H-003). El techo de 40 tok/s necesita ≤ 37.5 MB/token
   desde NVMe (bottleneck-analysis §2).
3. **H-001**: ¿es el NVMe el cuello de botella? Comparar tokens/s entre E002a/b/c con el
   I/O medido.

## Comandos reproducibles

```bash
# Descarga
HF_XET_HIGH_PERFORMANCE=1 hf download Qwen/Qwen3-235B-A22B-GGUF \
  --include "Q4_K_M/*" --local-dir /home/loonbac/Projects/models

# Benchmark (ngl variable)
research/experiments/E002/run_benchmark.sh <ngl>

# Run manual (streaming puro, todo CPU)
llama-cli -m models/Q4_K_M/Qwen3-235B-A22B-Q4_K_M-00001-of-00005.gguf \
  -ngl 0 -st -no-cnv -p "..." -n 64 -t 8 --no-display-prompt
```

## Logs

- `logs/run-ngl{0,20,40}-*.log` — salida de cada run con métricas
- `logs/*.io` — muestreo de I/O NVMe durante generación
- `logs/gen-*.txt` — texto generado
