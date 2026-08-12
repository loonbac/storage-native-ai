# Hipótesis refutadas

Formato obligatorio del protocolo de corrección:

```text
H-XXX — <enunciado>
  Estado: REFUTADO
  Razón: <qué supuesto falló exactamente>
  Experimento: <qué se hizo>
  Evidencia: <dónde está la evidencia>
  Fecha:
```

**Regla**: una hipótesis refutada indica EXACTAMENTE qué se refutó. Nunca saltar de
"esta estrategia falla" a "el proyecto es imposible". El conocimiento refutado se conserva
aquí permanentemente y puede revisitarse si cambian las condiciones.

## Refutadas

### R-001 — Predicción P-E2-1 (E002 -ngl 0): 1.5–3.5 t/s

**Estado: REFUTADO**
Razón: la predicción asumió el cuello en CPU/BW-RAM; el cuello real es el NVMe saturado.
El modelo revisado (t/s = BW_NVMe ÷ tráfico_medido) predice exactamente 0.4 t/s.
Experimento: E002a (Qwen3-235B, -ngl 0, 64 tokens).
Evidencia: `experiments/E002/logs/run-ngl0-20260811-133210.log` (+.io), descubrimiento 0003.
Fecha: 2026-08-11

### R-002 — Predicción P-E2-2: I/O bajo tras warmup (< 200 MB/s)

**Estado: REFUTADO**
Razón: el page cache (32 GB) no retiene un modelo de 142 GB → thrashing → NVMe saturado
(~1093 MiB/s sostenido) durante toda la generación.
Experimento: E002a, muestreo /proc/diskstats.
Evidencia: `experiments/E002/logs/run-ngl0-20260811-133210.log.io`.
Fecha: 2026-08-11

### R-003 — Predicción P-E2-3: offload parcial (ngl 4) mejora a 3–12 t/s

**Estado: REFUTADO**
Razón: llama.cpp estándar no implementa caché de expertos; -ngl mueve layers enteros,
pero los expertos (95% del peso) siguen en NVMe→CPU → rendimiento invariante (0.4 t/s).
Experimento: E002b.
Evidencia: `experiments/E002/logs/run-ngl4-20260811-134541.log` (+.io, .vram).
Fecha: 2026-08-11

### R-004 — Utilidad del offload -ngl parcial para MoE en llama.cpp estándar

**Estado: REFUTADO** (para este caso)
Razón: -ngl 4 usó 6.3 GB de VRAM sin cambiar el rendimiento; el cuello (NVMe) no se
toca porque los expertos no tienen caché propia.
Experimento: E002b.
Evidencia: `experiments/E002/logs/run-ngl4-20260811-134541.log.vram` (pico 6353 MiB).
Fecha: 2026-08-11

### R-005 — H-006: la caché de expertos alcanza ≤37.5 MB/token

**Estado: REFUTADO** (con el techo teórico, no con una implementación)
Razón: el Oracle Cache (Belady MIN — límite matemático de toda política) da 933 MB/token
con 44 GB y 4139 MB/token con 12 GB en Qwen3-235B (25× y 110× el objetivo). La
propiedad limitante: working set de reutilización de ~54 GB (ventana 32 tokens) supera
la caché disponible; distribución de frecuencias plana; cold misses de 134.2 GB.
Experimento: E006.1+E006.2+E006.4 (cache_simulator.py sobre traces reales de 1198 tokens).
Evidencia: `experiments/E006/results.md`, discoveries/0005, falsification-002.md.
Fecha: 2026-08-11

### R-006 — Supuesto del ciclo 1: la locality de Qwen3-235B es una ley de potencia (pocos expertos calientes)

**Estado: REFUTADO**
Razón: la distribución de frecuencias es plana: top-10% de expertos cubren 14.5-19%,
top-25% 35-42% (una ley de potencia daría >80%). La locality es temporal (reuse
P50=2 tokens) pero sin concentración fuerte.
Experimento: E006.3 (analyze_locality.py sobre traces de 30B y 235B).
Evidencia: discoveries/0004, experiments/E006/traces/.
Fecha: 2026-08-11

### R-007 — H-008: compresión de pesos alcanza el objetivo sin entrenamiento

**Estado: REFUTADO** (límite de información medido)
Razón: lossless máx 2-12% en capas densas (entropía ~3.9 bits/valor de los Q4; la capa
0 esparsa da 28% — no representativa); sin estructura low-rank en filas vivas (99%
energía en 93%); SeedLM (4-8×) requiere retrain.
Experimento: E007 (entropía + SVD sobre pesos reales del 235B).
Evidencia: discoveries/0007, experiments/E007/.
Fecha: 2026-08-11

### R-008 — H-010: el reordenamiento físico reduce bytes NVMe

**Estado: REFUTADO** (invarianza matemática + layout real)
Razón: el LRU del kernel por página de 4KB es independiente del layout (frecuencia de
acceso por página invariante); sin desperdicio de páginas (reads de 3.5-5MB completos);
el reordenamiento solo cambia latencia, no bytes/token.
Experimento: E007 (offsets reales del GGUF + patrón de acceso).
Evidencia: discoveries/0008, experiments/E007/.
Fecha: 2026-08-11

### R-009 — H-007: la sparsity de pesos del modelo permite reducir los bytes

**Estado: REFUTADO** (medición por capa del shard 1)
Razón: la sparsity media de pesos es 4.53% (capa 0: 36.49% anomalía; capas 5-18:
0.44-2.68%) → reducción de bytes del FFN ~3%. El claim inicial "36.5% del modelo"
extrapolaba la capa 0.
Experimento: E007 (weight_analysis.py v3, dequantización Q4_K validada con token_embd).
Evidencia: discoveries/0006, experiments/E007/weight_analysis.py.
Fecha: 2026-08-11
