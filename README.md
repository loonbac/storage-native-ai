# STORAGE-NATIVE AI — Inferencia de LLMs fuera de VRAM

> **Investigación y caracterización empírica de sistemas de IA donde el almacenamiento NVMe forma parte activa de la jerarquía de memoria del modelo, utilizando RAM y VRAM como cachés de alta velocidad.**

![Linux](https://img.shields.io/badge/OS-Linux-blue)
![CUDA](https://img.shields.io/badge/CUDA-13.3-green)
![PyTorch](https://img.shields.io/badge/PyTorch-2.13.0-orange)
![llama.cpp](https://img.shields.io/badge/llama.cpp-b10333-brightgreen)
![Language](https://img.shields.io/badge/Idioma-Espa%C3%B1ol_Neutro-yellow)
![License](https://img.shields.io/badge/Licencia-MIT-blue)

---

## 🎯 Objetivos y North Star

El objetivo central de este proyecto es:

> **Ejecutar un modelo de frontera de escala equivalente a DeepSeek-V4-Flash a ~40 tokens/s utilizando una única GPU de consumo (NVIDIA RTX 3060 de 12 GB de VRAM), sin depender de clústeres de alto costo.**

### Ancla experimental actual

Para las fases iniciales de experimentación se utiliza **Qwen3-235B-A22B** (MoE con 235B totales / 22B activos, ~140 GB en Q4_K_M). **Este modelo no equivale en capacidad ni alcance a DeepSeek-V4-Flash**, sino que se emplea exclusivamente como *ancla experimental intermediaria* por compartir la arquitectura MoE gigante con pocos expertos activos y por ser el modelo más grande que cabe en el almacenamiento NVMe de trabajo disponible (~222 GB libres).

### Escalera de objetivos

| Nivel | Meta | Estado |
|---|---|---|
| **0** | Demostrar inferencia fuera de VRAM | 🟢 **DEMOSTRADO** |
| **1** | Modelo significativamente mayor que VRAM (11.8× VRAM, Qwen3-235B) | 🟢 **DEMOSTRADO** |
| **2** | Modelo 10× mayor que VRAM con caché de expertos explícita | 🟡 *En progreso (Ciclo 2)* |
| **3** | Modelo 50× mayor que VRAM | 🟠 Pendiente |
| **4** | Modelo 100× mayor que VRAM | 🟠 Pendiente |
| **5** | Modelo de frontera en producción local | 🟠 Pendiente |
| **Final** | DeepSeek-V4-Flash ~40 tok/s en RTX 3060 12 GB | 🎯 Objective North Star |

---

## 📊 Jerarquía de Memoria Medida

Mediciones empíricas realizadas sobre el hardware objetivo (NVIDIA RTX 3060 12GB + AMD Ryzen 7 5700X + 32GB DDR4 + NVMe PCIe 3.0 x4):

| Nivel | Capacidad | Ancho de banda medido | Latencia media | Fuente / Método |
|---|---|---|---|---|
| **VRAM GDDR6** | 12 GB | ~360 GB/s (especificación) | ~100 ns | Especificación del fabricante |
| **RAM DDR4-3200** | 32 GB | ~40-50 GB/s | ~80 ns | Especificación host |
| **PCIe H2D (CPU→GPU)** | — | **26.7 GB/s** | ~50 µs | Medición empírica (PyTorch CUDA events) |
| **NVMe Secuencial (direct)** | 222 GB libres | **1.1 – 1.6 GB/s** | — | Medición empírica (`fio` 3.42, 1-4 jobs) |
| **NVMe Random 4K** | — | ~44K IOPS (~173 MB/s) | **84.5 µs** | Medición empírica (`fio` direct=1) |
| **RAM Page Cache** | ~20 GB útiles | ~390 MB/s (random) | — | Medición empírica (`fio` direct=0, ×8 vs direct) |

---

## 🔬 Descubrimientos Clave Registrados

* **[Descubrimiento 0001](research/discoveries/0001-nvme-bandwidth.md):** Caracterización de ancho de banda secuencial (1.1–1.6 GB/s) y latencia aleatoria 4K (84.5 µs) del almacenamiento NVMe SK Hynix PCIe 3.0 x4.
* **[Descubrimiento 0002](research/discoveries/0002-pcie-h2d-bandwidth.md):** Demostración empírica de que la transferencia CPU→GPU mediante PCIe H2D alcanza **~26.7 GB/s** (saturando al 85% el canal PCIe Gen4 x16). **Conclusión:** El bus PCIe no es el cuello de botella del streaming; el límite de primer orden es el NVMe (~18× más lento que el bus PCIe).
* **[Descubrimiento 0003](research/discoveries/0003-qwen3-235b-offload.md):** Demostración del Nivel 0-1. Ejecución exitosa de **Qwen3-235B-A22B Q4_K_M (142.15 GB, 11.8× la VRAM)** generando texto desde NVMe en la RTX 3060 (0.4 t/s). Se demostró que el NVMe opera al 100% de saturación (I/O-bound) y que la localidad de routing + page cache reduce el tráfico efectivo de pesos de 12.3 GB/token teóricos a **2.87 GB/token** (78% atendido desde caché en RAM).
* **[Descubrimiento 0004](research/discoveries/0004-locality-qwen3moe.md):** Caracterización del ruteo MoE de Qwen3. La localidad es real y estable, pero con una distribución plana (el top-25% de expertos cubre solo el 35-42% del tráfico) y un *working set* amplio por capa (~40%).
* **[Descubrimiento 0005](research/discoveries/0005-oracle-cache-refutation.md):** Falsificación formal de H-006 mediante el algoritmo Belady MIN (Oracle Cache). Se demostró que el límite teórico absoluto con 44 GB de caché (VRAM+RAM) es de **933 MB/token** (25× por encima del objetivo de 37.5 MB/token), refutando que el almacenamiento solo con caché de expertos pueda alcanzar los 40 t/s en escala 235B.
* **[Descubrimiento 0006](research/discoveries/0006-sparsity-weights.md):** Análisis de esparsidad de pesos. La esparsidad media es de solo 4.53% (salvo la Capa 0 con 36.5%), refutando la hipótesis de esparsidad natural de matriz para reducir el tráfico.
* **[Descubrimiento 0007](research/discoveries/0007-compressibility.md):** Evaluaciones de compresibilidad sin re-entrenamiento: compresión sin pérdida entre 2% y 12% en capas densas, sin bajo rango exploitable.
* **[Descubrimiento 0008](research/discoveries/0008-layout-physical.md):** Layout físico de almacenamiento: invarianza del LRU por página ante reordenamiento.
* **[Descubrimiento 0009](research/discoveries/0009-topk-reduction.md):** Reducción de Top-k expertos. La reducción a $k=4$ disminuye el tráfico NVMe a 1.44 GB/token (~50%) preservando la coherencia del modelo.
* **[Descubrimiento 0010](research/discoveries/0010-workset-scale.md):** Demostración de que la relación *working set / escala* es una constante (~40%). En modelos escala 30B (Qwen3-30B-A3B), el tráfico se reduce a **13.3 MB/token** a 44 GB (cumpliendo el presupuesto de 37.5 MB/token), demostrando que la escala del modelo es la restricción física fundamental.

---

## 📁 Estructura del Repositorio

```text
storage-native-ai/
├── README.md              ← Este documento principal
├── research/              ← Ledger completo de investigación
│   ├── literature/        ← Estado del arte y trabajos relacionados
│   ├── discoveries/       ← Registro de descubrimientos empíricos numerados
│   ├── hypotheses/        ← Hipótesis activas, confirmadas y refutadas
│   ├── experiments/       ← Pruebas experimentales reproducibles (E001, E002, etc.)
│   ├── architecture/      ← Análisis de arquitectura actual y alternativas
│   ├── rejected/          ← Ideas y ramas descartadas con justificación
│   └── knowledge/         ← Estado del conocimiento y análisis de cuellos de botella
└── tools/
    └── patches/           ← Parches para runtime de inferencia (llama.cpp MOE tracer)
```

---

## 🛠️ Cómo Reproducir los Experimentos

### 1. Medición de almacenamiento NVMe
Para ejecutar el benchmark de I/O secuencial y aleatorio:
```bash
# Lectura secuencial directa (bs=1M, iodepth=32)
fio --name=seq_read --rw=read --bs=1M --size=2G --iodepth=32 --direct=1 --unlink=1 --filename=fio_test.bin

# Lectura aleatoria de latencia (bs=4K, iodepth=1)
fio --name=rand_read --rw=randread --bs=4k --size=1G --iodepth=1 --direct=1 --unlink=1 --filename=fio_test.bin
```

### 2. Medición de transferencia CPU→GPU (PCIe H2D)
```python
import torch

start = torch.cuda.Event(enable_timing=True)
end = torch.cuda.Event(enable_timing=True)
x_pinned = torch.empty(1024 * 1024 * 1024 // 4, dtype=torch.float32, pin_memory=True)

start.record()
y = x_pinned.cuda(non_blocking=True)
end.record()

torch.cuda.synchronize()
elapsed_ms = start.elapsed_time(end)
bandwidth_gbps = (1.0 / (elapsed_ms / 1000.0))
print(f"Ancho de banda H2D Pinned: {bandwidth_gbps:.2f} GB/s")
```

### 3. Parche de trazado de routing MoE para llama.cpp
En la carpeta `tools/patches/` se incluye el parche `0001-moe-routing-tracer.patch` para instrumentar el ruteo de expertos en `llama.cpp` (tag `b10333`).

Para aplicarlo sobre una copia limpia de `llama.cpp`:
```bash
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp
git checkout b10333
git apply ../tools/patches/0001-moe-routing-tracer.patch
```

---

## ⚖️ Principios Operativos e Rigurosidad

1. **Evidencia empírica sobre especulación:** Ninguna afirmación se acepta sin medición o derivación matemática verificable.
2. **Protocolo de corrección de conocimiento:** El conocimiento refutado jamás se borra; se conserva registrado indicando la razón, la evidencia y el experimento que lo refutó.
3. **Falsificación obligatoria:** Cada hipótesis planteada incluye la condición exacta o experimento capaz de destruirla.

---

## 📜 Licencia

Este proyecto está bajo la Licencia [MIT](LICENSE).
