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
