# Related Work — sistemas y proyectos

Sistemas, repositorios, patentes y productos relevantes. Clasificación de novedad
relativa: conocida / variante de conocida / combinación conocida / mejora incremental /
aparentemente novedosa / novedad no determinada.

## Índice

| ID | Nombre | Tipo | Novedad | Estado |
|---|---|---|---|---|
| R-001 | llama.cpp | repo (instalado local) | — | 🟢 |
| R-002 | FlexGen | repo+paquete | — | 🟢 |
| R-003 | PowerInfer-2 | sistema | — | 🟡 |
| R-004 | MoE-Infinity | sistema | — | 🟡 |
| R-005 | gdsllm (GPUDirect Storage streaming) | repo | — | 🟡 |
| R-006 | vLLM | sistema producción | — | 🟢 |
| R-007 | Samsung SmartSSD / AMD | producto CSD | — | 🟢 |
| R-008 | DeepSeek V3 | modelo | — | 🟢 |
| R-009 | Qwen3-235B-A22B | modelo (nuestro ancla) | — | 🟢 |
| R-010 | SeedLM | método (repo) | — | 🟡 |
| R-011 | CXL memory expansion | tecnología | — | 🟠 |
| R-012 | TurboSparse modelos | modelos | — | 🟡 |
| R-013 | NVIDIA GPUDirect Storage | tecnología | — | 🟢 |
| R-014 | llama-swap-bin (AUR) | herramienta local | — | 🟢 (instalable) |

## Detalle

### R-001 — llama.cpp (ggml-org)
- URL: https://github.com/ggml-org/llama.cpp
- Qué hace: inferencia GGUF en C/C++; mmap de pesos, offload por capas (-ngl), tensor
  splitting, varios backends (CUDA, Vulkan, Metal, CPU). b10333 CUDA instalado local.
- Por qué importa: nuestro baseline de ejecución E001/E002; el mmap ya es "storage-native"
  de facto (los pesos se leen del disco bajo demanda vía page cache).
- Verificado: sí — instalado y smoke-testeado localmente. 🟢 DEMOSTRADO (local).

### R-002 — FlexGen (Relaxed-System-Lab)
- URL: https://github.com/Relaxed-System-Lab/FlexGen
- Qué hace: engine high-throughput para 1 GPU con offloading GPU/CPU/disco, políticas de
  scheduling IO-eficientes.
- Por qué importa: referencia de baseline offloading; OPT-175B en 1 GPU.
- Verificado: sí (repo público, paper MLSys'23). 🟢.

### R-003 — PowerInfer-2 (SJTU)
- URL: https://powerinfer.ai/ / https://github.com/SJTU-IPADS/PowerInfer
- Qué hace: framework móvil con neuron clusters, ejecución heterogénea; Mixtral 47B
  @11.68 tok/s en smartphone.
- Por qué importa: la granularidad neuron-cluster + predicción de activación es
  transferible a nuestro runtime.
- Verificado: parcial (paper + web). 🟡.

### R-004 — MoE-Infinity (SJTU/CMU)
- URL: https://arxiv.org/abs/2401.14361
- Qué hace: sparsity-aware expert cache para MoE en máquinas personales; batch 1.
- Por qué importa: escenario idéntico al nuestro; su caché es referencia para E006.
- Verificado: parcial. 🟡.

### R-005 — gdsllm (rscunha13)
- URL: https://github.com/rscunha13/gdsllm
- Qué hace: runtime que streamea pesos NVMe→VRAM vía GPUDirect Storage (~7 GB/s, cero
  copias por CPU).
- Por qué importa: demostración de que GDS puede multiplicar el BW efectivo vs la ruta
  page-cache (nuestro NVMe medido ~1.1-1.6 GB/s). Candidato para E004.
- Nota: repo individual, requiere verificación de madurez y de soporte GDS en nuestro
  hardware (RTX 3060 + NVMe PCIe 3.0, driver 610.57.04). Verificar viabilidad antes de
  adoptar. 🟡.

### R-006 — vLLM
- URL: https://github.com/vllm-project/vllm
- Qué hace: serving con PagedAttention, prefix caching, offloading de KV a CPU/SSD.
- Por qué importa: estado del arte en gestión de memoria jerárquica para serving.
- Verificado: sí. 🟢.

### R-007 — Samsung SmartSSD (AMD/Xilinx)
- URL: https://www.xilinx.com/publications/product-briefs/xilinx-smartssd-computational-storage-drive-product-brief.pdf
- Qué hace: CSD con FPGA; cómputo cerca del almacenamiento (compresión, DB, ML).
- Por qué importa: computational storage como paradigma (HillInfer lo usa para KV).
  NO disponible en nuestro hardware — idea de arquitectura a largo plazo. 🟢 existe / 🟠 no testeable localmente.

### R-008 — DeepSeek V3 (DeepSeek-AI)
- URL: https://github.com/deepseek-ai/DeepSeek-V3
- Qué hace: MoE 671B/37B activos, MLA, FP8. Modelo de referencia del North Star.
- Verificado: sí. 🟢.

### R-009 — Qwen3-235B-A22B (Alibaba)
- URL: https://huggingface.co/Qwen/Qwen3-235B-A22B
- Qué hace: MoE 235B totales / 22B activos; ~9.4% activos. Nuestro ancla experimental
  (Q4_K_M ≈ 130-140 GB, cabe en 222 GB libres).
- Por qué importa: proxy de frontera que cabe en el disco; medir su localidad de routing
  es crítico (P-007 advierte que no todos los MoE sirven para offloading).
- Verificado: spec del modelo (HF). Pendiente: medir localidad real en E002. 🟢 spec / 🟠 locality.

### R-010 — SeedLM
- URL: https://github.com/amkjK/SeedLM (a verificar)
- Qué hace: pesos comprimidos a semillas LFSR, regenerados en runtime.
- Verificado: paper ICLR'25. 🟡.

### R-011 — CXL memory expansion
- Qué hace: memoria expandible por PCIe (CXL.mem), NDP en el controlador.
- Por qué importa: tier de memoria intermedio entre DRAM y SSD. Nuestro CPU (AM4) no
  soporta CXL: conocimiento de literatura, no testeable localmente. 🟠.

### R-012 — TurboSparse modelos (SJTU/CMU)
- URL: https://huggingface.co/PowerInfer
- Qué hace: LLMs con sparsity de activación real (ReLU) entrenados para sparse inference.
- Por qué importa: si la calidad es suficiente, usar un modelo ReLU-sparse reduce el
  tráfico de pesos ~10× (solo neuronas activas se cargan). E0xx candidato.
- Verificado: parcial. 🟡.

### R-013 — NVIDIA GPUDirect Storage
- URL: https://developer.nvidia.com/gpudirect-storage
- Qué hace: DMA directo storage→GPU sin bounce buffer en CPU; 2-8× BW, 3.8× menor latencia.
- Por qué importa: multiplicador de BW para weight streaming (E004).
- Verificado: documentación NVIDIA. Requiere verificación local (driver 610.57.04, sm_86).
  🟢 tecnología / 🟡 soporte local.

### R-014 — llama-swap-bin (AUR)
- URL: AUR
- Qué hace: gestor de modelos GGUF con swap; utilidad para gestionar múltiples modelos.
- Por qué importa: herramienta de conveniencia; opcional.
- Estado: 🟢 instalable.

## Prior-art check — conclusiones preliminares

Las ideas del topic se clasifican así contra el estado del arte:
- "Offloading de pesos a SSD con streaming": **conocida** (FlexGen, llama.cpp, PowerInfer-2).
- "Caché de expertos con sparsity awareness": **conocida** (MoE-Infinity, fMoE, Diff-MoE).
- "Sparsity de activación para reducir tráfico": **conocida** (TurboSparse, ENDOR).
- "Regeneración de pesos": **variante** de SeedLM.
- "Computación cerca del almacenamiento": **conocida** (SmartSSD, HillInfer, RecSSD).
- "Nuestra combinación integrada (streaming+caché predictivo+sparsity+regeneración en
  1 GPU consumer 12GB)": **combinación conocida** — aparentemente novedosa como sistema
  completo, pero sin pieza radicalmente nueva identificada todavía. Pendiente de
  profundizar en cada idea antes de declarar novedad (sección 11 del topic).
