# Descubrimiento 0004

## Hipótesis

La locality de activación de expertos de Qwen3-MoE es lo suficientemente concentrada
como para que una caché de expertos la explote (H-006). Se esperaba una distribución
con pocos expertos dominantes (ley de potencia).

## Motivación

Determinar la estructura de la locality real (la variable S4 del ciclo 1, nunca aislada)
y dimensionar la caché de expertos.

## Estado previo del conocimiento

- E002 (0003): locality efectiva 78% bajo page cache (mezclada con política LRU del kernel).
- P-007 (literatura): "no todos los MoE tienen localidad de routing" — Qwen3 sin medir.
- Expectativa inicial: distribución sesgada (top pocos expertos dominan).

## Estado del arte relacionado

- MoE-Infinity (2401.14361): sparsity-aware expert cache para batch=1.
- Oracle-MoE (ICML'25): routers con poca localidad temporal.

## Experimento

E002d + E006.3: tracer de routing en llama.cpp (fork b10333, LLAMA_TRACE_MOE) capturó
los expertos top-8 por capa por token de Qwen3-30B-A3B (4 prompts × 300 tokens) y
Qwen3-235B-A22B (700 tokens, prompt de razonamiento). Análisis: distribución de
frecuencias, working set por ventana, reuse distance, hit rate de caché temporal.

## Configuración

Hardware: RTX 3060 12GB, Ryzen 7 5700X, 32GB RAM. Software: llama.cpp fork b10333
con tracer (experiments/E002d/llama-moe-tracer.patch). Modelos: Qwen3-30B-A3B Q4_K_M
(48 capas, 128 expertos, top-8, 2.92 MB/experto) y Qwen3-235B-A22B Q4_K_M (94 capas,
128 expertos, top-8, 11.42 MB/experto). ngl=0, t=8.

## Resultado (30B — promedio 4 prompts; 235B — 690 tokens)

| Métrica | Qwen3-30B-A3B | Qwen3-235B-A22B |
|---|---|---|
| Expertos únicos/token (de 128) | 109.6-111.0 | 123.8 |
| Redundancia intra-token | 71.1-71.5% | 83.5% |
| Top-10% expertos cubren | 16.1-19.3% | 14.5% |
| Top-25% cubren | 36.6-41.6% | 34.7% |
| Working set W=8 (por capa) | 27-30/128 (21-23%) | 28/128 (22%) |
| Working set W=32 (por capa) | 44-53/128 (35-42%) | 50/128 (39%) |
| Reuse distance P50 | 2 tokens | 2 tokens |
| Reuse distance P90 | 14-18 tokens | 18 tokens |
| Hit rate caché W=8 (por capa) | 61-63% | 62.9% |
| Hit rate caché W=32 (por capa) | 68.5-70.4% | 69.9% |

## Evidencia

experiments/E006/traces/*.trace (crudos), analyze_locality.py (reproducible),
cache_simulator.py (simulación). Prompts variados (matemáticas, código, técnica,
narrativa) con varianza mínima entre ellos.

## Qué demuestra

1. **La locality de Qwen3-MoE es REAL y ESTABLE** entre prompts y tamaños de modelo:
   reuse distance P50 = 2 tokens, hit rate ~70% con ventana de 32 tokens por capa.
2. **La distribución es PLANA, no una ley de potencia**: top-25% de expertos cubren
   solo ~35-42% de activaciones (un sesgo fuerte daría >80%). No hay "pocos expertos
   dominantes" seleccionables por frecuencia.
3. **El working set por capa crece lentamente pero es amplio**: W=32 → ~39-42% de los
   128 expertos por capa. En términos absolutos (94 capas × 11.42 MB): la ventana de 32
   tokens del 235B necesita ~54 GB de caché.
4. La redundancia intra-token es ALTÍSIMA (71-83%): los mismos ~110-124 expertos se
   re-activan en las 94-48 capas del mismo token.

## Desglose expertos vs no-expertos (requisito E006.3, GGUF real)

Medido sobre el archivo Qwen3-235B-A22B-Q4_K_M (5 shards, 235.09B params, 0.6047 B/param):

| Componente | Params | GB | % del modelo |
|---|---|---|---|
| Expertos (12,032 unidades: 94 capas × 128) | 227.10B | **137.31** | 96.6% |
| Attention (658 tensores) | 6.70B | 4.05 | 2.8% |
| Embeddings + output (2 tensores) | 1.24B | 0.75 | 0.5% |
| Router (ffn_gate_inp, 94) | 0.05B | 0.03 | <0.1% |
| **Total no-expertos** | 8.00B | **4.84** | 3.4% |
| TOTAL | 235.09B | 142.15 | 100% |

Implicación para el tráfico: los no-expertos (4.84 GB) se activan SIEMPRE por token
(4.84 GB/token brutos), pero caben enteros en la page cache de 32 GB RAM → tráfico NVMe
≈ 0 tras la primera lectura (warmup). **El tráfico de almacenamiento está dominado al
100% por los expertos** — los números del simulador de caché de expertos son el análisis
completo del problema (los no-expertos no aportan tráfico NVMe sostenido).

Análisis por UNIDAD (capa, experto) — 12,032 unidades (el §2 por índice agrega capas):
- 9,216/12,032 unidades distintas usadas (76.6%) en 690 tokens (p1).
- Concentración por unidad: top-0.1% (12 unid) = 1.4%, top-1% (120) = 10.6%,
  top-5% (601) = 33.6%, top-10% (1203) = 51.3% de activaciones.
- Ratio max/media por unidad: 11.8× (vs 1.8× por índice) — hay unidades calientes
  específicas, pero el top-10% aún requiere 1,203 unidades ≈ 13.7 GB de caché para
  cubrir la mitad de las activaciones.

## Qué NO demuestra

- No mide con contexto largo (>700 tokens) ni batch > 1.
- No distingue locality de routing pura de la influencia del prompt (misma familia de
  prompts de razonamiento; aunque la varianza entre 4 prompts distintos fue mínima).
- No cubre otros modelos (solo la familia Qwen3-MoE).
- La página cache del kernel (32GB) ya amortigua parte del tráfico en la práctica.

## Conocimiento modificado

- **S4 resuelto (familia Qwen3-MoE)**: locality real y moderada (~70% a W=32), NO
  extrema. La expectativa de "pocos expertos calientes" (ley de potencia) se REFUTA.
- **H-006 queda bajo sospecha**: con distribución plana y working set amplio, la caché
  de expertos debe retener muchísimo para cubrir la reutilización. El simulador (0005)
  cuantifica el veredicto.

## Estado

🟢 Demostrado (para la familia Qwen3-MoE, esta configuración).

## Confianza

Alta (tracer validado: formato 100% OK, 0 índices fuera de rango, cobertura 48/48 y
94/94 capas uniforme; 5 traces, 2 modelos, 4+1 prompts).

## Próxima hipótesis

El working set amplio + distribución plana hacen que la caché de expertos no alcance
37.5 MB/token con capacidades realistas (≤44GB) — cuantificado en 0005 (Oracle).

## Próximo experimento

E006.1: simulador Oracle/LRU/LFU sobre los traces (ejecutado — ver 0005).
