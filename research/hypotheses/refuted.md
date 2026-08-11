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
