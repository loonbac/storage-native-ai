# Hipótesis activas

Formato de cada hipótesis:

```text
H-XXX — <enunciado verificable>
  Estado: ACTIVA | PLAUSIBLE | REFUTADA (→ refuted.md) | CONFIRMADA (→ confirmed.md)
  Falsable por: <experimento que la destruiría>
  Prioridad: <crítica | alta | media | baja>
  Última evidencia: <fecha, experimento>
```

## H-001 — El NVMe (~1.1–1.6 GB/s) es el cuello de botella de primer orden

El streaming de pesos desde NVMe limita el rendimiento antes que la RAM o la VRAM para
modelos >> VRAM. Falsable por: un experimento que muestre que el rendimiento no escala con
el ancho de banda de almacenamiento cuando se varía la velocidad efectiva de lectura.
Prioridad: crítica.

## H-002 — La page cache de 32 GB RAM como caché intermedia multiplica el rendimiento

Los pesos leídos del NVMe quedan en page cache y los accesos repetidos (expertos
recurrentes, layers compartidos) no re-leen del disco. Falsable por: medir con `direct=1`
vs `direct=0` en la carga de un modelo > RAM y verificar que el rendimiento de la 2ª
pasada no mejora. Prioridad: alta.

## H-003 — Un modelo MoE con pocos expertos activos puede correr a velocidad útil con offloading

Estado: PARCIALMENTE CONFIRMADA (E002): corre (0.4 t/s desde NVMe, batch 1) pero no a
velocidad útil para el North Star con llama.cpp estándar. La locality efectiva ~78%
(2.87 GB/token vs 12.3 sin reutilización) muestra potencial; falta caché explícita.
Falsable por: un experimento que muestre que la caché de expertos no reduce el tráfico.
Prioridad: crítica.

## H-004 — Los pesos en Q4_K_M son el punto óptimo tamaño/calidad para este proyecto

~0.55 bytes/parámetro. Falsable por: evaluación de calidad (perplejidad/bench) que muestre
degradación inaceptable vs Q8/FP16 para los experimentos. Prioridad: media.

## H-005 — El gap fundamental del North Star es ~2 órdenes de magnitud en parámetros activos por token

Estado: REFINADA por E002. El gap medido es menor que el teórico (2.87 GB/token real vs
12.3 teórico sin reutilización) pero el requisito de 40 t/s sigue exigiendo reducir el
tráfico NVMe de 2.87 GB/token a ≤37.5 MB/token (factor ~76×). Cerrarlo exige caché de
expertos + sparsity + posiblemente regeneración de pesos o nueva arquitectura. Prioridad:
crítica (guía toda la investigación).

### H-006 — Una caché de expertos en VRAM reduce el tráfico NVMe por token por debajo de 2.87 GB

Estado: **REFUTADA** (falsification-002, discoveries/0005). El Oracle (techo teórico)
da 933 MB/token con 44 GB — 25× el objetivo de 37.5 MB/token. La caché SÍ mejora
lo práctico (~3×, a ~0.95 GB/token) pero no alcanza el objetivo. Falsada por:
working set de reutilización amplio (~54 GB en ventana de 32 tokens) + distribución
plana + cold misses. Movida a refuted.md.

## H-007 a H-011 — Nueva familia (ciclo 3)

> **Corrección de higiene (2026-08-11, task-1 del ciclo 3):** las definiciones de
> H-010 y H-011 del topic del ciclo 3 REEMPLAZAN las versiones del cierre del ciclo 2
> (que mapeaban H-010 = "contexto largo + caché ≥96GB" y H-011 = "caché real 3×").
> Las definiciones vigentes del ciclo 3 son:

| ID | Hipótesis (definición del ciclo 3) | Resumen |
|---|---|---|
| H-007 | Sparsity de activación/pesos real | Los pesos de los expertos activados tienen estructura interna que permite ejecutar solo una fracción sin degradar la salida — reduciendo bytes leídos, no solo FLOPs |
| H-008 | Regeneración/representación compacta de pesos | Representar los pesos de los expertos con mucha menos información que sus bytes Q4, reduciendo el tráfico NVMe ("store less, reconstruct locally") |
| H-009 | Arquitecturas con menor working set | Modelos/arquitecturas con menor working set efectivo logran mejor relación capacidad/VRAM/tráfico; distinguir propiedad de arquitectura vs del Qwen3-235B |
| H-010 | Reducción de movimiento de datos / jerarquía de memoria | Cambiar DÓNDE y CÓMO permanecen los pesos (page cache, RAM, VRAM, layout físico, agrupamiento, lectura secuencial) reduce el COSTE FÍSICO de acceso sin cambiar el número lógico de expertos |
| H-011 | Reducción del número de expertos físicamente necesarios | El routing tiene redundancia suficiente para evitar cargar/calcular algunos expertos (top-k alternativo, skipping, aproximación) sin degradar significativamente la calidad |

**Veredictos del ciclo 3 (2026-08-11, discoveries 0006-0010):**
- H-007 (sparsity pesos): REFUTADA (corregido) — sparsity media 4.53% (capa 0 anomalía 36.5%; capas medias <2.7%) → −3% bytes. Sparsity dinámica de activaciones (H-007b) NO TESTEABLE en el ciclo.
- H-008 (compresión): REFUTADA sin retrain (lossless 2-12% en capas densas; entropía 3.9 bits); SeedLM requiere retrain (NO TESTEABLE).
- H-009 (working set): PARCIAL — relación WS/model-size constante ~40% (propiedad de escala); el 30B alcanza 13.3 MB/tok @44GB (bajo objetivo); frontera calidad/WS es el problema abierto.
- H-010 (layout): REFUTADA — invarianza del LRU por página ante reordenamientos.
- H-011 (top-k): PARCIAL — k=4 da −50% (1.44 GB/tok) con calidad aceptable; k=2 incoherente.
Combinación máxima en el 235B (sin retrain): ~1.36 GB/tok (36× objetivo). La escala es el límite fundamental.
Prioridad (ciclo 3, por valor informativo): ver limit-models.md (task-2) — falsación × potencial × coste.

<!-- Se agregan hipótesis nuevas conforme avanza la investigación. Nunca se borran;
las refutadas pasan a refuted.md con evidencia. -->
