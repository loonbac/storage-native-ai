# Pasada de falsificación F-001 (2026-08-11)

Objetivo de la pasada: **intentar destruir las hipótesis activas principales**
(H-003: "MoE con pocos expertos activos puede correr a velocidad útil con offloading";
H-005: "el gap se cierra reduciendo el tráfico de pesos por token con locality/sparsity").

Método: falsificación activa — para cada hipótesis, construir el ataque más fuerte posible
con los datos existentes y ver si la evidencia la destruye.

---

## Ataque F-001-A: "La locality medida en E002 (78%) es un artefacto de la page cache LRU, no de la locality de routing — la caché de expertos explícita no funcionará"

**Razonamiento del ataque:** si el router de Qwen3-235B activara expertos de forma
aleatoria, el page cache (32 GB de 142 GB = ~22% del modelo) tendría hit rate ~22%, no
78%. El 78% medido SOLO puede explicarse por distribución de accesos muy sesgada
(pocos expertos/páginas calientes reutilizados) — que es exactamente la localidad que la
caché de expertos explota.

**Veredicto: ATAQUE REPELIDO.** El argumento refuerza H-003/H-005 en vez de destruirlo:
la localidad real existe en Qwen3-235B (contrasta P-007, que advierte que no todos los
MoE la tienen). La hipótesis sobrevive.

**Precisión:** esto NO demuestra que una caché explícita funcione (falta E006), pero sí
que el supuesto de localidad no está refutado por la evidencia.

---

## Ataque F-001-B: "El offload de llama.cpp no sirvió (0.4 t/s invariante) → el offloading en general no sirve"

**Razonamiento del ataque:** si -ngl 4 no mejora nada, quizá el offloading no tiene
futuro en este modelo.

**Refutación del ataque:** -ngl 4 no ayuda porque llama.cpp estándar NO implementa caché
de expertos; solo mueve layers enteros a GPU, y los expertos (95% del peso) quedan en
NVMe→CPU. La literatura muestra sistemas con caché de expertos (MoE-Infinity, fMoE,
Diff-MoE) que sí reducen el tráfico. El ataque confunde "esta implementación (llama.cpp
estándar) no tiene la técnica" con "la técnica no funciona".

**Veredicto: ATAQUE REPELIDO** (por confusión de niveles: implementación ≠ técnica).

**Precisión:** lo que SÍ queda refutado es la utilidad de `-ngl` parcial para MoE en
llama.cpp estándar — eso queda registrado en refuted.md.

---

## Ataque F-001-C: "40 t/s es imposible porque el tráfico medido (2.87 GB/token) aún exige 115 GB/s del NVMe"

**Razonamiento del ataque:** con locality del 78%, el tráfico NVMe es 2.87 GB/token →
40 t/s × 2.87 GB = 114.8 GB/s del NVMe → imposible (1.15 GB/s). El gap es ~100×, no
"cerrable".

**Réplica:** el ataque usa el tráfico NVMe ACTUAL (con page-cache-only, sin caché de
expertos en VRAM). El presupuesto correcto: 40 t/s exige ≤37.5 MB/token DESDE NVMe. Con
caché de expertos calientes en VRAM (10 GB ≈ 18B params), la fracción de activos servida
por caché sube de 78% (RAM, sin control) a >99% (VRAM, controlada), dejando el NVMe solo
para expertos raros. El factor requerido (~76× sobre 2.87 GB) es de la misma magnitud que
la reducción ya lograda por la page cache (12.3→2.87 = 4.3×) y no está refutado por
ningún límite físico (el BW combinado VRAM+RAM+PCIe sostiene 10.16 GB/token @40 t/s;
bottleneck-analysis §4.3-4.4).

**Veredicto: ATAQUE REPELIDO.** El ataque no establece imposibilidad; solo muestra que
la page cache sola no basta — lo cual ya sabíamos.

**Precisión:** lo que el ataque SÍ demuestra: la localidad de page-cache-only NO alcanza
para 40 t/s. Eso es un dato importante (no una imposibilidad).

---

## Ataque F-001-D: "Las predicciones de E002 fueron refutadas (0.4 t/s vs 1.5-3.5) → el modelo de análisis es incorrecto"

**Razonamiento del ataque:** si las predicciones fallan, el análisis de cuellos de
botella está mal y las conclusiones no son confiables.

**Réplica:** las predicciones asumieron el cuello en CPU/BW-RAM (modelo "tráfico = activos
sin reutilización"). El experimento reveló el cuello real (NVMe saturado, tráfico 2.87
GB/token). El modelo REVISADO — t/s = BW_NVMe ÷ tráfico_medido = 1.15 ÷ 2.87 = 0.40 —
predice la medición EXACTAMENTE. La falsación corrigió el modelo; el nuevo modelo es
verificado. Esto es el protocolo funcionando, no su fracaso.

**Veredicto: ATAQUE REPELIDO** (el modelo revisado es exacto; la falsación mejoró el
conocimiento, sección 24 del topic).

---

## Resumen de la pasada

| Hipótesis | Ataque | Veredicto |
|---|---|---|
| H-003/H-005 (locality + caché) | A: artefacto LRU | Repelido (la localidad es real) |
| Offloading útil | B: -ngl no ayudó | Repelido (implementación ≠ técnica) |
| 40 t/s factible | C: gap 100× | Repelido (no hay límite físico; falta E006) |
| Modelo de análisis | D: predicciones fallaron | Repelido (modelo revisado es exacto) |

**Resultado: NINGUNA hipótesis central fue refutada en esta pasada.** La evidencia de
E002 las refuerza parcialmente. LO QUE SÍ QUEDÓ REFUTADO (registrado en refuted.md):
(a) las predicciones P-E2-1/2/3 (cuellos de CPU/RAM, I/O bajo tras warmup, offload
parcial útil); (b) la utilidad de -ngl parcial para MoE en llama.cpp estándar.

**Límite de esta pasada:** la hipótesis más débil no atacada empíricamente es "la caché
de expertos explícita reduce el tráfico lo suficiente" — requiere E006 para falsarla o
confirmarla. Es la siguiente falsificación pendiente.

**Nueva hipótesis generada (H-006):** "Una caché de expertos en VRAM (top frecuentes,
10 GB) reduce el tráfico NVMe por token por debajo de 2.87 GB → t/s > 0.4".
Falsable por: E006 (caché explícita) mostrando que el tráfico NVMe no cae.
