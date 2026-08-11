# Descubrimiento 0002

## Hipótesis

El ancho de banda de transferencia CPU→GPU (PCIe) limita el streaming de pesos en el
mismo orden que el NVMe (~1.5 GB/s) o peor, dado el supuesto de PCIe 4.0 x8 (~12-14 GB/s
teórico) para la RTX 3060.

## Motivación

El análisis de cuellos de botella necesita el techo real de la transferencia host→GPU,
que es el tramo final del camino SSD→RAM→VRAM.

## Estado previo del conocimiento

Suposición (del goal): PCIe 4.0 x8 ≈ 12-14 GB/s para la RTX 3060.

## Estado del arte relacionado

- Especificación PCIe 4.0: 16 GT/s por lane, ~1.969 GB/s/lane útil (encoding 128b/130b).
  x8 → ~15.75 GB/s; x16 → ~31.5 GB/s.
- Los reportes locales son contradictorios: nvidia-smi reporta link.gen.current=1,
  width=16; lspci del bus 06:00.0 reporta (parcialmente) gen4 x4. Ambos incompatibles
  con la medición empírica (ver Resultado).

## Experimento

Benchmark de copia H2D con PyTorch 2.13.0 (CUDA events, min de 30 iteraciones) para
tensores pinned de 1, 2 y 4 GB; también pageable y latencia por tamaño pequeño.

## Configuración

Hardware: RTX 3060 12 GB (GA106 LHR), Ryzen 7 5700X, 32 GB DDR4.
Software: Arch Linux, PyTorch 2.13.0 + CUDA 13.3, driver 610.57.04.

## Resultado

| Test | BW medido |
|---|---|
| H2D pinned 1 GB (CUDA events) | **26.73 GB/s** |
| H2D pinned 2 GB (CUDA events) | **26.74 GB/s** |
| H2D pinned 4 GB (CUDA events) | **26.74 GB/s** |
| H2D pinned 2 GB (perf_counter, min 10) | 24.89 GB/s |
| H2D pageable 2 GB | 20.18 GB/s |
| H2D latencia 0.5 MB | 54 µs (~9 GB/s efectivo) |
| H2D latencia 4 MB | 241 µs (~16 GB/s) |
| H2D latencia 16 MB | 821 µs (~19 GB/s) |
| H2D latencia 64 MB | 3.14 ms (~20 GB/s) |
| D2H pageable 2 GB | 9.10 GB/s |

## Evidencia

Comando reproducible (Python/PyTorch, CUDA events, min de 30):

```python
import torch
start = torch.cuda.Event(enable_timing=True); end = torch.cuda.Event(enable_timing=True)
xp = torch.empty(n, dtype=torch.float32, pin_memory=True)
start.record(); y = xp.cuda(non_blocking=True); end.record()
torch.cuda.synchronize(); t = start.elapsed_time(end)
```

## Qué demuestra

1. El techo real H2D es **~26.7 GB/s**, consistente con PCIe Gen4 x16 (~85% eficiencia),
   NO con x8 (~15.75 GB/s). La tarjeta efectivamente transfiere a velocidades x16.
2. La latencia fija por transferencia es ~50 µs; el BW satura (>19 GB/s) a partir de
   ~16 MB por transferencia.
3. Los reportes del sistema (nvidia-smi gen1×16, lspci gen4×4) son inconsistentes entre
   sí y con la medición; el dato empírico es el que se usa para el diseño.

## Qué NO demuestra

- No mide H2D bajo carga concurrente de cómputo (contienda de link).
- No identifica por qué los reportes de link difieren (incertidumbre abierta).
- No mide el BW efectivo con GDS (GPUDirect Storage) — pendiente E004.

## Conocimiento modificado

El supuesto "PCIe 4.0 x8 ≈ 12-14 GB/s" se corrige a "**~26.7 GB/s medido**". Implicación:
el tramo host→GPU NO es el cuello de botella del streaming; el NVMe (~1.5 GB/s) sí lo
es, ~18× más lento que el H2D. La jerarquía útil para 40 tok/s queda limitada por
NVMe+RAM, con margen de sobra en PCIe.

## Estado

🟢 Demostrado (medición directa reproducible, 3 tamaños, CUDA events).

## Confianza

Alta (para el BW H2D). Media (para la interpretación del link físico, sin resolver).

## Próxima hipótesis

¿El streaming de pesos a la GPU puede mantener ~20+ GB/s sostenido con cómputo
concurrente (overlap de DMA y kernels)? ¿GDS mejora o degrada vs pinned H2D?

## Próximo experimento

E004 prep: benchmark de overlap — copiar 2 GB H2D mientras la GPU ejecuta un GEMM
continuo, midiendo BW y tiempo de cómputo degradado.
