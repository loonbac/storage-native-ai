# STORAGE-NATIVE AI — Research Ledger

> Investigación de sistemas de IA donde el **almacenamiento masivo forma parte activa de la
> jerarquía de memoria del modelo**, con RAM y VRAM como cachés de alta velocidad.

## North Star

> **Ejecutar un modelo de frontera de escala equivalente a DeepSeek-V4-Flash a ~40 tokens/s
> usando una única NVIDIA RTX 3060 de 12 GB de VRAM, sin depender de un clúster de cientos
> o miles de GPUs.**

Este objetivo es deliberadamente extremadamente ambicioso. Ninguno de estos supuestos es
obligatorio:

- NO asumir que las técnicas actuales son suficientes.
- NO asumir que la arquitectura Transformer es obligatoria.
- NO asumir que los pesos tienen que residir en VRAM.
- NO asumir que la arquitectura actual de los LLM es la óptima.
- NO asumir que la solución ya existe.

## Escalera de objetivos

| Nivel | Meta |
|---|---|
| 0 | Demostrar inferencia fuera de VRAM |
| 1 | Modelo significativamente mayor que VRAM |
| 2 | Modelo 10× mayor que VRAM |
| 3 | Modelo 50× mayor que VRAM |
| 4 | Modelo 100× mayor que VRAM |
| 5 | Modelo de frontera |
| Final | DeepSeek-V4-Flash ~40 tok/s en RTX 3060 12 GB |

**Ancla experimental actual:** Qwen3-235B-A22B (MoE, 235B totales / 22B activos) en Q4_K_M
(~130–140 GB). Misma clase arquitectónica que los DeepSeek de frontera (MoE gigante, pocos
expertos activos). Cabe en el NVMe de trabajo (~222 GB libres). DeepSeek-R1/V3 (671B, ~400 GB
en Q4) queda **descartado por límite de disco**.

## Estados del conocimiento

Toda afirmación importante debe llevar UNO de estos estados:

- 🟢 **DEMOSTRADO** — evidencia experimental reproducible o demostración suficientemente sólida.
- 🟡 **PLAUSIBLE** — evidencia favorable pero insuficiente.
- 🟠 **DESCONOCIDO** — no hay evidencia suficiente.
- 🔴 **ACTUALMENTE INVIABLE** — no funciona con las técnicas/arquitectura/hardware investigados. NO implica imposibilidad fundamental.
- ⚫ **IMPOSIBILIDAD DEMOSTRADA** — razón fundamental (demostración matemática, límite físico, contradicción lógica, restricción de información). Uso excepcional.

**Regla**: "esta implementación falla" ≠ "el objetivo es imposible". Nunca extrapolar de lo
particular a lo global.

## Clases de evidencia

```text
HECHO                    — observado/medido directamente
INFERENCIA               — derivado lógicamente de hechos
HIPÓTESIS                — afirmación verificable aún no confirmada
SUPOSICIÓN               — asumido sin verificar
RESULTADO EXPERIMENTAL   — salida medida de un experimento
RESULTADO DE LITERATURA  — afirmación extraída de la literatura
ESPECULACIÓN             — idea sin soporte
```

## Protocolo de corrección de conocimiento

Nunca borrar conocimiento anterior. Ante contradicción:

```text
CONOCIMIENTO ANTERIOR → CONTRADICCIÓN → ANÁLISIS DE EVIDENCIA
→ EXPERIMENTO SI ES NECESARIO → NUEVA CONCLUSIÓN
```

El conocimiento refutado se conserva como:

```text
Estado: REFUTADO
Razón:
Experimento:
Evidencia:
Fecha:
```

## Estructura

```text
research/
├── README.md              ← este archivo
├── literature/            ← Modo A: papers, related work, bibliografía
├── discoveries/           ← cada descubrimiento numerado (formato en discoveries/README.md)
├── hypotheses/            ← activas, confirmadas, refutadas
├── experiments/           ← E001, E002, ... (uno por carpeta, reproducible)
├── architecture/          ← arquitectura actual, alternativas, historial
├── rejected/              ← ideas/ramas descartadas con motivo
└── knowledge/             ← estado del conocimiento actual + historial
```

## Hardware objetivo (medido)

| Componente | Valor medido | Clase de evidencia |
|---|---|---|
| GPU | NVIDIA RTX 3060 12 GB (sm_86), driver 610.57.04 | HECHO (nvidia-smi) |
| CPU | AMD Ryzen 7 5700X, 8C/16T | HECHO (lscpu) |
| RAM | 32 GB (31 GiB), zram 4 GB swap | HECHO (/proc/meminfo) |
| NVMe trabajo | SK Hynix 238G PCIe 3.0 x4, en `/home/loonbac/Projects`, ~222 GB libres | HECHO (lsblk/df) |
| NVMe secuencial 1M (1 job, depth 32, direct) | **1126 MB/s** | RESULTADO EXPERIMENTAL (fio) |
| NVMe secuencial agregado (4 jobs) | **~1565 MB/s** | RESULTADO EXPERIMENTAL (fio) |
| NVMe random 4K latencia media | **84.5 µs** (p50 ≈ 100 µs) | RESULTADO EXPERIMENTAL (fio) |
| NVMe random 4K depth 1 | ~48 MB/s, ~12K IOPS | RESULTADO EXPERIMENTAL (fio) |
| NVMe random 4K con page cache (32 GB RAM) | 390 MB/s (×8 vs direct) | RESULTADO EXPERIMENTAL (fio) |
| Raíz `/` | SATA Kingston SA400, 53 GB libres — **no usar para modelos grandes** | HECHO (df) |

## Toolchain (task-1)

| Herramienta | Versión | Origen |
|---|---|---|
| PyTorch | 2.13.0 + CUDA 13.3 | pacman `python-pytorch-cuda` |
| CUDA toolkit | 13.3.73 | pacman (dep de llama.cpp-cuda) |
| llama.cpp | b10333 (8dc0728), CUDA sm_86 | AUR `llama.cpp-cuda` |
| fio | 3.42 | pacman |

Smoke test GPU (Qwen2.5-0.5B Q4_K_M): prompt 1550 t/s, generación 378.8 t/s. HECHO.

## Principios operativos

1. **Maximizar información por unidad de recurso, no commits.** Un experimento que produce
   0.5 tok/s pero explica el porqué vale más que uno que produce 20 tok/s sin explicación.
2. **Escalera experimental incremental** — no lanzarse directo al modelo objetivo.
3. **Registrar siempre Rendimiento / Memoria / Calidad por separado.**
4. **Reproducibilidad**: hardware, OS, drivers, versiones, código, modelo, quant, config,
   comandos, resultados y logs.
5. **No autoengaño**: actividad ≠ progreso, más código ≠ más conocimiento, una ejecución
   exitosa ≠ solución general, explicación plausible ≠ explicación demostrada.
6. **Falsificación obligatoria**: al menos un agente que intente destruir la hipótesis activa.
7. **Prior-art check**: nunca declarar "hemos inventado X" sin comparar contra el estado del arte.

## Registro de sesiones

- Cada sesión: ejecutar experimentos → actualizar `knowledge/current.md` → guardar
  descubrimientos en engram (`mem_save`, estructura What/Why/Where/Learned).
