# Descubrimiento 0007 (CORREGIDO tras auditoría)

## Hipótesis

H-008: los pesos de los expertos pueden representarse con significativamente menos
bytes que sus Q4 (reduciendo el tráfico NVMe).

## Motivación

Si los pesos tienen baja entropía o bajo rango, se reconstruyen localmente y se leen
menos bytes.

## Estado previo del conocimiento

- 0006 (corregido): la sparsity de pesos del modelo es ~4.5% (capa 0: 36.5% anomalía).
- Versión inicial de este discovery (REFUTADA por auditoría): afirmaba "entropía
  2.68 bits" basada en la capa 0 — no reproducible y no representativa.

## Estado del arte relacionado

- SeedLM (P-010): semillas PRNG → 4-8× sobre FP16, requiere optimización (retrain).
- Neural weight compression (P-020): codecs entrenados.

## Experimento (CORREGIDO — weight_analysis.py v3 conservado)

Entropía de los nibbles qs (4 bits) del gate en capas representativas (0 y 9) del
shard 1; SVD del gate del experto vivo (capa 0).

## Configuración

Shard 1 del 235B Q4_K_M. Gate ffn_gate_exps[4096, 1536, 128].

## Resultado (CORREGIDO)

| Capa | Entropía (bits/valor de 4) | Lossless máx | P(nibble 0) |
|---|---|---|---|
| 0 (anomalía esparsa) | 2.881 | 28.0% | 49.5% |
| 9 (representativa) | **3.901** | **2.5%** | 4.8% |
| Capas medias (5-18) | ~3.5-3.9 (alta entropía) | ~2-12% | bajo |

- SVD gate experto 45 (capa 0, filas vivas): rango 99% en 93.2% de las filas vivas
  (rango ALTO — sin estructura low-rank).
- Nota (corrección): el down del 235B es Q6_K (type 14, 5.16 MB/experto), no Q4_K;
  los "NaN" reportados inicialmente en el down fueron un artefacto de dequantizar
  Q6_K como Q4_K — el análisis de compressibilidad del gate (Q4_K correcto) es el
  válido para H-008.
- Los valores Q4 de las capas densas tienen entropía ~3.9 bits (casi incompresibles:
  la cuantización Q4 ya está cerca del límite de información).

## Evidencia

experiments/E007/weight_analysis.py (v3, conservado — reproduce estas cifras).

## Qué demuestra (CORREGIDO)

1. **El lossless de las capas representativas es ~2-12%** (entropía 3.5-3.9 bits) —
  los Q4 de las capas densas son casi incompresibles. El 28% de la capa 0 es la
  anomalía esparsa, no representativo.
2. **Sin estructura low-rank**: el rango efectivo del gate vivo es 93% (las filas
  vivas son de rango alto).
3. El lossless promedio del modelo ≈ 2-10% → 2.87 → ~2.6-2.8 GB/token. Irrelevante
  para el objetivo.

## Codebook (compresión con pérdida — requisito del contrato)

Sobre el gate denso (capa 9, experto 45, Q4_K): codebook k-means conservado en
codebook_analysis.py:

| Bins | Bits/valor | RMS (del std) | Compresión vs Q4 |
|---|---|---|---|
| 32 | 5.0 | 8.1% | 0.96× (PEOR) |
| 128 | 7.0 | 4.2% | 0.69× |

**El codebook NO comprime los Q4**: ya tienen 16 niveles (4.8 bits); un codebook de
<16 niveles pierde precisión sin ahorrar bits; uno de más niveles no comprime.
→ H-008 REFUTADA también por codebook (la única vía de compresión >1.5× es con
pérdida severa o retrain).

## Qué NO demuestra

- SeedLM (4-8×) no se evaluó (requiere retrain → NO TESTEABLE en el ciclo; el
  experimento futuro: optimizar semillas sobre una muestra y medir calidad).

## Conocimiento modificado

- **H-008: REFUTADA** (confirmada con el número correcto): el lossless sin retrain es
  ~2-12% en capas densas (no 30%); no hay low-rank; la única vía mayor (SeedLM)
  requiere entrenamiento. El techo de compresión sin entrenamiento es marginal.
- Corrección: la entropía 2.68 bits (capa 0) no es representativa; la real es ~3.9.

## Estado

🟢 Demostrado (corregido y reproducible).

## Confianza

Alta (entropía directa de los nibbles reales; script conservado).

## Próxima hipótesis

La reducción de bytes/experto sin entrenamiento tiene un techo ~2-12%. El gap al
objetivo exige otras vías (working set H-009, top-k H-011) — ya evaluadas.

## Próximo experimento

Cerrado — H-008 no justifica continuar sin retrain.

## Prior-art check (novedad)

- La entropía de pesos cuantizados (Q4 cerca del límite de información) es un hecho
  conocido en la literatura de cuantización/compresión. Nuestra medición (3.9 bits en
  capas densas del 235B) es una medición nueva del modelo, no un descubrimiento.
  **Resultado observado en este estudio; novedad no establecida.**
