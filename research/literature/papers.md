# Papers

Encuesta de literatura (Modo A). Cada entrada: relevancia, hallazgo clave, estado de
conocimiento y relación con hipótesis del proyecto. Los estados reflejan el nivel de
verificación actual (abstracts + fuentes múltiples); pendiente de lectura completa de
textos donde se indica.

## Índice

| ID | Título | Año | Estado | Relevancia |
|---|---|---|---|---|
| P-001 | DeepSeek-V3 Technical Report | 2024 | 🟢 | Referencia del North Star |
| P-002 | FlexGen (single-GPU offloading) | 2023 | 🟢 | Offloading clásico |
| P-003 | PowerInfer-2 (smartphone >mem) | 2024 | 🟡 | 11.68 tok/s Mixtral 47B en teléfono |
| P-004 | Turbo Sparse (ReLU sparsity) | 2024 | 🟡 | Reducir parámetros activos |
| P-005 | MoE-Infinity (expert cache sparsity) | 2024 | 🟡 | Caché de expertos en máquina personal |
| P-006 | fMoE (fine-grained expert offload) | 2025 | 🟡 | Offloading MoE fino |
| P-007 | Not All Models Suit Expert Offloading | 2025 | 🟡 | Localidad de routing por modelo — **falsificador** |
| P-008 | Oracle-MoE (locality routing) | 2025 | 🟡 | Routing con localidad para memoria limitada |
| P-009 | ReMoE (router fine-tuning reuse) | 2025 | 🟡 | Aumentar reuse de expertos |
| P-010 | SeedLM (pesos desde PRNG) | 2024 | 🟡 | Regeneración de pesos — línea radical |
| P-011 | PagedAttention / vLLM | 2023 | 🟢 | Jerarquía de memoria en serving |
| P-012 | HiFC (KV cache a flash) | 2025 | 🟡 | KV offloading eficiente |
| P-013 | Tutti (SSD KV cache práctica) | 2025 | 🟡 | KV en SSD sin stalls |
| P-014 | ENDOR (formato sparse para offload) | 2024 | 🟡 | Formato de pesos hardware-friendly |
| P-015 | I/O for LLM Inference (survey, roofline) | 2026 | 🟡 | Marco de análisis cuellos de botella |
| P-016 | CHEOPS'25 IBM (I/O NVMe offload) | 2025 | 🟡 | Caracterización I/O NVMe |
| P-017 | PIM Is All You Need (CXL GPU-free) | 2025 | 🟡 | Alternativa sin GPU |
| P-018 | SpeedLoader (I/O heterogénea) | 2024 | 🟡 | Distribución+offloading |
| P-019 | HillInfer (SmartSSD KV eviction) | 2025 | 🟡 | Computational storage |
| P-020 | Neural weight compression | 2025 | 🟡 | Codecs aprendidos de pesos |
| P-021 | MoE-SpeQ (prefetch especulativo) | 2025 | 🟡 | Prefetch predictivo de expertos |
| P-022 | Diff-MoE (expert caching por prioridad) | 2025 | 🟡 | Caché diferencial de expertos |

## Detalle

### P-001 — DeepSeek-V3 Technical Report (DeepSeek-AI, 2024)
- URL: https://arxiv.org/abs/2412.19437
- Hallazgo clave: MoE 671B totales / 37B activos por token; MLA (Multi-head Latent
  Attention) + DeepSeekMoE; entrenado nativo en FP8; sin auxiliary loss para balance.
- Relevancia: referencia arquitectónica del North Star (DeepSeek-V4-Flash hereda esta
  familia). Confirma que la clase "MoE gigante, pocos activos" es la de frontera.
- Estado: 🟢 DEMOSTRADO (reporte técnico oficial, múltiples fuentes). RESULTADO DE LITERATURA.
- Relación: H-003, H-005.

### P-002 — FlexGen (Sheng et al., MLSys 2023)
- URL: https://arxiv.org/abs/2303.06865
- Hallazgo clave: offloading IO-eficiente (GPU/CPU/disco) para generación high-throughput
  en 1 GPU; OPT-175B en single GPU; batch efectivo grande vía policy de scheduling.
- Relevancia: demuestra Nivel 0-1 (modelo >> VRAM en 1 GPU commodity) hace 2 años.
- Estado: 🟢 DEMOSTRADO (paper + repo + paquete PyPI). RESULTADO DE LITERATURA.
- Relación: E002 (referencia de baseline), H-001.

### P-003 — PowerInfer-2 (Lyu et al., 2024)
- URL: https://arxiv.org/abs/2406.06282
- Hallazgo clave: descompone MatMul en "neuron clusters"; ejecución heterogénea
  CPU/NPU/GPU; Mixtral 47B a **11.68 tok/s en smartphone** (22× vs otros frameworks).
- Relevancia: prueba de que modelos >> memoria de cómputo corren a velocidad útil en
  hardware débil — valida la dirección del proyecto. La granularidad neuron-cluster es
  una idea clave para el runtime.
- Estado: 🟡 PLAUSIBLE (paper + web oficial; no verificado localmente). RESULTADO DE LITERATURA.
- Relación: H-001, H-005, E002.

### P-004 — Turbo Sparse (Song et al., 2024)
- URL: https://arxiv.org/abs/2406.05955
- Hallazgo clave: SwiGLU/GeGLU tienen sparsity de activación limitada; reemplazarlas por
  ReLU + entrenamiento adecuado produce sparsity REAL (95%+ de neuronas FFN inactivas)
  con SOTA quality.
- Relevancia: ataca directamente el gap de parámetros activos/token (H-005): si ~95% de
  las neuronas FFN no se activan, se pueden omitir del tráfico.
- Estado: 🟡 PLAUSIBLE. RESULTADO DE LITERATURA.
- Relación: H-005 (crítica), architecture/alternatives.

### P-005 — MoE-Infinity (Xue et al., 2024)
- URL: https://arxiv.org/abs/2401.14361
- Hallazgo clave: en batch=1, los modelos MoE reutilizan pocos expertos frecuentemente
  (activation sparsity); expert cache sparsity-aware con prefetch por layers.
- Relevancia: exactamente nuestro escenario (máquina personal, batch 1). Referencia
  directa para el caché de expertos de E002/E006.
- Estado: 🟡 PLAUSIBLE. RESULTADO DE LITERATURA.
- Relación: H-003, E006.

### P-006 — fMoE (Wang et al., 2025)
- URL: https://arxiv.org/abs/2502.05370
- Hallazgo clave: offloading fino de expertos (a nivel de parámetro/expert individual)
  en serving; reduce transferencias innecesarias.
- Estado: 🟡 PLAUSIBLE. RESULTADO DE LITERATURA.
- Relación: H-003, E006.

### P-007 — Not All Models Suit Expert Offloading (2025)
- URL: https://arxiv.org/html/2505.16056v1
- Hallazgo clave: la localidad de activación de expertos entre tokens consecutivos varía
  MUCHO entre modelos; algunos (p. ej. ciertos Qwen MoE) tienen routing poco local →
  el offloading+caché no les sirve.
- Relevancia: **falsificador potencial de H-003**. Hay que medir la localidad de routing
  de Qwen3-235B-A22B ANTES de apostar a caché de expertos.
- Estado: 🟡 PLAUSIBLE. RESULTADO DE LITERATURA.
- Relación: H-003 (falsifica), task-7 (falsificación), E002 (medir locality).

### P-008 — Oracle-MoE (Zhou et al., ICML 2025)
- URL: https://proceedings.mlr.press/v267/zhou25b.html
- Hallazgo clave: routers reales tienen poca localidad temporal; routing en "oracle
  space" preserva localidad → menor tráfico de expertos.
- Relevancia: idea de arquitectura para reducir transferencias (Modo B).
- Estado: 🟡 PLAUSIBLE. RESULTADO DE LITERATURA.
- Relación: H-005, architecture/alternatives.

### P-009 — ReMoE (2025)
- URL: https://arxiv.org/html/2605.27081
- Hallazgo clave: fine-tuning del router para aumentar reuse de expertos → menos
  evictions y menos I/O en memoria limitada.
- Relevancia: ataca el problema desde el entrenamiento/router, no solo el runtime.
- Estado: 🟡 PLAUSIBLE. RESULTADO DE LITERATURA.
- Relación: H-005, architecture/alternatives.

### P-010 — SeedLM (Kamat et al., ICLR 2025)
- URL: https://arxiv.org/abs/2410.10714
- Hallazgo clave: comprime bloques de pesos a semillas de un LFSR; en inferencia se
  REGENERA la matriz desde la semilla (compresión 4×+ con FP16 output).
- Relevancia: es la línea "weight regeneration" del proyecto, ya existente como
  compresión post-training. Nuestra idea de "pesos generados" es una VARIANTE de esto.
- Estado: 🟡 PLAUSIBLE. RESULTADO DE LITERATURA.
- Relación: H-005, architecture/alternatives (regeneración).

### P-011 — PagedAttention / vLLM (Kwon et al., SOSP 2023)
- URL: https://arxiv.org/abs/2309.06180
- Hallazgo clave: gestión tipo VM de páginas para KV cache; elimina fragmentación;
  24× throughput.
- Relevancia: paging como principio de gestión de memoria jerárquica; aplicable a pesos.
- Estado: 🟢 DEMOSTRADO (SOSP'23, producción amplia). RESULTADO DE LITERATURA.
- Relación: E006 (tensor paging).

### P-012 — HiFC (NeurIPS 2025)
- URL: https://proceedings.neurips.cc/paper_files/paper/2025/file/4431224d3762aa655f0aee4eaf04ff16-Paper-Conference.pdf
- Hallazgo clave: KV cache swapping a flash de alta eficiencia; framework flash-friendly.
- Estado: 🟡 PLAUSIBLE. RESULTADO DE LITERATURA.
- Relación: memoria jerárquica (KV), E0xx.

### P-013 — Tutti (2025)
- URL: https://arxiv.org/html/2605.03375
- Hallazgo clave: restauración de KV desde SSD sin GPU stalls; resuelve el problema de
  I/O pequeño/aleatoria del KV cache.
- Estado: 🟡 PLAUSIBLE. RESULTADO DE LITERATURA.
- Relación: memoria jerárquica.

### P-014 — ENDOR (Ren et al., 2024)
- URL: https://arxiv.org/abs/2406.11674
- Hallazgo clave: formato sparse hardware-friendly para inference offload; reduce
  tráfico de pesos aprovechando sparsity del modelo.
- Estado: 🟡 PLAUSIBLE. RESULTADO DE LITERATURA.
- Relación: formato de pesos (nivel almacenamiento), H-001.

### P-015 — I/O for LLM Inference: A Survey (Springer, 2026)
- URL: https://link.springer.com/article/10.1007/s10462-026-11651-1
- Hallazgo clave: descompone el I/O de inferencia en 3 flujos (pesos, KV, activaciones)
  y aplica roofline analysis a cada uno.
- Relevancia: marco teórico para task-4 (cuellos de botella).
- Estado: 🟡 PLAUSIBLE (survey reciente, no leído completo). RESULTADO DE LITERATURA.
- Relación: task-4.

### P-016 — CHEOPS'25: I/O Characterizing of Offloading LLMs to NVMe (IBM)
- URL: https://atlarge-research.com/pdfs/2025-cheops-llm.pdf
- Hallazgo clave: caracterización I/O real de offloading modelos + KV a NVMe SSD.
- Relevancia: datos medidos comparables con los nuestros (fio).
- Estado: 🟡 PLAUSIBLE. RESULTADO DE LITERATURA.
- Relación: H-001, task-4.

### P-017 — PIM Is All You Need (2025)
- URL: https://arxiv.org/abs/2502.07578
- Hallazgo clave: sistema CXL GPU-free para inferencia LLM (processing-in-memory).
- Relevancia: paradigma alternativo (¿GPU obligatoria?) — relevante para Paradigm Break.
- Estado: 🟡 PLAUSIBLE. RESULTADO DE LITERATURA. (Sin hardware CXL local: no testeable.)
- Relación: architecture/alternatives.

### P-018 — SpeedLoader (NeurIPS 2024)
- URL: https://proceedings.neurips.cc/paper_files/paper/2024/file/3d3a9e085540c65dd3e5731361f9320e-Paper-Conference.pdf
- Hallazgo clave: esquema I/O-eficiente para operación heterogénea/distribuida.
- Estado: 🟡 PLAUSIBLE. RESULTADO DE LITERATURA.
- Relación: task-4.

### P-019 — HillInfer (2025)
- URL: https://arxiv.org/html/2602.18750
- Hallazgo clave: KV eviction jerárquica usando SmartSSD (computational storage FPGA)
  para long-context en el edge.
- Relevancia: computational storage aplicado a LLM — hardware no disponible localmente
  pero idea de arquitectura.
- Estado: 🟡 PLAUSIBLE. RESULTADO DE LITERATURA.
- Relación: architecture/alternatives.

### P-020 — Neural weight compression for LMs (2025)
- URL: https://arxiv.org/html/2510.11234v1
- Hallazgo clave: codecs neurales entrenados para comprimir pesos de LLM.
- Estado: 🟡 PLAUSIBLE. RESULTADO DE LITERATURA.
- Relación: H-005 (compresión extrema).

### P-021 — MoE-SpeQ (2025)
- URL: https://arxiv.org/html/2511.14102
- Hallazgo clave: decoding especulativa cuantizada + prefetch proactivo de expertos para
  ocultar la latencia I/O del offloading.
- Relevancia: el I/O bottleneck del offloading MoE se ataca con prefetch + especulación.
- Estado: 🟡 PLAUSIBLE. RESULTADO DE LITERATURA.
- Relación: H-001, E005 (prefetch).

### P-022 — Diff-MoE (SC 2025)
- URL: https://dl.acm.org/doi/10.1145/3712285.3759903
- Hallazgo clave: caché de expertos por prioridad/diferencial para batch.
- Estado: 🟡 PLAUSIBLE. RESULTADO DE LITERATURA.
- Relación: E006.

## Análisis transversal

**Patrón dominante en el estado del arte**: el offloading/streaming existe y funciona
(FlexGen, llama.cpp, PowerInfer-2, MoE-Infinity, gdsllm), pero el cuello de botella
fundamental documentado es el I/O de pesos + la localidad de activación de expertos.
El frente de investigación activo (2024-2025) ataca: (a) caché/prefetch de expertos,
(b) sparsity de activación (ReLU/TurboSparse), (c) formatos de pesos, (d) regeneración
de pesos (SeedLM), (e) routing con localidad (Oracle-MoE, ReMoE).

**Novedad relativa de nuestras ideas (clasificación preliminar)**:
- Streaming SSD→VRAM con caché: CONOCIDA (variante de MoE-Infinity/PowerInfer-2).
- ReLU sparsity: CONOCIDA (TurboSparse).
- Pesos regenerados por semilla: VARIANTE de SeedLM.
- Caché de expertos predictivo: VARIANTE de MoE-Infinity/fMoE/Diff-MoE.
- La COMBINACIÓN específica (streaming + caché predictivo de expertos + sparsity +
  regeneración parcial, en una RTX 3060 12GB, 32GB RAM, NVMe 222GB) no tiene precedente
  documentado como sistema único — APARENTEMENTE NOVEDOSA como combinación, pero cada
  pieza es conocida. (Pendiente de prior-art check sistemático en cada fase.)
