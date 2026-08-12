# Descubrimiento 0005

## Hipótesis

H-006: una caché de expertos (con política óptima) puede reducir el tráfico NVMe/token
de Qwen3-235B hacia el objetivo de ≤37.5 MB/token.

## Motivación

Determinar el LÍMITE TEÓRICO (Oracle = Belady MIN) del tráfico alcanzable con caché de
expertos, ANTES de implementar una caché real (prioridad metodológica del ciclo 2:
medir → entender → falsificar → implementar).

## Estado previo del conocimiento

- E002 (0003): tráfico real 2.87 GB/token con page-cache-only (32GB RAM).
- 0004: locality Qwen3-MoE real pero moderada (~70% hit a W=32), distribución plana,
  working set amplio (ventana de 32 tokens ≈ 54 GB en el 235B).

## Estado del arte relacionado

- Belady MIN (1966): política de reemplazo óptima — techo de cualquier caché.
- MoE-Infinity, fMoE, Diff-MoE: cachés de expertos reales (≤ este techo).

## Experimento

E006.1+E006.2+E006.4: simulador offline (cache_simulator.py) sobre traces reales del
235B (p1 700 tokens + p2 499 tokens, prompts de razonamiento): políticas oracle
(Belady MIN, heap lazy), LRU (OrderedDict O(1)), LFU (heap lazy). Semántica por-token
(el runtime no evicta a mitad de token). Barrido de capacidades 2-96 GB.

## Configuración

Traces: experiments/E006/traces/235b-p1-*, 235b-p2-* (tracer validado, 0004).
Modelo: Qwen3-235B-A22B Q4_K_M, 94 capas, 128 expertos/capa, top-8, 11.42 MB/experto,
modelo de expertos total = 134.2 GB. Tokens: 1198 procesamientos.

## Resultado

| Capacidad | Oracle (MB/token) | hit% | LRU (MB/token) | hit% | LFU (MB/token) | hit% |
|---|---|---|---|---|---|---|
| 8 GB | 4914 | 42.8 | 5537 | 35.5 | 5596 | 34.8 |
| **12 GB (VRAM)** | **4139** | 51.8 | **4374** | 49.1 | 4742 | 44.8 |
| 20 GB | 2954 | 65.6 | 3062 | 64.3 | 3398 | 60.4 |
| 32 GB | 1716 | 80.0 | 1771 | 79.4 | 1961 | 77.2 |
| **44 GB (VRAM+RAM)** | **933** | 89.1 | **955** | 88.9 | 1074 | 87.5 |
| 64 GB | 338 | 96.1 | 342 | 96.0 | 399 | 95.4 |
| 96 GB | 110 | 98.7 | 110 | 98.7 | 112 | 98.7 |

**Objetivo: 37.5 MB/token. Referencias de capacidad: 12 GB = 1076 unidades; 44 GB = 3945.**

Descomposición del tráfico a 44 GB (1198 tokens): cold misses ≈ 110 MB/token (working
set leído una vez); reutilización residual ≈ 845 MB/token (misses de la caché). La
reutilización NO decrece con más tokens.

## Evidencia

cache_simulator.py (reproducible), traces crudos, salidas tabuladas. Validación:
curva monótona, oracle ≥ LRU ≥ LFU en todos los puntos, brecha oracle-LRU pequeña
(1-5%).

## Qué demuestra

1. **H-006 REFUTADA para el objetivo de ≤37.5 MB/token**: el límite teórico (Oracle)
   con 44 GB (VRAM+RAM reales) es **933 MB/token — 25× el objetivo**. Incluso con una
   caché de 96 GB (inexistente aquí), el techo es 110 MB/token — 3× el objetivo.
2. **La propiedad limitante es el working set de reutilización**: la ventana de ~32
   tokens del 235B necesita ~54 GB de caché (94 capas × ~50 expertos/capa × 11.42 MB).
   Con 44 GB disponibles, ~845 MB/token de activaciones no cubiertas por la caché.
   La distribución plana (0004: top-25% = 35%) impide seleccionar pocos expertos.
3. **El cold miss también cuenta**: 134.2 GB de expertos deben leerse al menos una vez;
   a 1198 tokens son ~110 MB/token. Solo con N ≥ ~3600 tokens (contexto largo) el cold
   baja de 37.5 MB/token — y aun así la reutilización residual lo impide (44 GB).
4. **La caché de expertos SÍ mejora el rendimiento práctico** (aunque no alcance el
   objetivo): con VRAM 12 GB + page cache 32 GB (44 GB efectivos), el tráfico estimado
   pasa de 2.87 GB/token (E002, page-cache-only) a ~0.95 GB/token → ~1.2 t/s estimados
   (vs 0.4 baseline): ~3×. Pero 12 GB SOLOS (4.4 GB/token) rinden PEOR que el page
   cache (2.87 GB/token): la caché de expertos SOLO aporta sobre el page cache.

## Qué NO demuestra

- No mide el tráfico con la caché real implementada (E006 no se ejecutó: el contrato
  exige no forzarlo si el Oracle refuta).
- No cubre prefetch imperfecto (E006.5: la ganancia máxima del prefetch = brecha
  oracle-LRU ≤ 5.5% — no cambia el veredicto).
- No evalúa sparsity de activación ni compresión (fuera del alcance del ciclo 2).
- Los números dependen del peso por experto (Q4_K_M); con Q8/F16 el tráfico escala.

## Conocimiento modificado

- **H-006: REFUTADA** (para el objetivo de 37.5 MB/token con capacidades ≤44 GB).
  El veredicto es del Oracle (límite teórico), no de una implementación fallida.
- **Nuevo conocimiento**: (a) el límite real de la caché de expertos en esta máquina es
  ~0.95 GB/token (44 GB efectivos); (b) la caché de expertos es complementaria al page
  cache, no sustituta; (c) el término dominante es la reutilización residual
  (845 MB/token), no el cold miss.
- La combinación page cache + caché de expertos: mejora práctica ~3× (0.4 → ~1.2 t/s),
  lejos del North Star pero un paso real.

## Estado

🟢 Demostrado (simulación sobre traces reales, política óptima incluida).

## Confianza

Alta (Oracle = techo matemático; simulador validado; traces reales del modelo ancla).

## Próxima hipótesis

El objetivo de 37.5 MB/token exige atacar el TÉRMINO DE REUTILIZACIÓN desde la raíz:
sparsity de activación (menos bytes únicos por token), compresión/regeneración de pesos
(menos bytes por experto leído), o arquitecturas con working set menor. Ver
"nueva familia de hipótesis" en falsification-002.

## Próximo experimento

Ciclo 3: evaluar un modelo con sparsity de activación real (TurboSparse-style) o la
regeneración de pesos (SeedLM-style) sobre el mismo trace, midiendo el tráfico mínimo
por token con la MISMA metodología.
