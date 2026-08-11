# E002 — Métricas

Fecha: 2026-08-11. Modelo: Qwen3-235B-A22B Q4_K_M (142.15 GB, 5 shards) desde NVMe.
Modelo = 11.8× la VRAM (12 GB). Prompt: 5 tokens, generación: 64 tokens, ctx 4096.

## Resultados por configuración

| Métrica | E002a (-ngl 0) | E002b (-ngl 4) |
|---|---|---|
| Wall total (carga + prompt + 64 tokens) | 382.6 s | 366.6 s |
| Prompt processing | 0.4 t/s | 0.4 t/s |
| Generation | **0.4 t/s** | **0.4 t/s** |
| VRAM pico (muestreo activo) | 316 MiB (idle) | **6353 MiB** (media 4339) |
| I/O NVMe medio durante TODO el run | **1093 MiB/s** | **1095 MiB/s** |
| I/O NVMe pico | 1331 MiB/s | — |
| Tiempo de carga estimado (142 GB @ 1.09 GB/s) | ~130 s | ~130 s |

## Análisis de tráfico (el dato clave)

| Métrica | Valor |
|---|---|
| I/O NVMe sostenido durante generación | 1093–1095 MiB/s ≈ 1.15 GB/s |
| Tráfico NVMe por token | 1.15 GB/s ÷ 0.4 t/s = **~2.87 GB/token** |
| Params Q4 equivalentes por token desde NVMe | ~5.1 B (de 22 B activos) |
| Fracción de activos servida por page cache RAM | **~78%** (1 − 2.87/12.3) |
| Techo si el NVMe estuviera al 100% | 0.4 t/s — el cuello real |

## Calidad (muestra)

El modelo genera texto coherente en modo thinking (Qwen3), en inglés, con razonamiento
estructurado. Ver `logs/gen-ngl0-20260811-133210.txt`. Evaluación formal pendiente.

## Predicciones (predictions.md) — resultado

| Predicción | Resultado | Veredicto |
|---|---|---|
| P-E2-1: 1.5–3.5 t/s (ngl=0) | 0.4 t/s | **REFUTADA** (fuera de rango) |
| P-E2-2: I/O bajo tras warmup (< 200 MB/s) | 1093 MiB/s sostenido | **REFUTADA** (page cache 32 GB << 142 GB) |
| P-E2-3: 3–12 t/s (ngl parcial) | 0.4 t/s (invariante) | **REFUTADA** |
| P-E2-4: tráfico < 12.3 GB/token | 2.87 GB/token | **CONFIRMADA** (locality real ~78%) |
| P-E2-5: TTFT 10–90 s | ~130 s carga + prompt | **PARCIAL** (carga lenta, en rango alto) |

## Por qué fallaron las predicciones

Todas las predicciones asumieron el modelo de "tráfico = activos sin reutilización" para
estimar el cuello. La realidad: el page cache (32 GB) NO retiene el modelo de 142 GB →
thrashing → el NVMe queda saturado al ~100% y la generación se vuelve 100% I/O-bound en
el NVMe. La locality existe (78% servido por RAM) pero el NVMe sigue siendo el techo:
2.87 GB/token × 0.4 t/s = 1.15 GB/s = exactamente el BW del NVMe.
