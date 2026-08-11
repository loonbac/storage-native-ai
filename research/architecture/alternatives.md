# Arquitecturas alternativas

Ideas y arquitecturas candidatas (Modo B — Inventar), actualizado tras el ciclo 1
(literatura + cuellos de botella + E001/E002). Cada una debe pasar por el pipeline:
`idea → hipótesis → modelo mental → predicción → experimento`.

Clasificación de novedad contra el estado del arte (prior-art check, related-work.md):
**conocida / variante de conocida / combinación conocida / mejora incremental /
aparentemente novedosa / novedad no determinada**.

## Contexto que las alimenta (datos del ciclo 1)

- El cuello medido: NVMe saturado (~1.15 GB/s), tráfico real 2.87 GB/token con
  page-cache-only (locality 78%), 0.4 t/s con llama.cpp estándar.
- Para 40 t/s: tráfico NVMe por token ≤ 37.5 MB (factor ~76× de reducción).
- Palancas identificadas: locality/caché de expertos, sparsity de activación,
  regeneración de pesos, prefetch predictivo, menos parámetros activos.

## Candidatas

### A-1 — Caché de expertos calientes en VRAM (H-006, prioridad inmediata)
- **Descripción:** mantener los expertos más frecuentes (top-K por ventana de tokens)
  residentes en VRAM (~10 GB ≈ 18B params Q4); el resto se lee bajo demanda.
- **Novedad:** variante de MoE-Infinity/fMoE/Diff-MoE (conocida); nuestra aportación:
  integración con el presupuesto real medido y política de eviction por locality.
- **Predicción:** tráfico NVMe por token cae de 2.87 GB a <1 GB → t/s > 1.
- **Experimento:** E006 (requiere runtime con caché — llama.cpp no lo ofrece estándar).

### A-2 — Streaming capa-por-capa con prefetch predictivo (MoE-SpeQ style)
- **Descripción:** solapar I/O de la capa t+1 con cómputo de la capa t; predicción
  especulativa de expertos (decodificación especulativa cuantizada).
- **Novedad:** variante de MoE-SpeQ (conocida).
- **Predicción:** oculta la latencia del NVMe; el límite pasa a ser el BW efectivo
  (37.5 MB/token @40 t/s sigue siendo el techo duro).
- **Experimento:** E005/E003.

### A-3 — Sparsity de activación real (TurboSparse / ReLU)
- **Descripción:** si ~95% de las neuronas FFN están inactivas (ReLU-entrenado), solo se
  cargan las activas → tráfico de pesos ×20.
- **Novedad:** conocida (TurboSparse, PowerInfer).
- **Limitación para el ancla:** Qwen3-235B usa SiLU — no tiene sparsity ReLU. Requiere
  un modelo entrenado para eso (TurboSparse-Mixtral existe) o fine-tuning del router.
- **Predicción:** con modelo ReLU-sparse, el tráfico por token cae ~10-20×.
- **Experimento:** benchmark de un modelo TurboSparse (30B) comparado con el denso.

### A-4 — Regeneración de pesos (SeedLM-style)
- **Descripción:** comprimir bloques de pesos a semillas PRNG (LFSR); regenerar la
  matriz en el dispositivo de cómputo → tráfico = semillas (≈0.1-0.25 B/param).
- **Novedad:** variante de SeedLM (ICLR'25) — conocida.
- **Predicción:** 4-8× menos bytes/token; no elimina el cómputo de regeneración.
- **Experimento:** evaluar SeedLM en el 235B o un modelo chico, medir calidad y costo.

### A-5 — Routing con localidad (Oracle-MoE / ReMoE)
- **Descripción:** modificar el router (fine-tuning) para que tokens consecutivos
  activen expertos similares → la caché funciona mejor.
- **Novedad:** conocida (Oracle-MoE ICML'25, ReMoE 2025).
- **Predicción:** aumenta el hit rate de caché sin cambiar la arquitectura de cómputo.
- **Experimento:** E002d (medir locality pura) primero; luego evaluar si el router de
  Qwen3-235B necesita ReMoE.

### A-6 — Paradigm Break: ¿por qué los pesos deben llegar a la GPU? (largo plazo)
- **Direcciones:** cómputo cerca del almacenamiento (SmartSSD FPGA — no disponible en
  este hardware), NDP en CXL (CPU AM4 no soporta CXL), ejecución híbrida
  almacenamiento→cómputo local.
- **Novedad:** conocida en investigación (HillInfer, PIM), sin precedente en hardware
  consumer.
- **Estado:** 🟠 DESCONOCIDO si es viable con hardware existente; se documenta como
  brújula, no como plan inmediato.

### A-7 — Arquitecturas con menos parámetros activos (diseño propio, largo plazo)
- **Pregunta abierta:** ¿existe una arquitectura que active <100M params/token con
  calidad de frontera? (el presupuesto del NVMe @40 t/s). Nadie lo ha demostrado; el
  estado del arte (TurboSparse, MoE fine-grained) se acerca pero no llega.
- **Novedad:** novedad no determinada — requiere investigación de arquitecturas.
- **Estado:** ESPECULACIÓN fundamentada; no es plan inmediato.

## Priorización (Coordinator, sección 28 del topic)

1. **E006 / A-1** — mayor valor informativo: falsa o confirma H-006 (la palanca de
   mayor impacto medido: locality 78% ya existe, falta explotarla).
2. **E002d / A-5** — aísla locality de routing pura (refina S4).
3. **A-3 / A-4** — reducciones multiplicativas de bytes/token (baratas de evaluar con
   modelos existentes).
4. **A-6 / A-7** — largo plazo, solo tras agotar 1-3.
