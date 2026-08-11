# Conocimiento actual

Estado del conocimiento del proyecto a fecha de hoy. Es la fuente de verdad operativa;
los cambios históricos se conservan en `history/`.

## Afirmaciones con su estado y evidencia

### Hardware

1. **RTX 3060 12 GB (sm_86), 32 GB RAM, NVMe 238G** — 🟢 DEMOSTRADO (nvidia-smi, /proc/meminfo, lsblk). HECHO.
2. **NVMe secuencial 1.1–1.6 GB/s** (según jobs, bs=1M, direct) — 🟢 DEMOSTRADO (fio, descubrimiento 0001). RESULTADO EXPERIMENTAL.
3. **NVMe random 4K latencia media ~84 µs** — 🟢 DEMOSTRADO (fio, descubrimiento 0001). RESULTADO EXPERIMENTAL.
4. **Page cache RAM 32 GB multiplica random read ×8** — 🟢 DEMOSTRADO (fio direct=0, descubrimiento 0001). RESULTADO EXPERIMENTAL.

### Rendimiento de la cadena

5. **A 40 tok/s el presupuesto de pesos desde NVMe es ~28–39 MB/token (~56–78 M parámetros Q4)** — 🟢 DEMOSTRADO por aritmética simple sobre (2). INFERENCIA (deriva de hechos medidos).
6. **Qwen3-235B-A22B activa ~22B de 235B (~9.4%)** — 🟢 DEMOSTRADO (spec del modelo, verificable en config GGUF). RESULTADO DE LITERATURA.
7. **El gap entre parámetros activos/token actuales (miles de millones) y el presupuesto NVMe (~78 M) es ~2 órdenes de magnitud** — 🟢 DEMOSTRADO por aritmética (5)+(6). INFERENCIA.

### Toolchain

8. **PyTorch 2.13.0 + CUDA 13.3 + RTX 3060 funcionan** — 🟢 DEMOSTRADO (smoke test tensor GPU). RESULTADO EXPERIMENTAL.
9. **llama.cpp-cuda b10333 genera en GPU** — 🟢 DEMOSTRADO (Qwen2.5-0.5B: prompt 1550 t/s, gen 378.8 t/s). RESULTADO EXPERIMENTAL.

### PCIe / transferencias (descubrimiento 0002)

10. **H2D pinned ~26.7 GB/s** (CUDA events, 1/2/4 GB) — 🟢 DEMOSTRADO. RESULTADO EXPERIMENTAL.
11. **Latencia H2D fija ~50 µs; BW satura >19 GB/s a partir de ~16 MB por transferencia** — 🟢 DEMOSTRADO. RESULTADO EXPERIMENTAL.
12. **El tramo PCIe NO es el cuello de botella del streaming** (26.7 vs 1.5 GB/s del NVMe) — 🟢 DEMOSTRADO por comparación (INFERENCIA sobre hechos medidos).
13. **Reportes de link contradictorios** (nvidia-smi gen1×16, lspci gen4×4) — 🟠 DESCONOCIDO; se usa el dato empírico.

### Cuellos de botella (bottleneck-analysis.md)

14. **Presupuesto NVMe @40 tok/s: ~75 M params Q4/token** — 🟢 DEMOSTRADO (aritmética sobre 0001). INFERENCIA.
15. **Qwen3-235B Q4 demanda 12.3 GB/token sin reutilización; jerarquía completa entrega 10.16 GB/token → déficit 17%** — 🟢 DEMOSTRADO (aritmética). INFERENCIA.
16. **Locality h ≥ 0.2 hace factible 40 tok/s** — 🟢 DEMOSTRADO (aritmética, tabla 4.4). INFERENCIA. **La locality real de Qwen3-235B es 🟠 DESCONOCIDO — es LA variable crítica (S4).**
17. **Streaming naive (modelo completo por token) es inviable por construcción (×3500)** — 🟢 DEMOSTRADO (aritmética). NO implica imposibilidad del objetivo, solo de esa estrategia.

### E002 — Qwen3-235B desde NVMe (descubrimiento 0003)

18. **Nivel 0-1 demostrado: Qwen3-235B (142 GB, 11.8× VRAM) genera 0.4 t/s desde NVMe** — 🟢 DEMOSTRADO. RESULTADO EXPERIMENTAL.
19. **El NVMe estuvo saturado (~1093-1095 MiB/s) durante toda la generación → 100% I/O-bound** — 🟢 DEMOSTRADO. RESULTADO EXPERIMENTAL. H-001 CONFIRMADA.
20. **Tráfico real: 2.87 GB/token desde NVMe (5.1B params Q4), locality efectiva ~78% vía page cache** (vs 12.3 GB sin reutilización) — 🟢 DEMOSTRADO. RESULTADO EXPERIMENTAL. La locality de Qwen3-235B EXISTE (contrasta P-007).
21. **Modelo verificado exacto: t/s = BW_NVMe ÷ tráfico_por_token = 1.15/2.87 = 0.40** — 🟢 DEMOSTRADO. INFERENCIA verificada.
22. **-ngl parcial (llama.cpp estándar) no cambia el cuello para MoE: sin caché de expertos** — 🟢 DEMOSTRADO (ngl=4, 6.3GB VRAM, 0.4 t/s invariante). RESULTADO EXPERIMENTAL.
23. **Gap restante al North Star: reducir tráfico NVMe de 2.87 GB/token a ≤37.5 MB (factor ~76×)** — 🟢 DEMOSTRADO (aritmética). INFERENCIA. Sin límite físico que lo impida (BW combinado VRAM+RAM+PCIe sostiene 10.16 GB/token @40 t/s).

## Lo que NO sabemos todavía (incertidumbres críticas, ordenadas por valor informativo)

1. **¿La caché de expertos explícita en VRAM reduce el tráfico NVMe lo suficiente?** (H-006,
   E006) — la falsificación F-001 la señala como la siguiente prueba pendiente.
2. ¿Cuánto de la locality efectiva (78%) es locality de routing pura vs política LRU?
3. ¿Puede el runtime solapar I/O y cómputo sin degradar (S5)?
4. ¿Cuál es la calidad real de Qwen3-235B en Q4_K_M vs FP8/BF16 (S6)?
5. ¿GPU Direct Storage aporta algo útil en esta configuración (H2D ya a 26.7 GB/s)?
6. ¿El BW real de RAM en cargas mixtas (37 GB/s copy medido, 28 GB/s read) sostiene el
   tráfico de expertos entre RAM y CPU en paralelo con el NVMe?

## Ver también

- `bottleneck-analysis.md` — documento completo de cuellos de botella (task-4).
- `../hypotheses/active.md` — hipótesis en curso (H-001…H-006).
- `../hypotheses/falsification-001.md` — primera pasada de falsificación.
- `../hypotheses/refuted.md` — predicciones/estrategias refutadas (R-001…R-004).
- `../discoveries/` — descubrimientos 0001 (NVMe), 0002 (PCIe H2D), 0003 (Qwen3-235B offload).
- `history/` — evolución del conocimiento (protocolo de corrección).
