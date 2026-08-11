# E001 — Métricas

Fecha: 2026-08-11. Todas las medidas con Qwen2.5-7B-Instruct Q4_K_M (-ngl 99, CUDA).

## Rendimiento (llama-bench, r=2)

| Test | t/s | Nota |
|---|---|---|
| pp128 (prompt 128 tokens) | 2150.5 ± 106.6 | |
| pp512 (prompt 512 tokens) | 2410.9 ± 19.4 | |
| tg128 (generación 128 tokens) | 68.79 ± 0.01 | |
| tg256 (generación 256 tokens) | 68.76 ± 0.01 | |

## Rendimiento (llama-cli real, single turn, 200 tokens)

| Métrica | Valor |
|---|---|
| Prompt processing | 1100.7 t/s |
| Generation | 68.7 t/s |
| Wall total (incluye carga modelo) | 4.393 s |
| TTFT (primer token tras carga) | ~0.08 s (carga excluida, inferido) |

## Memoria

| Métrica | Valor |
|---|---|
| VRAM usada (bench corto, ctx ≤ 256) | ~4781 MiB |
| VRAM usada (gen 512 tokens, ctx default 32K) | ~6573 MiB |
| VRAM total | 11906 MiB |
| RSS del proceso (RAM) | **803 MiB** |
| Peso del modelo | 4.36 GiB |
| KV cache preasignada (ctx 32K, 24 layers, GQA 4 KV heads) | ~2.1 GiB (6573 − 4470 de pesos) |

## Bytes por token (análisis de BW)

| Métrica | Valor |
|---|---|
| Bytes de pesos leídos por token (todos residentes en VRAM) | 4.68 GB |
| Tráfico VRAM efectivo @68.8 t/s | 4.68 × 68.8 = **~322 GB/s** |
| Techo BW VRAM GDDR6 (RTX 3060) | 360 GB/s |
| Utilización del BW de VRAM | **~89%** |

## Calidad (muestra)

Prompt: "Escribe una breve explicación de qué es un modelo de lenguaje grande."
Respuesta (en español, coherente, bien estructurada): define LLM como red neuronal
profunda entrenada en texto, menciona miles de millones de parámetros y patrones
semánticos, lista características. Sin artefactos visibles en la muestra.
(Ver `logs/e001_gen.txt` para la respuesta completa. Evaluación formal pendiente.)

## Conclusión de medición

El baseline 7B Q4_K_M genera 68.8 t/s, limitado por BW de VRAM (~89% del techo).
Implicación: el techo de generación de un modelo denso es `360 GB/s ÷ bytes_por_token`.
Para un objetivo de 40 t/s, un modelo denso puede tener hasta ~9 GB de pesos/token
(~16B params Q4) SIN saturar VRAM — pero solo si cabe en los 12 GB.
