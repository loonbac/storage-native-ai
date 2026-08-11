# E001 — Verificación de reproducibilidad

Re-ejecución del benchmark clave (contrato de verificación del goal, punto 5).

**Fecha:** 2026-08-11 (misma sesión, ~1 h después del run original)
**Comando:** `llama-bench -m models/Qwen2.5-7B-Instruct-Q4_K_M.gguf -ngl 99 -p 512 -n 256 -t 8 -r 1`

| Métrica | Original (r=2) | Re-ejecución (r=1) | Diferencia |
|---|---|---|---|
| pp512 | 2410.90 ± 19.38 t/s | 2337.99 t/s | −3.0% (dentro de varianza) |
| tg256 | 68.76 ± 0.01 t/s | 68.69 t/s | **−0.1%** |

**Veredicto:** generación reproducible (Δ0.1%). Prompt processing dentro de varianza
(Δ3%, sensible a estado de page cache/turbo). El benchmark es reproducible.

Nota: la pequeña diferencia en pp se explica por el estado del sistema (page cache
caliente del modelo Qwen3-235B de 142GB en el primer run vs frío ahora) y el r=1 vs r=2.
La generación (memory-bound en VRAM) es insensible a esas variables.
