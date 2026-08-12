# Historial de conocimiento

Protocolo de corrección: el conocimiento anterior NUNCA se borra. Ante contradicción:

```text
CONOCIMIENTO ANTERIOR → CONTRADICCIÓN → ANÁLISIS DE EVIDENCIA
→ EXPERIMENTO SI ES NECESARIO → NUEVA CONCLUSIÓN
```

El conocimiento refutado se registra aquí como:

```text
Estado: REFUTADO
Razón:
Experimento:
Evidencia:
Fecha:
```

## 2026-08-11 — Fundación

- Estado inicial creado: `../current.md`.
- Primera corrección de especulación: "NVMe ≈ 2 GB/s" → "NVMe ≈ 1.1–1.6 GB/s medido"
  (descubrimiento 0001). La especulación queda registrada en el descubrimiento como
  "Estado previo del conocimiento".

## 2026-08-11 — Ciclo 1 completo (ledger + literatura + cuellos + E001 + E002 + falsificación)

- Supuesto corregido: "PCIe 4.0 x8 ≈ 12-14 GB/s" → "H2D medido ≈ 26.7 GB/s" (0002).
- Supuesto corregido: "NVMe ≈ 2 GB/s" → "1.1–1.6 GB/s" (0001).
- Predicciones P-E2-1/2/3 REFUTADAS (R-001…R-003) y sustituidas por modelo verificado:
  t/s = BW_NVMe ÷ tráfico_por_token (0.4 = 1.15/2.87, exacto).
- R-004: utilidad de -ngl parcial para MoE en llama.cpp estándar refutada.
- H-001 confirmada (NVMe = cuello de primer orden). H-003 parcial, H-005 refinada,
  H-006 generada (caché de expertos en VRAM, a falsar con E006).
- Conocimiento nuevo: locality efectiva de Qwen3-235B ≈ 78% bajo page cache
  (descubrimiento 0003); Nivel 0-1 demostrado (0.4 t/s, 11.8× VRAM).

## 2026-08-11 — Ciclo 2 (Explotación de localidad): H-006 REFUTADA

- Tracer de routing construido y validado (fork llama.cpp b10333, LLAMA_TRACE_MOE).
- Traces reales: Qwen3-30B (4 prompts × 300) y Qwen3-235B (2 prompts, 1198 tokens).
- 0004: locality Qwen3-MoE real, estable y MODERADA (no ley de potencia — R-006).
- 0005: Oracle Cache refuta H-006 para ≤37.5 MB/token (933 MB/token @44GB = techo).
- R-005: H-006 refutada con techo teórico, no con implementación fallida.
- Nueva familia H-007..H-011 (sparsity de activación como prioridad).
- Mejora práctica estimada de la caché real: ~3× (2.87 → 0.95 GB/token, ~1.2 t/s).

## 2026-08-11 — Ciclo 3 (raíz del tráfico): la ESCALA es el límite fundamental
> REGISTRO ORIGINAL (superado por la sección de CORRECCIÓN más abajo — las cifras
> "36.5%", "lossless ~30%" y "0.76 GB/tok" fueron refutadas por auditoría y corregidas).

- H-007 sparsity de pesos: 36.5% neuronas muertas (estructurada, sin retrain) → −24% (PARCIAL).
- H-008 compresión: lossless ~30% máx sin retrain (REFUTADA); SeedLM NO TESTEABLE.
- H-010 layout: invarianza LRU por página (REFUTADA); corrección peso experto 12.24 MB.
- H-011 top-k: k=4 −50% con calidad aceptable; k=2 incoherente (PARCIAL).
- H-009 working set: relación ~40% constante (escala); 30B alcanza 13.3 MB/tok (bajo objetivo).
- Límite fundamental: el tráfico mínimo ∝ tamaño del modelo; el objetivo se alcanza con
  modelos que caben en la jerarquía; la frontera calidad/working-set queda abierta.
- Combinación máxima en el 235B sin retrain: ~0.76 GB/tok (20× objetivo).
- Corregido: peso por experto (down Q6_K); experto 127 muerto (100% ceros); NaN del down.

## 2026-08-11 — CORRECCIÓN del ciclo 3 (auditoría independiente)

- H-007 CORREGIDO: la sparsity de pesos es dependiente de la capa — media del shard 1
  = 4.53% (capa 0: 36.5% anomalía; capas 5-18 <2.7%). El claim inicial "36.5% del
  modelo" extrapolaba la capa 0 → REFUTADA (reducción real ~3%).
- H-008 CORREGIDO: la entropía de las capas densas es ~3.9 bits (lossless 2-12%);
  el "2.68 bits" inicial era de la capa 0 esparsa (no representativa) → REFUTADA
  confirmada con el número correcto.
- weight_analysis.py v3 conservado y reproducible (reproduce 4.53%, 3.9 bits, control
  token_embd 0.25%).
- Combinación máxima 235B sin retrain: ~1.36 GB/tok (36× objetivo) — domina H-011 (k=4).
