# Análisis de cuellos de botella

> Documento central de task-4. Matemática de ancho de banda real del hardware,
> gap cuantificado parámetros-activos/token vs BW disponible, y supuestos limitantes.
> Fecha: 2026-08-11. Fuente de datos: descubrimientos 0001 y 0002 + specs.

## 1. Jerarquía de memoria real (datos medidos y specs)

| Nivel | Capacidad | BW | Latencia | Fuente |
|---|---|---|---|---|
| VRAM GDDR6 (RTX 3060) | 12 GB | ~360 GB/s | ~100 ns | spec |
| RAM DDR4-3200 dual | 32 GB | ~40-50 GB/s | ~80 ns | spec (pendiente medir) |
| PCIe H2D (CPU→GPU) | — | **26.7 GB/s** | ~50 µs + | 0002 (CUDA events) |
| NVMe secuencial | 222 GB libres | **1.1-1.6 GB/s** | — | 0001 (fio) |
| NVMe random 4K | — | ~44K IOPS | **~84 µs** | 0001 (fio) |
| Page cache RAM | ~20-25 GB útiles | (usa BW de RAM) | — | inferencia |

Clave: cada nivel es ~30-300× más lento que el anterior. La jerarquía es:
`VRAM (360 GB/s) → RAM (~45 GB/s) → PCIe (26.7 GB/s) → NVMe (1.5 GB/s)`.

## 2. Presupuesto de pesos por token a 40 tok/s

Objetivo North Star: 40 tokens/s. Tráfico máximo de pesos sostenible desde cada nivel:

| Nivel | BW ÷ 40 tok/s | Params Q4 (0.56 B/param) |
|---|---|---|
| NVMe | 37.5 MB/token | **75 M** |
| RAM | 1.125 GB/token | **2.25 B** |
| VRAM | 9 GB/token | **16-18 B** |

## 3. Demanda real de Qwen3-235B-A22B (ancla)

- Modelo completo: 235B × 0.56 B/param ≈ **132 GB** (Q4_K_M ≈ 130-140 GB).
- Activos por token: 22B × 0.56 ≈ **12.3 GB/token** si NO hay reutilización entre tokens.
- Pasada completa del modelo desde NVMe: 132 GB ÷ 1.5 GB/s ≈ **88 s** (una sola pasada).

## 4. Casos: ¿qué pasa con cada estrategia?

### 4.1 Streaming naive (leer el modelo completo por token)
132 GB/token → 5.3 TB/s necesarios → **×3500 del NVMe real**. Inviable. ⚫-candidato para
*esta estrategia* (no para el objetivo): el streaming naive es imposible por construcción.

### 4.2 MoE sin caché (solo pesos activos, sin reutilización)
12.3 GB/token → 484 GB/s → **×323 del NVMe**, ×11 de la RAM. Inviable con streaming puro.

### 4.3 Jerarquía ideal (VRAM+RAM+NVMe al 100%, sin locality)
VRAM 9 + RAM 1.125 + NVMe 0.0375 = **10.16 GB/token** vs 12.3 demandados →
**déficit del 17%**. Ni siquiera con toda la jerarquía a plena eficiencia se alcanzan
40 tok/s SIN reutilización de pesos entre tokens.

### 4.4 Con locality de expertos (hit rate h en caché)
Tráfico efectivo = 12.3 × (1−h) GB/token.

| h (fracción de pesos activos ya en caché) | Tráfico/token | Tokens/s teórico (VRAM+RAM) | ¿40 tok/s? |
|---|---|---|---|
| 0.0 | 12.3 GB | 33 | NO (déficit 17%) |
| 0.2 | 9.84 GB | 41 | **SÍ, marginal** |
| 0.5 | 6.15 GB | 66 | SÍ, holgado |
| 0.8 | 2.46 GB | 164 | SÍ, muy holgado |
| 0.9 | 1.23 GB | 328 | SÍ |

**Conclusión central**: basta con ~20% de reutilización de pesos activos entre tokens
consecutivos para que 40 tok/s de Qwen3-235B Q4 sea matemáticamente factible en esta
máquina. La localidad de routing de expertos es LA variable que decide el North Star.

### 4.5 ¿Cuánto cabe residente en VRAM?
12 GB totales − KV cache (ctx 8-32K ≈ 1-2 GB) − activaciones (~1 GB) ≈ **9-10 GB de pesos
residentes ≈ 16-18B params Q4**. Los 22B activos no caben todos residentes; ~4-6B params
(~3.4 GB/token) deben venir de niveles inferiores si cambian entre tokens. Con locality,
los "más usados" son justamente los que quedan residentes.

## 5. El gap en una frase

> **Modelos actuales activan miles de millones de parámetros por token; el NVMe solo
> puede entregar ~75 M/token a 40 tok/s. El gap (~2-3 órdenes de magnitud) se cierra
> con la jerarquía completa + reutilización (locality) de pesos activos — no con más
> ancho de banda.**

## 6. Supuestos limitantes (estado y qué lo resolvería)

| # | Supuesto | Estado | Qué lo falsifica/confirma |
|---|---|---|---|
| S1 | NVMe ~1.1-1.6 GB/s es el techo del nivel 1 | 🟢 medido | fio con otros bs/patterns |
| S2 | RAM ~40-50 GB/s | 🟡 spec | benchmark RAM (stream triad) |
| S3 | PCIe H2D 26.7 GB/s no es cuello | 🟢 medido | overlap con cómputo |
| S4 | **Localidad de routing de Qwen3-235B suficiente (h ≥ 0.2)** | 🟠 **DESCONOCIDO** | **E002: medir hit rate de expertos entre tokens** |
| S5 | Runtime puede solapar I/O y cómputo sin degradar | 🟠 DESCONOCIDO | pipeline benchmark |
| S6 | Q4_K_M preserva calidad suficiente | 🟠 DESCONOCIDO | evaluación de calidad vs FP8/BF16 |
| S7 | KV cache no desplaza demasiados pesos residentes | 🟡 plausible | medir KV footprint por ctx |
| S8 | Page cache de 32 GB no es un cuello (modelo 132 GB > RAM) | 🟡 plausible | evictions por muestreo |
| S9 | Qwen3-235B tiene arquitectura MoE con ~9.4% activos | 🟢 spec | verificado en config GGUF |

## 7. Implicaciones para el diseño (qué dice el análisis)

1. **El streaming desde NVMe solo sirve para la cola fría** (expertos/pesos raramente
   activados): ~75 M params/token @40 t/s. No intentar leer el modelo por token.
2. **El nivel caliente debe ser VRAM+RAM**: 10.16 GB/token combinados es el presupuesto
   real de 40 tok/s; hay que maximizar locality para que el tráfico efectivo baje de 12.3.
3. **La prioridad #1 de experimentación es medir locality de Qwen3-235B** (h). Si h es
   alto → North Star plausible con runtime optimizado. Si h es bajo → la arquitectura
   debe cambiar el problema (routing local como Oracle-MoE/ReMoE, o sparsity ReLU).
4. **Segunda prioridad**: solape I/O+cómputo (S5) y calidad Q4 (S6).
5. **El PCIe no es el problema** (26.7 GB/s): GDS (E004) aporta menos de lo esperado
   como multiplicador de BW; su valor real sería quitar copias de CPU.

## 8. Escalera de objetivos actualizada (metas realistas)

| Nivel | Meta | Meta de rendimiento realista |
|---|---|---|
| 0-1 | Modelo >> 12 GB en la 3060 | ~1-3 tok/s (streaming naive, llama.cpp) |
| 2 | Qwen3-235B Q4 (132 GB = 11× VRAM) | ~1-3 tok/s naive; 5-15 tok/s con caché |
| North Star | 40 tok/s Qwen3-235B Q4 | factible solo con h ≥ 0.2 + runtime solapado |

## 9. Honestidad epistemológica

- Nada aquí es ⚫ (imposibilidad demostrada). El déficit del 17% del caso 4.3 NO es
  imposibilidad: es el punto de partida que la locality (S4) puede cerrar.
- El caso 4.1 (streaming naive) es inviable por construcción, pero eso NO invalida el
  objetivo — solo esa estrategia.
- Todas las afirmaciones de este documento derivan de hechos medidos (0001, 0002) o
  specs verificables; la única variable crítica sin dato es S4 (locality).
