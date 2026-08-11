# Hipótesis confirmadas

```text
H-XXX — <enunciado>
  Confirmada por: <experimento/evidencia>
  Evidencia: <referencia>
  Fecha:
```

## Confirmadas

### H-001 — El NVMe (~1.1–1.6 GB/s) es el cuello de botella de primer orden

**Confirmada por:** E002 (descubrimiento 0003). Durante toda la generación de
Qwen3-235B (142 GB) desde NVMe, el disco estuvo saturado a 1093–1095 MiB/s (~95-100%)
y la generación fue 100% I/O-bound: t/s = BW_NVMe ÷ tráfico_por_token = 1.15/2.87 = 0.4 t/s (exacto).

**Evidencia:** `experiments/E002/logs/*.log.io`, descubrimiento 0003.
**Fecha:** 2026-08-11

_(Nuevas confirmaciones se agregan aquí.)_
