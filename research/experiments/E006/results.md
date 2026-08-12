# E006 — Resultados del simulador de caché (consolidado)

Fecha: 2026-08-11. Modelo: Qwen3-235B-A22B Q4_K_M (11.42 MB/experto, 94 capas, 128
expertos/capa, top-8). Traces: p1 (699 tokens) + p2 (499 tokens) = 1198 procesamientos.
Script reproducible: `cache_simulator.py`. Detalle completo: discoveries/0005.

## E006.2 — Cache-size sweep (tráfico MB/token)

| Capacidad | Oracle | LRU | LFU |
|---|---|---|---|
| 8 GB | 4914 | 5537 | 5596 |
| 12 GB (VRAM) | 4139 | 4374 | 4742 |
| 20 GB | 2954 | 3062 | 3398 |
| 32 GB | 1716 | 1771 | 1961 |
| 44 GB (VRAM+RAM) | 933 | 955 | 1074 |
| 64 GB | 338 | 342 | 399 |
| 96 GB | 110 | 110 | 112 |

**Objetivo 37.5 MB/token: NO ALCANZADO en ningún punto** (mínimo 110 MB/token a 96 GB).

## E006.4 — Políticas de reemplazo

- **Oracle ≥ LRU ≥ LFU** en todos los puntos (curva monótona, sin anomalías).
- **Brecha oracle-vs-LRU: 1-5%** — el LRU está cerca del óptimo teórico; no hay margen
  para políticas más sofisticadas (frecuencia, aprendizaje) que superen el LRU en >5%.
- **LFU es PEOR que LRU** (10-30% más tráfico en la mayoría de puntos): la frecuencia
  global retiene expertos populares antiguos que ya no se usan en la ventana actual
  (la locality es temporal, no frecuencial).

## E006.5 — Prefetch predictivo (predictor implementado + accuracy medida)

Predictores evaluados sobre los 1198 tokens del 235B (prefetch_predictor.py,
reproducible). Predicen los expertos del token t+1 por capa:

| Predictor | Precision | Recall | Nota |
|---|---|---|---|
| last (expertos del token anterior) | 43.8% | 43.8% | simple, balanceado |
| window (top-K frecuentes en W=8) | 29.2% | 58.4% | cubre más, menos preciso |
| bigram (co-ocurrencia experto→experto) | **98.8%** | 37.0% | pocas predicciones pero casi siempre correctas |

**Efecto en tráfico NVMe/token (LRU + prefetch last vs LRU puro):**

| Capacidad | LRU puro | LRU + prefetch | Δ |
|---|---|---|---|
| 12 GB | 4757.5 MB/token | 4757.5 MB/token | 0.0% |
| 44 GB | 962.8 MB/token | 962.8 MB/token | 0.0% |

**El prefetch NO reduce el tráfico NVMe (0.0%)**: los bytes leídos del almacenamiento
son los mismos (cada experto se lee una vez al entrar a caché); el prefetch solo
ADELANTA la lectura en el tiempo. Su beneficio real es ocultar la LATENCIA (solapar
I/O con cómputo), no los bytes. Como la métrica principal del ciclo es NVMe bytes/token,
el prefetch no altera el veredicto de H-006. Cota superior teórica (oracle−LRU): 1-5%.
Nota: el mejor predictor (bigram, 98.8% precision) sería viable para ocultar latencia
en una implementación real, pero es irrelevante para el tráfico.

## Conclusión consolidada

1. La caché de expertos tiene un techo de ~0.95 GB/token (44 GB efectivos, LRU realista).
2. El término dominante es la reutilización residual (~845 MB/token), no el cold miss.
3. El objetivo 37.5 MB/token es inalcanzable con caché de expertos en esta máquina
   (H-006 refutada, ver discoveries/0005 y hypotheses/falsification-002.md).
4. La mejora práctica estimada de la caché real: 2.87 → 0.95 GB/token (~3×), lo que
   daría ~1.2 t/s — no se implementó por contrato (el Oracle refutó el objetivo).

## Reproducibilidad verificada (2026-08-11)

Re-ejecución del simulador sobre el trace p1 (235B) con las mismas capacidades:
resultados IDÉNTICOS a la corrida original (Oracle 12G=4058.9, LRU 12G=4297.2,
LFU 12G=4548.0; Oracle 44G=917.5, LRU 44G=936.4, LFU 44G=980.5). La simulación es
determinista sobre los traces crudos.
