# E002 — Análisis

## Qué demuestra (HECHOS medidos)

1. **Nivel 0-1 de la escalera DEMOSTRADO**: Qwen3-235B-A22B (142.15 GB, **11.8× la VRAM**)
   genera texto desde NVMe en una RTX 3060 12 GB: **0.4 t/s** con -ngl 0 (todo CPU,
   mmap) e idéntico con -ngl 4.
2. **H-001 CONFIRMADA**: el NVMe es el cuello de botella de primer orden. Durante TODA la
   generación el NVMe estuvo saturado a 1093–1095 MiB/s (~95-100% de su capacidad
   medida de 1.1–1.6 GB/s).
3. **Locality real de Qwen3-235B (S4, parcialmente)**: el tráfico desde NVMe es
   **2.87 GB/token** (≈5.1 B params Q4), NO 12.3 GB (22B activos sin reutilización).
   La page cache de RAM sirve **~78%** de los pesos activos. La locality EXISTE en
   Qwen3-235B — contraste con la advertencia de P-007 ("no todos los MoE suiten").
   Nota: este 78% incluye el efecto de la política LRU del kernel + locality real de
   routing; no está aislado cuánto aporta cada uno.
4. **El offload parcial de llama.cpp (-ngl) no cambia el cuello para MoE**: los expertos
   (~95% del peso) siguen en NVMe→RAM→CPU. llama.cpp estándar NO tiene caché de expertos
   (a diferencia de MoE-Infinity/fMoE). VRAM pico 6353 MiB (4 layers) sin efecto en t/s.
5. **Modelo de generación I/O-bound confirmado**: `t/s = BW_NVMe ÷ tráfico_NVMe_por_token`
   = 1.15 GB/s ÷ 2.87 GB = 0.40 t/s. Exacto.

## Qué NO demuestra

- No aísla la locality de routing de la política LRU del kernel (S4 necesita un
  experimento con caché controlada: medir cuántos expertos distintos se activan por
  ventana de tokens).
- No mide calidad formal (solo muestra cualitativa).
- No mide con batch > 1.
- No prueba que la caché de expertos explícita mejore el rendimiento (requiere runtime
  con caché — propuesto como E006).
- El valor 2.87 GB/token depende del tamaño de page cache (32 GB) y del ctx; con
  contexto más largo o más RAM cambiaría.

## Conocimiento modificado

- **H-001: CONFIRMADA** (NVMe = cuello de primer orden, con evidencia de saturación).
- **H-003 (MoE con pocos activos puede correr útil con offloading)**: PARCIALMENTE
  confirmada — corre (0.4 t/s, útil para batch=1 latencia-indiferente), pero NO es
  "velocidad útil" para el North Star con llama.cpp estándar.
- **S4 (locality)**: el tráfico efectivo 2.87 GB/token (vs 12.3) demuestra locality
  operativa ~78% bajo page cache. PERO el techo de 40 t/s exige ≤ 37.5 MB/token desde
  NVMe → falta un factor ~76× de reducción de tráfico NVMe. La locality actual NO basta;
  se necesita caché explícita de expertos calientes en VRAM + predicción de routing.
- **Nueva pregunta**: ¿cuánto del 78% es locality de routing vs política LRU? Si el
  routing tuviera locality fuerte, una caché explícita de expertos en VRAM (10 GB ≈ 18B
  params) podría cubrir ~80% de los activos → tráfico NVMe ~2.4 GB/token → 0.48 t/s...
  marginal. La clave real es que los expertos REUTILIZADOS entre tokens consecutivos
  queden residentes: si la reutilización es alta, el tráfico NVMe por token colapsa.

## Próximos experimentos (máximo valor informativo)

1. **E002d — medir locality de routing pura**: correr con caché fría por token (sin
   page cache: `--no-mmap` o `posix_fadvise DONTNEED` entre tokens) y comparar tráfico.
   O instrumentar el router (ver qué expertos se activan por token).
2. **E006 — caché de expertos explícita**: cargar los expertos más frecuentes a VRAM
   (p. ej. top-K por ventana) y medir la caída del tráfico NVMe por token.
3. **E003 — jerarquía explícita SSD→RAM→VRAM** con prefetch predictivo (MoE-SpeQ style).

## Implicación para el North Star

El gap real no es "NVMe 1.5 vs necesidad de 484 GB/s" (abstracto) sino "NVMe 1.15 GB/s
vs 2.87 GB/token actual con page-cache-only". Cerrar a 40 t/s requiere bajar el tráfico
NVMe por token ~76× (a ≤37.5 MB). Las palancas: (a) caché de expertos en VRAM (locality),
(b) sparsity de activación (TurboSparse), (c) pesos regenerados (SeedLM), (d) prefetch
predictivo. Ninguna está descartada; todas son verificables experimentalmente.
