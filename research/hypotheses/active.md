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

## H-006 — Una caché de expertos en VRAM reduce el tráfico NVMe por token por debajo de 2.87 GB

Generada por falsificación F-001. Los expertos calientes (10 GB ≈ 18B params Q4) en
VRAM desplazan del NVMe la mayor parte de los ~2.87 GB/token actuales → t/s > 0.4.
Falsable por: E006 (caché explícita) que muestre que el tráfico NVMe por token no cae
significativamente o que la eviction destruye la calidad. Prioridad: alta.

<!-- Se agregan hipótesis nuevas conforme avanza la investigación. Nunca se borran;
las refutadas pasan a refuted.md con evidencia. -->
