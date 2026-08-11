# Historial de arquitectura

Registro cronológico de la evolución arquitectónica del proyecto. Cada entrada describe
qué cambió, por qué, y con qué evidencia. Nada se borra — ver `../knowledge/` para el
protocolo de corrección.

## 2026-08-11 — Estado inicial

- Hardware inventariado: RTX 3060 12 GB (sm_86), 32 GB RAM, NVMe 238G (~222 GB libres),
  NVMe 1.1–1.6 GB/s secuencial medido, latencia random 4K ~84 µs.
- Toolchain instalado: PyTorch 2.13.0+CUDA 13.3, llama.cpp-cuda b10333, fio 3.42.
- Ancla experimental elegida: Qwen3-235B-A22B (MoE, 22B activos) en Q4_K_M (~140 GB).
- Decisión de restricción: DeepSeek-R1/V3 (671B) descartado por límite de disco (~400 GB Q4).
- Estructura del Research Ledger creada.
