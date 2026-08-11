# Descubrimiento 0001

## Hipótesis

El NVMe SK Hynix de 238 GB (PCIe 3.0 x4, OEM) proporciona suficiente ancho de banda
secuencial para streamear pesos de un modelo grande, y su latencia random es lo
suficientemente baja como para justificar acceso aleatorio a expertos MoE.

## Motivación

El camino SSD→RAM→VRAM está limitado en primer orden por el ancho de banda y la latencia
del almacenamiento. Sin medición real del NVMe, cualquier análisis de cuellos de botella
sería especulación.

## Estado previo del conocimiento

Especulación: NVMe PCIe 3.0 x4 teórico ≈ 2 GB/s (3.94 GT/s × 4 lanes / 8). No medido.

## Estado del arte relacionado

- Especificación PCIe 3.0: ~1 GB/s por lane bidireccional útil (encapsulado).
- fio es el benchmark de referencia estándar para almacenamiento en bloque.

## Experimento

fio 3.42 sobre `/home/loonbac/Projects` (NVMe SK Hynix HFM256GDHTNI, ext4):
- Secuencial read bs=1M, iodepth=32, 1 job y 4 jobs, direct=1.
- Random read bs=4k, iodepth=1 (latencia) y agregado iodepth=32 × 4 jobs, direct=1.
- Random read con page cache (direct=0) para medir el efecto de la RAM de 32 GB.

## Configuración

Hardware: AMD Ryzen 7 5700X, 32 GB DDR4, NVMe SK Hynix 238G (ext4), RTX 3060 12 GB.
Software: Arch Linux, fio 3.42.
Configuración: direct=1 (excepto test page cache), unlink=1, --output-format=terse/normal.

## Resultado

| Test | Resultado |
|---|---|
| Secuencial 1M, 1 job, depth 32, direct | **1126 MB/s** |
| Secuencial 1M, 4 jobs, depth 32, direct | **~1565 MB/s** agregado (391 MB/s × 4) |
| Random 4K, depth 1, direct | ~48 MB/s, ~12K IOPS |
| Random 4K latencia (depth 1) | media **84.5 µs**, p50 ≈ 100 µs, p99 ≈ 250 µs |
| Random 4K, 4 jobs, depth 32, direct | ~173 MB/s, ~44K IOPS |
| Random 4K, page cache (direct=0) | ~390 MB/s (≈×8 vs direct) |

## Evidencia

Salida fio completa en `research/experiments/` (registrada en knowledge/history). Comandos
reproducibles:

```bash
fio --name=s1 --rw=read --bs=1M --size=2G --iodepth=32 --direct=1 --unlink=1 \
    --filename=fio_s1.bin --output-format=normal
fio --name=r1 --rw=randread --bs=4k --size=1G --iodepth=1 --direct=1 --unlink=1 \
    --filename=fio_r1.bin --output-format=normal
```

## Qué demuestra

Bajo esta configuración (ext4, direct I/O, host 5700X):
1. El ancho de banda secuencial real está en **1.1–1.6 GB/s**, ~55–78% del teórico PCIe 3.0 x4.
2. La latencia random 4K es ~84 µs de media — suficiente para no descartar acceso
   aleatorio a bloques de expertos, pero 2 órdenes de magnitud por encima de RAM/VRAM.
3. La page cache de 32 GB RAM multiplica el random read ×8 (390 MB/s): la RAM como caché
   de almacenamiento funciona, pero solo cabe ~23% de un modelo de 140 GB.

## Qué NO demuestra

- No mide acceso mezclado secuencial+random (patrón real de inferencia).
- No mide lectura con tamaño intermedio (bs=64K–256K, típico de tensores).
- No mide el ancho de banda bajo carga concurrente con la GPU (PCIe compartido).
- No mide la latencia end-to-end SSD→RAM→VRAM.

## Conocimiento modificado

La especulación "NVMe ≈ 2 GB/s" se corrige a "≈ 1.1–1.6 GB/s medido". Implicación
inmediata para el North Star: a 40 tok/s, el presupuesto de pesos por token desde NVMe es
~28–39 MB/token (≈56–78 M parámetros Q4), no los 50 MB estimados con 2 GB/s.

## Estado

🟢 Demostrado (bajo esta configuración).

## Confianza

Alta (mediciones directas con herramienta estándar).

## Próxima hipótesis

El límite de ~1.6 GB/s es del NVMe, del controlador ext4 o del host — ¿un test con
`--numjobs=8` o bs=64K cambia el agregado? ¿El acceso mmap de llama.cpp (lecturas de
tensores de tamaño variable) alcanza este ancho de banda?

## Próximo experimento

E001-bench: medir el ancho de banda de lectura real del NVMe con el patrón de acceso de
llama.cpp (mmap de un GGUF grande) usando `llama-cli` con `-ngl 0` sobre Qwen3-235B y
observando el tiempo de carga, comparado con fio bs=64K/256K.
