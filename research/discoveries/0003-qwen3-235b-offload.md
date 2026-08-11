# Descubrimiento 0003

## Hipótesis

Qwen3-235B-A22B (142 GB Q4, 11.8× la VRAM) puede generar texto desde NVMe en la RTX 3060
(Nivel 0-1), y el rendimiento estará limitado por el ancho de banda del NVMe, con la
locality de routing + page cache reduciendo el tráfico por token muy por debajo de los
12.3 GB de activos sin reutilización.

## Motivación

Demostrar el Nivel 0-1 de la escalera y medir la variable crítica S4 (locality real de
Qwen3-235B) que decide la viabilidad del North Star.

## Estado previo del conocimiento

- bottleneck-analysis.md: presupuesto NVMe @40 t/s = 37.5 MB/token; activos sin
  reutilización = 12.3 GB/token; locality h ≥ 0.2 haría factible 40 t/s.
- P-007 (literatura): no todos los MoE tienen localidad de routing suficiente.

## Estado del arte relacionado

- MoE-Infinity (2401.14361): sparsity-aware expert cache para batch=1.
- llama.cpp: mmap + page cache como mecanismo nativo de storage-native inference.

## Experimento

E002 (experiments/E002): llama-cli con Qwen3-235B-A22B Q4_K_M (142.15 GB), -ngl 0 y
-ngl 4, prompt 5 tokens, generación 64 tokens, ctx 4096, con muestreo de I/O NVMe
(/proc/diskstats, 2 s) y VRAM durante todo el run.

## Configuración

Hardware: RTX 3060 12 GB, Ryzen 7 5700X, 32 GB DDR4, NVMe SK Hynix (1.1-1.6 GB/s).
Software: Arch Linux, llama.cpp-cuda b10333 (8dc0728), CUDA 13.3, driver 610.57.04.
Modelo: Qwen3-235B-A22B Q4_K_M, 142.15 GB, 5 shards (repo oficial Qwen).
Cuantización: Q4_K_M (~0.605 B/param).

## Resultado

| Métrica | E002a (-ngl 0) | E002b (-ngl 4) |
|---|---|---|
| Generation | 0.4 t/s | 0.4 t/s |
| I/O NVMe medio (todo el run) | 1093 MiB/s | 1095 MiB/s |
| VRAM pico | 316 MiB | 6353 MiB |
| Wall (carga + 64 tokens) | 382.6 s | 366.6 s |

Tráfico NVMe por token = 1.15 GB/s ÷ 0.4 t/s = **2.87 GB/token** (~5.1 B params Q4).
Fracción de activos servida por page cache: **~78%**.

## Evidencia

experiments/E002/logs/: run-ngl0-20260811-133210.{log,log.io}, run-ngl4-20260811-134541.{log,log.io,log.vram},
gen-*.txt (texto generado). Reproducible con run_benchmark.sh <ngl>.

## Qué demuestra

1. Nivel 0-1 demostrado: modelo 11.8× la VRAM genera texto desde NVMe (0.4 t/s).
2. El NVMe está saturado (~95-100%) durante toda la generación → la generación es
   100% I/O-bound en el NVMe: t/s = BW_NVMe ÷ tráfico_por_token (0.4 = 1.15/2.87).
3. La locality + page cache reducen el tráfico NVMe por token de 12.3 GB a 2.87 GB
   (~78% servido por RAM) — Qwen3-235B SÍ tiene locality operativa (contrasta P-007).
4. El offload parcial de llama.cpp (-ngl) NO cambia el cuello para MoE: los expertos
   siguen en NVMe; llama.cpp estándar no tiene caché de expertos.

## Qué NO demuestra

- No aísla la locality de routing de la política LRU del kernel (S4 exacta).
- No mide calidad formal.
- No prueba que caché de expertos explícita mejore el rendimiento.
- Los números dependen del tamaño de page cache (32 GB) y del contexto.

## Conocimiento modificado

- H-001 CONFIRMADA (NVMe = cuello de primer orden, saturación medida).
- H-003 PARCIAL: corre pero no a velocidad útil para el North Star.
- S4 parcialmente resuelto: locality efectiva ~78% bajo page cache; falta factor ~76×
  para 40 t/s (2.87 GB → ≤0.0375 GB por token desde NVMe).

## Estado

🟢 Demostrado (para esta configuración; mediciones reproducibles).

## Confianza

Alta (I/O medido directamente, consistentes entre runs, modelo de cuello verificado
exactamente: 0.4 = 1.15/2.87).

## Próxima hipótesis

Una caché de expertos explícita en VRAM (top expertos frecuentes) reduce el tráfico
NVMe por token por debajo de 2.87 GB → t/s > 0.4. ¿Cuánto depende de la locality de
routing pura?

## Próximo experimento

E002d: medir locality de routing pura (caché fría por token o instrumentación del
router). E006: caché de expertos explícita.
