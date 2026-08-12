# Pasada de falsificación F-002 (2026-08-11)

Objetivo: falsificar **H-006** ("una caché de expertos reduce el tráfico NVMe/token de
Qwen3-235B hacia ≤37.5 MB/token") con el límite teórico (Oracle Cache) como arma.

## Resultado: H-006 REFUTADA

**Evidencia**: discoveries/0005. El Oracle (Belady MIN, el techo matemático de TODA
política de caché) da **933 MB/token con 44 GB** (VRAM+RAM reales) y 4139 MB/token con
12 GB — 25× y 110× el objetivo de 37.5 MB/token, respectivamente. Incluso con una caché
imposible de 96 GB, el techo es 110 MB/token (3× el objetivo).

**Qué se refutó EXACTAMENTE**: la afirmación "la locality de Qwen3-235B es explotable
mediante caching de expertos hasta ≤37.5 MB/token". NO se refutó: (a) que la caché de
expertos mejore el rendimiento práctico (2.87 → ~0.95 GB/token, ~3×); (b) que otras
técnicas (sparsity, compresión, arquitectura) puedan alcanzar el objetivo.

## Propiedad limitante (por qué la caché no alcanza)

1. **Working set de reutilización amplio**: la ventana de ~32 tokens del 235B activa
   ~50 de los 128 expertos por capa → ~54 GB de pesos en la ventana de reutilización.
   La caché real (44 GB) no la cubre → ~845 MB/token de reutilización residual que la
   caché no puede evitar (el Oracle lo confirma).
2. **Distribución plana** (0004): top-25% de expertos cubren solo 35% de activaciones —
   no hay pocos expertos calientes seleccionables.
3. **Cold misses**: 134.2 GB de expertos deben leerse al menos una vez; a N tokens el
   costo es 134.2/N MB/token (≈110 MB/token a 1198 tokens). Solo con contexto largo
   (N ≥ ~3600) baja de 37.5 — pero la reutilización residual lo impide aun así.

## Nueva familia de hipótesis (para el ciclo 3)

| ID | Hipótesis | Mecanismo | Cómo falsarla |
|---|---|---|---|
| H-007 | La **sparsity de activación** (ReLU-entrenado, TurboSparse-style) reduce los bytes únicos por token de la raíz | ~95% de neuronas FFN inactivas → menos bytes por experto procesado; menos expertos activos | Medir tráfico mínimo por token de un modelo ReLU-sparse con el mismo trace/simulador |
| H-008 | La **compresión/regeneración de pesos** (SeedLM-style) reduce el costo por experto leído | Semillas PRNG en vez de pesos → 4-8× menos bytes por experto | Evaluar SeedLM sobre Qwen3-235B (o proxy 30B): calidad + tráfico |
| H-009 | **Arquitecturas con menor working set**: menos capas × más expertos, o shared experts jerárquicos | Reduce las unidades (capa, experto) en la ventana de reutilización | Simular con traces de un MoE con n_layers menor / n_expert mayor |
| H-010 | El objetivo 37.5 MB/token es alcanzable solo con **contexto largo (N ≥ 3600 tokens) + caché ≥ 96 GB** — impráctico en esta máquina | Amortización del cold miss + cobertura del working set | Run de ~4000 tokens con caché de 96 GB simulada (verificar el límite) |
| H-011 | La **combinación** caché de expertos (VRAM) + page cache (RAM) + prefetch predictivo alcanza ~0.9 GB/token y ~1.2 t/s — la mejora práctica real | Stack completo de 44 GB efectivos | E006 real (implementación) — justificable como mejora 3×, no como North Star |

**Nota metodológica**: H-006 se refutó con el techo TEÓRICO (Oracle), no con una
implementación fallida — cumple la regla de no convertir "la implementación no puede"
en "el objetivo es imposible". El objetivo sigue siendo la brújula; el ciclo 3 ataca
el término de reutilización desde la raíz (H-007/H-008/H-009).
