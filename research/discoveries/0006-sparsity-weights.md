# Descubrimiento 0006 (CORREGIDO tras auditoría)

## Hipótesis

H-007: los pesos de los expertos del Qwen3-235B contienen sparsity estructurada
explotable sin entrenamiento que reduce los BYTES leídos (no solo FLOPs).

## Motivación

El término dominante del tráfico NVMe es la lectura de pesos de expertos. Si una
fracción estructural de esos pesos es cero, se puede omitir su lectura.

## Estado previo del conocimiento

- Ciclo 2 (0004): la locality de expertos no es explotable hasta 37.5 MB/token con caché.
- Versión inicial de este discovery (REFUTADA por auditoría): afirmaba "36.5% de
  neuronas muertas del modelo" basándose SOLO en la capa 0 — extrapolación indebida.

## Estado del arte relacionado

- PowerInfer/TurboSparse: sparsity de activación ENTRENADA (~95% neuronas FFN inactivas).
- La sparsity de pesos de LLM densos es típicamente ~0% de ceros exactos.

## Experimento (CORREGIDO — conservado en weight_analysis.py v3)

E007: dequantización Q4_K (layout b10333, control token_embd 0.25% ceros) de los
pesos del Qwen3-235B. Sparsity por CAPA (gate, 128 expertos × 30 filas c/u) sobre las
19 capas del shard 1; entropía de nibbles; SVD del gate del experto vivo.

## Configuración

Shard 1 del 235B Q4_K_M (capas 0-18). Tensores ffn_gate_exps[4096, 1536, 128].

## Resultado (CORREGIDO)

| Capa | Ceros exactos (gate) |
|---|---|
| 0 | 36.49% |
| 1 | 15.65% |
| 2 | 8.45% |
| 3-4 | ~3.8% |
| 5-18 | **0.44-2.68%** |
| **MEDIA PONDERADA (shard 1)** | **4.53%** |

- Control token_embd: 0.25% de ceros (dequantización correcta).
- **La sparsity es ALTAMENTE dependiente de la capa**: la capa 0 (36.5%) es una
  anomalía; las capas 5-18 tienen <2.7% de ceros (densas, como LLM típicos).
- SVD del gate (experto 45, capa 0, filas vivas): rango 99% en 93.2% de las vivas
  (rango alto — sin estructura low-rank).

## Evidencia

experiments/E007/weight_analysis.py (v3, conservado — reproduce estas cifras).

## Qué demuestra (CORREGIDO)

1. **La sparsity de pesos del modelo es ~4.5% (media), NO 36.5%**: la capa 0 es una
   anomalía de entrenamiento; el modelo global es denso (los LLM típicos tienen
   <1-3% de ceros).
2. **El skipping de filas muertas reduce solo ~3% de los bytes del FFN** (2×4.53%/3)
   → 2.87 → ~2.78 GB/token. NO explotable para el objetivo.
3. La capa 0 con 36.5% de sparsity es un hallazgo secundario (fenómeno de
   entrenamiento de capas tempranas), no una propiedad del modelo.

## Qué NO demuestra

- No mide la sparsity de ACTIVACIONES dinámica (SiLU) — las neuronas vivas pueden
  activarse o no por token (H-007b, NO TESTEABLE en el ciclo — requiere hook en el fork).
- No cubre las capas 19-93 (shards 2-5) — la media del shard 1 (4.53%) es la base;
  la tendencia decreciente sugiere que las capas profundas son aún más densas.

## Conocimiento modificado

- **H-007: REFUTADA** (tras corrección) — la sparsity de pesos del modelo es ~4.5%
  (no explotable); la reducción real ~3% de bytes. La expectativa inicial ("sparsity
  estructurada entrenada") se refuta: Qwen3-235B es denso salvo la capa 0.
- Corrección del claim previo: el "36.5% de neuronas muertas" era de la capa 0 sola.

## Estado

🟢 Demostrado (corregido y reproducible con el script conservado).

## Confianza

Alta (medición por capa sobre el shard 1 completo; script conservado).

## Próxima hipótesis

La sparsity de activaciones dinámicas (SiLU) de las neuronas VIVAS — requiere
instrumentación del forward (H-007b).

## Próximo experimento

H-007b (futuro): hook en el gate del fork para medir la fracción activa por token.

## Prior-art check (novedad)

- La sparsity de activación ENTRENADA (ReLU, TurboSparse/PowerInfer) es conocida:
  nuestra medición de sparsity de PESOS (ceros exactos) en Qwen3-235B es una medición
  nueva del modelo, pero el fenómeno "sparsity dependiente de la capa" no se declara
  novedoso. **Resultado observado en este estudio; novedad no establecida.**
- El hallazgo específico (capa 0 con 36.5% de ceros vs capas medias <2.7%) podría
  relacionarse con la literatura de "layer-wise sparsity" en LLM — no verificado con
  una búsqueda específica; se documenta sin claim.
