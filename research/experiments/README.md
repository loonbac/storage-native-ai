# Experimentos

Un experimento por carpeta: `E001/`, `E002/`, ...

Requisitos de reproducibilidad (sección 29 del proyecto):

1. **config.md** — hardware, OS, drivers, versiones, modelo, cuantización, parámetros,
   comandos exactos.
2. **Código** o scripts usados (o registro de cómo reconstruirlos).
3. **Logs** crudos de la ejecución.
4. **Métricas** (tokens/s, TTFT, latencia/token, VRAM, RAM, almacenamiento, ancho de
   banda, cache hit/miss, prefetch accuracy, bytes/token, parámetros activos/token,
   energía/token si es posible, calidad).
5. **Análisis** — qué demuestra, qué NO demuestra, cuál es el siguiente experimento.
6. Cada benchmark debe poder ejecutarse nuevamente con los mismos comandos.

## Escalera experimental (guía inicial, modificable)

```text
E001 — baseline de inferencia convencional (modelo en VRAM)
E002 — modelo fuera de VRAM (streaming/offloading desde NVMe) — Nivel 0-1
E003 — SSD → RAM → VRAM (jerarquía explícita)
E004 — SSD → GPU (GPU Direct Storage / lectura directa)
E005 — prefetch predictivo
E006 — caché a nivel tensor/expert
E007 — MoE streaming con eviction selectiva
E008 — sparsity / compresión
E009 — combinaciones
...
```

## Índice

| ID | Título | Estado | Fecha |
|---|---|---|---|
| E001 | Baseline convencional en VRAM (Qwen2.5-7B Q4_K_M, 68.8 t/s) | 🟢 completado | 2026-08-11 |
| E002 | Modelo fuera de VRAM (Nivel 0-1): Qwen3-235B 142GB, 0.4 t/s, NVMe saturado | 🟢 completado | 2026-08-11 |
