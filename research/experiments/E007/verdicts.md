# Ciclo 3 — Veredictos consolidados y autoauditoría

Fecha: 2026-08-11. Baseline: Qwen3-235B, 2.87 GB/token, ~0.4 t/s (E002).
Target informativo: 37.5 MB/token.

## Tabla de veredictos H-007..H-011

| Hipótesis | Veredicto | Reducción medida/límite | Gap al objetivo (37.5 MB) | Discovery |
|---|---|---|---|---|
| H-007 Sparsity (pesos) | **REFUTADA** (corregido) | sparsity media del modelo **4.53%** (capa 0: 36.5% anomalía; capas 5-18 <2.7%) → **−3%** (2.87→2.78 GB/tok) | 74× | 0006 |
| H-008 Compresión (sin retrain) | **REFUTADA** (corregido) | lossless real **2-12%** en capas densas (entropía 3.9 bits; capa 0 esparsa: 28% — no representativa); sin low-rank (rango 93%); SeedLM requiere retrain (NO TESTEABLE) | 72× | 0007 |
| H-009 Working set (escala) | **PARCIAL** | relación WS/model-size CONSTANTE ~40%; el 30B alcanza **13.3 MB/tok @44GB, 16.9 @12GB** (bajo objetivo) | 0× (con modelo que cabe) | 0010 |
| H-010 Layout físico | **REFUTADA** | 0% — invarianza del LRU por página ante reordenamientos; sin desperdicio de páginas | 77× | 0008 |
| H-011 Top-k reducido | **PARCIAL** | k=4: **−50%** (2.87→1.44 GB/tok) con calidad aceptable; k=2 incoherente | 38× | 0009 |

## Combinación máxima en el 235B (sin retrain)

Con las cifras CORREGIDAS (sparsity 4.53% → ×0.97; lossless 2-12% → ×0.93) y el top-k=4
(×0.50): 2.87 × 0.97 × 0.93 × 0.50 ≈ **1.29 GB/token** (~34× el objetivo). La tabla
"Gap restante" usa el valor redondeado ~1.36 GB/tok (36×) para la combinación. El 235B,
por su escala (working set 57.5 GB > 44 GB), no alcanza el objetivo con ninguna
combinación de técnicas sin entrenamiento.

## El límite fundamental identificado

> **La relación working-set/model-size es constante (~40%) en la arquitectura Qwen3-MoE.
> El tráfico mínimo de un modelo = cold miss + reutilización residual, ambos ∝ tamaño.
> El objetivo de 37.5 MB/token es alcanzable SOLO con modelos cuyo working set cabe en
> la jerarquía (VRAM+RAM ≤ 44 GB): el 30B lo demuestra (13-17 MB/token). El trade-off
> es la CALIDAD: no existe (en los modelos evaluados) un modelo de frontera con working
> set pequeño. La frontera calidad/working-set es el problema abierto.**

## Gap restante por técnica (2.87 → 37.5 MB/token)

| Técnica (235B) | Tráfico | Factor restante |
|---|---|---|
| Baseline page cache | 2.87 GB/tok | 77× |
| + sparsity (H-007, ~4.5%) | 2.78 GB/tok | 74× |
| + compresión lossless (H-008, ~5%) | 2.73 GB/tok | 73× |
| + top-k=4 (H-011) | 1.44 GB/tok | 38× |
| Combinación (k=4 + sparsity + lossless) | ~1.36 GB/tok | 36× |
| **Modelo que cabe (30B, H-009)** | **13.3 MB/tok** | **0.35× (BAJO objetivo)** |

## Veredictos NO TESTEABLES en el ciclo

- **SeedLM (H-008, con retrain)**: requiere optimización de semillas → experimento
  futuro: optimizar semillas sobre una muestra de expertos y medir calidad+tráfico.
- **Arquitectura frontera con working set pequeño (H-009)**: requiere modelos nuevos →
  futuro: evaluar un MoE fine-grained ~100B si la literatura lo justifica.
- **Sparsity de activaciones dinámica (H-007b)**: requiere instrumentar el forward →
  futuro: hook en el gate del fork para medir la fracción activa por token.

---

# AUTO AUDITORÍA (protocolo del ciclo 3)

1. **¿Todos los números son reproducibles?** SÍ — scripts CONSERVADOS en
   experiments/E007/: weight_analysis.py (H-007/H-008, v3 verificado),
   layout_analysis.py (H-010), topk_simulation.py (H-011); simuladores del ciclo 2
   (cache_simulator.py para H-009) verificados idénticos en re-ejecución.
2. **¿Los scripts vuelven a producir los resultados?** Los comandos de cada discovery
   son re-ejecutables (dequantización validada con control token_embd).
3. **¿Unidades correctas?** Revisado: MB/GB decimal consistentes; el 0008 CORRIGIÓ el
   peso del experto (12.24 MB — down Q6_K 5.16 + gate/up Q4 3.54) que el ciclo 2
   asumía 11.42; el 0010 usa 12.24. MiB/s de fio (ciclo 1) etiquetado. No se mezclan
   MB decimal con MiB en los cálculos de tráfico (todos decimales).
4. **¿Bytes lógicos vs físicos?** Distinguidos en 0008 (H-010): tráfico lógico =
   bytes únicos + relecturas; físico = lógico (sin desperdicio de páginas).
5. **¿FLOPs reducidos ≠ I/O reducido?** Distinguido en 0006 (H-007): el skipping de
   filas muertas reduce BYTES (se leen menos filas); los FLOPs del down (50% ceros
   dispersos) NO reducen bytes — explícito.
6. **¿Capacidad de almacenamiento ≠ tráfico/token?** Distinguido en 0007 (H-008):
   "no basta que el archivo sea más pequeño" — se respondió cuántos bytes abandonan
   el NVMe por token (lossless 2-12% en capas densas, corregido).
7. **¿Calidad separada de rendimiento?** Separadas en 0009 (H-011): velocidad (17→26
   t/s) vs calidad (k=2 incoherente) — la mejora de velocidad con k=4 NO se declaró
   como éxito de tráfico (la reducción de tráfico es aparte y medible).
8. **¿Claims de novedad sin evidencia?** Ningún claim de novedad: todos los resultados
   se presentan como "resultado observado en este estudio; novedad no establecida"
   (la sparsity de pesos del 36.5% en Qwen3 — no se verificó prior-art específico
   para esto; se documenta sin claim).
9. **¿Conclusiones sobre suposiciones no medidas?** La calidad de H-011 es
   cualitativa (30B, misma arquitectura) — marcada como Media-Alta confianza, no como
   demostración formal. La sparsity dinámica (H-007b) NO se midió — marcada como
   pendiente, no como resultado.
10. **¿Alguna inconsistencia corregida?** SÍ: (a) el peso por experto 11.42→12.24 MB
    (down Q6_K, 0008); (b) el experto 127 del ffn_up_exps tiene ~70.9% de ceros y ~67% de filas totalmente
    cero (casi muerto, NO 100% — la medición inicial con offset mal alineado daba
    100%; corregido a 70.9% con la matriz completa); (c) los "NaN del down" reportados inicialmente eran un artefacto de dequantizar
    Q6_K como Q4_K (el down es Q6_K) — corregido; el codebook (conservado en
    codebook_analysis.py) confirma que los Q4 no son comprimibles con pérdida
    aceptable (0.96× a 5 bits).

## Contrato de verificación (para el auditor)

- Cada experimento: experiments/E007/ (scripts) + discoveries 0006-0010 (resultados).
- Datos crudos: traces del ciclo 2 (E006/traces/), pesos del GGUF (shard 1).
- Reproducibilidad: weight_analysis.py, comandos con --override-kv, cache_simulator.py.
- Límites teóricos: entropía (0007), working set (0010), invarianza LRU (0008).
- Falsaciones: escritas ANTES en limit-models.md, evaluadas en cada discovery.
- No se implementaron soluciones complejas tras su techo teórico: el skipping de
  filas (H-007) y el reordenamiento (H-010) NO se implementaron (su techo ya
  cuantificado no alcanza el objetivo; se documentaron como mejoras parciales).
