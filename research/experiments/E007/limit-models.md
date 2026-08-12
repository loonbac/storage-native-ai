# Modelos de límite — H-007..H-011 (Ciclo 3, task-2)

Fecha: 2026-08-11. Contexto numérico consolidado:
- Baseline E002: **2.87 GB/token** (page-cache-only, 32 GB RAM), ~0.4 t/s.
- Brutos: 8.6 GB/token (752 activaciones × 11.42 MB/experto). Únicos/token: 1.41 GB.
- Cold miss: 134.2 GB de expertos / N tokens (~110 MB/token a 1198 tokens).
- Objetivo informativo: 37.5 MB/token. Caché+page cache (ciclo 2): ~0.95 GB/token.
- No-expertos: 4.84 GB (resueltos por page cache) — el problema es 100% expertos.

Las 10 preguntas del protocolo por hipótesis. **Condiciones de falsación escritas
ANTES de cualquier experimento.**

---

## H-007 — Sparsity de activación/pesos

1. **Tráfico mínimo teórico si fuera perfecta**: el FFN de cada experto es gated
   (W1: gate, W2/W3: up/down). Para saltar columnas de W2/W3 hace falta computar el
   gate (leer W1 siempre). Tráfico por experto = (1 + 2·f)/3 × 11.42 MB, con f =
   fracción de neuronas del gate ACTIVAS. Con f=1 (sin sparsity): 11.42 MB (baseline).
   Con f=0.5: 7.6 MB. Con f=0.1 (sparsity ReLU real): 4.6 MB.
2. **Parte de 2.87 GB/token eliminable**: 0% si f≈1 (SiLU sin sparsity); ~20-33% si
   f≈0.5-0.7 (SiLU real, sin retrain); hasta 60% con ReLU-sparse (requiere retrain).
3. **Límite físico restante**: con sparsity SiLU sin retrain: 1.9-2.3 GB/token — lejos
   del objetivo (50-60×). Con retrain (fuera de scope): ~1.1 GB/token brutos; con
   caché combinada ~0.4-0.6 GB/token.
4. **Supuestos**: (a) las neuronas del gate tienen outputs ≈ 0 con frecuencia; (b) el
   skipping por umbral no degrada la calidad; (c) el esquema de lectura por columnas
   es físicamente posible (layout columnar).
5. **¿Entrenamiento?** Para sparsity REAL (ReLU, ~95%) SÍ (TurboSparse-style). Para
   sparsity SiLU natural: NO, se mide.
6. **¿Modifica el modelo?** No (solo lectura selectiva) si la sparsity es natural.
7. **¿Modifica llama.cpp?** Sí (lectura selectiva de columnas del FFN + hook de
   activaciones para medir f).
8. **¿Medible localmente?** Sí: la sparsity de PESOS se mide del GGUF (fracción de
   elementos ≈ 0, magnitudes); la sparsity de ACTIVACIONES requiere un forward
   instrumentado (fork).
9. **Experimento mínimo**: (a) análisis de magnitudes/ceros de los pesos de expertos
   (GGUF); (b) si el análisis de pesos no decide: instrumentar el gate en el fork y
   medir f sobre 100-200 tokens.
10. **Condición de falsación (escrita ANTES)**: si f (fracción activa del gate) > 0.8
    con un umbral que no degrade → la reducción es <15% → H-007 REFUTADA para el
    objetivo (sin retrain). Si f ≤ 0.6 → PARCIAL (reducción ~27% medible, no alcanza
    el objetivo → cerrar como PARCIAL con límite cuantificado).
    **Resultado que justificaría continuar**: f ≤ 0.4 (reducción >40%) + calidad
    aceptable → vale la pena el esquema de lectura selectiva.

---

## H-008 — Regeneración/representación compacta de pesos

1. **Tráfico mínimo teórico**: compresión lossy de los pesos Q4 de expertos.
   Límites por método (sobre 11.42 MB/experto Q4):
   - Sin pérdida (entropía de 4-bit): ~4.8 bits/valor ≈ 11.4 MB (≈0%).
   - Con pérdida ligera (3-bit / SVD r<full / codebook): 2-3× (3.8-5.7 MB/experto).
   - SeedLM-style (semilla + residuo, requiere retrain): 4-8× (1.4-2.9 MB/experto).
2. **Parte de 2.87 GB/token eliminable**: sin retrain: 2.87 → 1.0-1.4 GB/token
   (2-3×, combinable con caché → ~0.3-0.5 GB/token); con retrain: hasta 4-8×
   (0.36-0.72 GB/token, ~0.1-0.2 con caché).
3. **Límite físico restante**: incluso con 8×: 0.36 GB/token ≈ 10× el objetivo — la
   compresión sola NO alcanza 37.5 MB/token; combinada con otras (sparsity k-óptimo)
   podría acercarse pero no está demostrado.
4. **Supuestos**: los pesos Q4 tienen estructura (bajo rango, colas de valores
   singulares) explotable SIN retrain; la pérdida de calidad por la aproximación es
   aceptable.
5. **¿Entrenamiento?** SeedLM SÍ (selección de semillas optimizada). SVD/codebook
   genérico: NO (pero la calidad de la aproximación genérica suele ser peor).
6. **¿Modifica el modelo?** Sí (aproximación con pérdida — cambia los pesos).
7. **¿Modifica llama.cpp?** Sí (descompresión en runtime — costo de cómputo extra).
8. **¿Medible localmente?** Sí: SVD, entropía, codebook k-means sobre una muestra de
   expertos (barato, sin retrain).
9. **Experimento mínimo**: SVD de las matrices W1/W2/W3 de una muestra de expertos
   (espectro de valores singulares → rango efectivo) + entropía de los valores Q4 +
   codebook k-means (bins) → límite de bytes/experto alcanzable con pérdida
   cuantificable (error de reconstrucción relativo).
10. **Condición de falsación (escrita ANTES)**: si el rango efectivo de W1/W2/W3 es
    >70% del rango total (los valores singulares no decaen) → el low-rank no da
    >1.4× sin pérdida grande → H-008 REFUTADA sin retrain. Si el error de
    reconstrucción con 2× de compresión supera el 5% RMS → la pérdida es inaceptable
    → PARCIAL (solo con retrain, NO TESTEABLE en el ciclo).
    **Resultado que justificaría continuar**: rango efectivo ≤50% con error <2% RMS
    → la representación compacta es viable y el límite (1.4-1.9 GB/token) se mide.

---

## H-009 — Arquitecturas con menor working set

1. **Tráfico mínimo teórico**: con caché ≥ working set del modelo: tráfico = cold
   miss = tamaño_expertos/N. El Qwen3-30B-A3B (working set W=32 ≈ 7 GB, expertos
   17.9 GB) cabe en 44 GB → tráfico ≈ cold ≈ 13.3 MB/token (ya medido, ciclo 2:
   simulador 44GB → 13.3 MB/token — ¡bajo el objetivo!).
2. **Parte de 2.87 GB/token eliminable**: el 235B no cabe (working set 54 GB > 44 GB).
   Un modelo con working set ≤ 44 GB alcanza el objetivo de TRÁFICO — la cuestión es
   la CALIDAD (el 30B no es "frontera").
3. **Límite físico restante**: la relación working-set/model-size es CONSTANTE (~38%
   para Qwen3-MoE, 30B y 235B medidos) → el working set escala con el modelo. Para
   calidad de frontera con working set pequeño se necesita una arquitectura distinta
   (no testeable sin modelos nuevos).
4. **Supuestos**: los datos del 30B son representativos de la familia (ya validado:
   las métricas relativas son casi idénticas 30B vs 235B).
5. **¿Entrenamiento?** No aplica (análisis comparativo).
6. **¿Modifica el modelo?** No.
7. **¿Modifica llama.cpp?** No.
8. **¿Medible localmente?** Sí, con datos EXISTENTES (traces del 30B y 235B del ciclo 2).
9. **Experimento mínimo**: tabla comparativa 30B vs 235B: working set/token y /ventana,
   bytes únicos/token, working-set/model-size, working-set/VRAM, tráfico teórico
   mínimo (simulador a 44 GB) — todo con datos ya capturados.
10. **Condición de falsación (escrita ANTES)**: si la relación working-set/model-size
    NO es constante entre 30B y 235B (difiere >20% relativo) → la propiedad es
    específica del 235B, no de la arquitectura (H-009 gana valor). Si ES constante →
    la propiedad es de escala: H-009 se cierra como PARCIAL ("el tráfico se resuelve
    con escala menor; la calidad es el trade-off") — no justifica descargas nuevas.
    **Resultado que justificaría continuar**: encontrar un modelo con working-set
    significativamente sub-lineal en tamaño → requeriría descargas (justificado solo
    si la literatura sugiere uno con calidad de frontera).

---

## H-010 — Movimiento de datos / coste físico de acceso

1. **Tráfico mínimo teórico**: el reordenamiento físico NO reduce bytes lógicos (los
   expertos se leen igual); reduce (a) el desperdicio de páginas (bytes físicos
   leídos ≠ bytes lógicos: al leer un experto fragmentado se traen páginas enteras de
   4 KB con datos no usados) y (b) las relecturas por thrashing del page cache
   (agrupar calientes mejora el hit rate LRU real). Límite: acercar el page cache real
   al LRU ideal del simulador → **2.87 → ~0.95-1.5 GB/token** (1.9-3×).
2. **Parte de 2.87 GB/token eliminable**: ~1.4-1.9 GB/token (el gap entre page cache
   real 78% y LRU ideal 44 GB).
3. **Límite físico restante**: ~0.95 GB/token (el techo del simulador a 44 GB) —
   25× el objetivo. No alcanza; es la mejora "gratis".
4. **Supuestos**: el desperdicio de páginas es significativo (acceso fragmentado) y/o
   el LRU real del kernel se puede mejorar reordenando (experimento de simulación).
5. **¿Entrenamiento?** No.
6. **¿Modifica el modelo?** No (solo el layout físico del archivo).
7. **¿Modifica llama.cpp?** No (el acceso es por índice; reordenar = reescribir el
   GGUF con los expertos en otro orden, actualizando índices).
8. **¿Medible localmente?** Sí: offsets de los tensores del GGUF + simulación del
   patrón de acceso físico (páginas tocadas por token, desperdicio) + simulación de
   reordenamiento (frecuencia/co-ocurrencia/capa) con los traces.
9. **Experimento mínimo**: (a) mapear los offsets de los 12,032 expertos en el GGUF
   (ya disponible en el reader); (b) con los traces, simular las páginas leídas por
   token (layout actual vs reordenado) → desperdicio y hit rate de page cache
   simulada; (c) estimar el tráfico físico por token en ambos layouts.
10. **Condición de falsación (escrita ANTES)**: si el desperdicio de páginas es <5%
    Y el hit rate de page cache simulada no mejora >10% con el mejor reordenamiento →
    el layout físico no es explotable → H-010 REFUTADA (el coste físico ≈ coste
    lógico; no hay mejora medible). Si mejora >10% → PARCIAL: cuantificar el límite
    (~0.95-1.5 GB/token) y cerrar (no alcanza el objetivo).
    **Resultado que justificaría continuar**: mejora >30% (2.87 → <2.0 GB/token) →
    implementar el reordenamiento real (reescribir GGUF) como mejora práctica.

---

## H-011 — Reducción del número de expertos necesarios

1. **Tráfico mínimo teórico**: k reducido elimina (8-k)/8 de las activaciones →
   2.87 GB/token × (k/8) con page cache (escala lineal): k=6 → 2.15; k=4 → 1.44;
   k=2 → 0.72; k=1 → 0.36 GB/token. El objetivo 37.5 MB requiere k≈0.1 (imposible).
2. **Parte de 2.87 GB/token eliminable**: 25% (k=6), 50% (k=4) — con impacto en
   calidad creciente.
3. **Límite físico restante**: ~0.36 GB/token (k=1, calidad probablemente destruida)
   — la reducción del top-k SOLA no alcanza el objetivo.
4. **Supuestos**: los expertos 7-8 del top-8 contribuyen poco (pesos bajos del
   routing) → su omisión degrada poco; el routing sin retrain es aproximable.
5. **¿Entrenamiento?** No para k reducido directo (solo se omiten expertos).
6. **¿Modifica el modelo?** Sí, en inferencia (top-k efectivo menor — cambia la salida).
7. **¿Modifica llama.cpp?** Sí (override de n_expert_used o patch del top-k).
8. **¿Medible localmente?** Sí: simulación con traces (bytes eliminados por k) +
   calidad con el fork (k configurable, comparar salidas vs baseline k=8).
9. **Experimento mínimo**: (a) simulación: para k=6,4,2 sobre los traces → bytes
   eliminados reales; (b) calidad: fork con k reducido, generar N tokens con el mismo
   prompt, comparar (divergencia de salida, coherencia) vs k=8.
10. **Condición de falsación (escrita ANTES)**: si con k=6 la salida diverge
    significativamente (incoherencia o cambio semántico del texto) → incluso 25% de
    reducción es inaceptable → H-011 REFUTADA sin retrain. Si k=6 es aceptable pero
    k=4 no → PARCIAL: la reducción máxima con calidad aceptable es ~25-50% (1.4-2.15
    GB/token), lejos del objetivo → cerrar.
    **Resultado que justificaría continuar**: k=4 con calidad indistinguible → 50%
    de reducción → combinable con H-008/H-010 hacia ~0.5 GB/token (aún no el objetivo).

---

# Priorización (poder de falsación × potencial × coste)

| # | Hipótesis | Potencial (2.87→) | Coste | Poder de falsación | Justificación |
|---|---|---|---|---|---|
| 1 | **H-008** (compresión) | 2-8× (→1.0-1.4 GB) | BAJO (SVD/entropía del GGUF) | ALTO (rango efectivo decide) | Experimento barato que falsa/confirma el límite de bytes/experto; alto potencial |
| 2 | **H-010** (layout físico) | 1.9-3× (→0.95-1.5 GB) | BAJO (offsets + simulación) | ALTO (desperdicio de páginas decide) | Mejora "gratis" medible; decide si el coste físico es reducible |
| 3 | **H-007** (sparsity) | 1.2-1.5× sin retrain | MEDIO (hook en fork) | ALTO (fracción activa decide) | El análisis de pesos (parte de H-008) ya pre-falsa la sparsity de pesos; la de activaciones requiere instrumentación |
| 4 | **H-011** (k reducido) | 1.3-4× (→0.7-2.15 GB) | MEDIO (simulación + fork) | MEDIO-ALTO (calidad decide) | La calidad es el criterio; el límite teórico ya sugiere no alcanzar el objetivo |
| 5 | **H-009** (working set) | el objetivo de TRÁFICO (30B: 13.3 MB/token) | MUY BAJO (datos existentes) | MEDIO (constancia de la relación) | Conclusión metodológica; no justifica descargas salvo hallazgo sub-lineal |

**Orden de ejecución**: H-008 → H-010 (análisis del mismo GGUF, baratos, deciden rápido)
→ H-007 (si el análisis de pesos no la pre-falsó) → H-011 → H-009 (comparativa final).

**Regla del protocolo respetada**: si el análisis de pesos de H-008 muestra que no hay
estructura (rango alto, entropía alta), eso también pre-falsa la sparsity de pesos de
H-007 (mismos datos) — una prueba barata falsa dos hipótesis.
