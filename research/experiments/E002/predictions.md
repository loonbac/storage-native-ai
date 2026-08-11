# E002 — Predicciones (antes del experimento)

Documento de predicciones falsables. Se marcan como CONFIRMADA o REFUTADA tras la
medición, con evidencia. (Protocolo del proyecto: predicción → experimento → medición →
análisis → actualización.)

## Contexto numérico (bottleneck-analysis.md)

- Qwen3-235B Q4: 142 GB. Activos/token: 22B ≈ 12.3 GB (sin reutilización).
- Techo NVMe: 37.5 MB/token @ 40 tok/s. Techo RAM: 1.125 GB/token @ 40 tok/s.
- CPU Ryzen 7 5700X: ~8 cores útiles para llama.cpp CPU backend.
- Referencia: 7B denso Q4 genera 68.8 t/s en GPU (E001) — es el punto de comparación.

## Predicciones

### P-E2-1 — Tokens/s de E002a (-ngl 0, todo CPU)
**Predicción:** 1.5–3.5 t/s.
Razonamiento: el cuello será el cómputo CPU + BW de RAM. El 5700X procesa ~22B
parámetros Q4 activos por token; referencia empírica de llama.cpp CPU: 7B denso ~5-8 t/s
en 8 hilos → escalando a 22B activos (MoE, solo FFN activo): ~2-4 t/s. El BW RAM
(37 GB/s) sostiene 12.3 GB/token a ~3 t/s = 37 GB/s → consistente: ~2.5-3 t/s si el
tráfico es ~12.3 GB/token.

### P-E2-2 — I/O del NVMe durante E002a
**Predicción:** el I/O del NVMe durante generación será BAJO después del warmup
(< 200 MB/s), porque el mmap + page cache (32 GB RAM) retienen los pesos leídos; solo la
primera pasada lee del disco. El I/O de arranque (carga) será ~1.1-1.6 GB/s (techo NVMe).

### P-E2-3 — Tokens/s de E002b/c (parcial GPU)
**Predicción:** 3–8 t/s (E002b) y 5–12 t/s (E002c), limitados por el I/O de los expertos
no residentes + sincronización CPU-GPU. Si el tráfico de pesos desde RAM/NVMe por token
supera lo que el PCIe (26.7 GB/s) o la RAM (37 GB/s) pueden entregar, ese será el cuello.

### P-E2-4 — Locality (S4, la variable crítica)
**Predicción:** el tráfico de pesos por token medido (bytes leídos del NVMe+RAM por
token) será **menor que 12.3 GB/token** si hay reutilización de expertos, pero el valor
exacto es DESCONOCIDO. Si resulta h ≈ 0 (tráfico ≈ activos sin reutilización), H-003 se
debilitará seriamente para Qwen3-235B (P-007 ya advierte que no todos los MoE tienen
localidad).

### P-E2-5 — TTFT
**Predicción:** alto (10–90 s) por la carga inicial de 142 GB desde NVMe (1.5 GB/s →
~95 s teórico; con page cache parcial y lectura bajo demanda, menor). Medible con el
wall time del primer run.

## Criterios de falsificación

- P-E2-1 REFUTADA si tg < 1.0 o > 5.0 t/s (fuera del rango predicho).
- P-E2-2 REFUTADA si el I/O sostenido durante generación > 500 MB/s.
- P-E2-3 REFUTADA si E002c no es ≥ E002b (offload adicional sin beneficio).
- P-E2-4 REFUTADA si el tráfico/token medido ≈ 12.3 GB (sin locality).
- P-E2-5 REFUTADA si TTFT < 10 s o > 300 s.
