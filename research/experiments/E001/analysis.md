# E001 — Análisis

## Qué demuestra

1. **El baseline 7B Q4_K_M genera 68.8 t/s en la 3060** con 100% VRAM. HECHO medido
   (llama-bench y llama-cli consistentes: 68.8 vs 68.7 t/s).
2. **El baseline está limitado por BW de VRAM, no por cómputo**: el tráfico de pesos
   (4.68 GB/token × 68.8 t/s ≈ 322 GB/s) usa ~89% del techo GDDR6 (360 GB/s). El
   chip (sm_86, 12.7 TFLOPS FP16... en realidad la 3060 tiene ~51 TFLOPS FP16 tensor,
   ~13 TFLOPS FP32) NO está saturado a 68 t/s con 7B Q4.
3. **Modelo simple del techo de generación**: `tokens/s ≈ BW_VRAM / bytes_por_token`
   para modelos densos con todos los pesos en VRAM. Para la 3060: 360 GB/s / 4.68 GB =
   77 t/s teórico → 68.8 medido (89% de eficiencia).
4. **TTFT es despreciable en este escenario** (~0.08 s tras carga): el costo dominante
   en inferencia autoregresiva es la generación (memory-bound).

## Qué NO demuestra

- No mide con contexto largo (KV cache creciendo; VRAM disponible para pesos cae).
- No mide batch > 1 (aquí batch=1, nuestro escenario de interés).
- No mide calidad formal (perplejidad/benchmarks); solo muestra cualitativa.
- No caracteriza el límite de cómputo puro (para saberlo haría falta un modelo que
  sature el tensor core, p. ej. FP16 sin quant en batch grande).

## Conocimiento modificado

- **H-004 (Q4_K_M como punto óptimo)**: la muestra de calidad es buena; pendiente de
  evaluación formal. Estado: sigue 🟡.
- **Nuevo conocimiento**: la generación densa en esta GPU está limitada por BW de VRAM.
  Implicación para el North Star: un modelo MoE con 22B activos NO puede generar a 40
  t/s leyendo todos los activos de VRAM (necesitaría 12.3 GB/token → 492 GB/s > 360).
  Incluso en VRAM pura, 22B activos Q4 exceden el BW de la 3060 a 40 t/s. El déficit
  de BW de VRAM refuerza la conclusión de bottleneck-analysis.md: hay que reducir
  bytes/token (locality, sparsity) o el gap es mayor de lo estimado (el presupuesto
  VRAM a 40 t/s es 9 GB/token, no 12.3).

## Próximos experimentos

1. **E002** — modelo fuera de VRAM: medir locality real de routing (S4, la variable
   crítica). El baseline de 68.8 t/s es el punto de comparación: cualquier técnica de
   offloading se compara contra "todo en VRAM".
2. Medir Qwen2.5-0.5B (más chico) para la curva de BW: 0.5B Q4 = 0.33 GB/token →
   techo ~1090 t/s... (el smoke dio 378 t/s gen, limitado por otro factor: kernel
   overhead / latencia, no BW — útil para entender el piso de overhead).
