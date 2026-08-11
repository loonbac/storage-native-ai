# E002d — Instrumentación del routing (tracer de expertos)

**Fecha:** 2026-08-11
**Estado:** 🟢 FUNCIONAL y VALIDADO

## Qué se construyó

Fork local de llama.cpp (b10333, commit 0865990) con un **tracer de routing de
expertos** habilitado por la env var `LLAMA_TRACE_MOE=<path>`.

### Mecanismo (3 puntos, 84 líneas de diff)

1. **Captura en construcción del grafo** (`src/llama-graph.cpp`, en `build_moe_ffn`):
   tras el top-k de expertos, se crea un nodo `ggml_cpy` hacia un tensor persistente
   nombrado `moe_trace_persist-<il>` y se agrega al grafo. El cpy se computa en el
   momento en que `selected_experts` aún es válido (antes de que el gallocr recicle su
   buffer).
2. **Lectura en el eval callback del scheduler** (`src/llama-context.cpp`,
   `llama_moe_trace_cb`): el callback del sched se invoca pre-computo de cada nodo;
   cuando el nodo tiene nombre `moe_trace_persist-*`, se copia `src[0]`
   (`selected_experts`) a un vector persistente en `llm_graph_result`.
   *Motivo del matcheo por nombre y no por puntero: el sched reescribe los tensores del
   grafo (copias entre backends), rompiendo las comparaciones de punteros.*
3. **Write-out** (final de `process_ubatch`): se escribe cada capa capturada como
   `<token_id> <layer> <ne0> <e0> ... <e{ne0-1}>` en el archivo de trace.

### Decisiones de diseño críticas (lecciones)

| Problema encontrado | Solución |
|---|---|
| El gallocr recicla buffers de tensores intermedios tras su último uso → solo la última capa sobrevivía | Nodo persist + cpy (el output del cpy no se recicla; lectura en callback pre-computo del cpy) |
| El sched reescribe punteros de tensores → matcheo por puntero fallaba | Matcheo por NOMBRE del nodo (`moe_trace_persist-<il>`) |
| Los decodes con grafo reutilizado no reconstruyen → traces faltantes | Forzar rebuild del grafo mientras el tracing está activo (`g_llama_moe_trace == nullptr` en la condición de reuse) |
| `strncmp` con 18 chars comparaba el `-` contra `\0` → nunca matcheaba | `strncmp(..., 17)` + `atoi(name+18)` |

### Validación (smoke tests)

1. **Qwen2.5-7B (denso, sin MoE)** con trace activo: corre sin crash, 0 líneas (correcto).
2. **Qwen3-30B-A3B (MoE, arquitectura qwen3moe — la misma que el 235B)** con trace:
   - 1107 líneas, **formato 100% OK** (NF == ne0+3), **0 índices fuera de [0,128)**.
   - **48/48 capas cubiertas uniformemente** (23-26 líneas por capa; sin sesgo en la
     capa final).
   - **128/128 expertos distintos** observados; top-5 con concentración visible:
     {18:153, 75:147, 8:140, 116:139, 52:134} — **primer indicio de locality**.
   - 23 token-ids únicos en el run.
3. **Fork sin trace**: rendimiento idéntico al baseline (tg256 68.66 vs 68.76 t/s E001).

### Costo del tracing

- Solo activo con `LLAMA_TRACE_MOE` definida (apertura perezosa + rebuild forzado).
- Sin la env var: **cero overhead** (una comparación de puntero por process_ubatch).
- Con tracing en el 235B: rebuild del grafo por decode (~ms) — despreciable vs el
  compute I/O-bound (0.4 t/s).

### Formato del trace (documentación de la definición operacional)

```
<token_id> <layer> <ne0> <e0> ... <e{ne0-1}>
```
- `token_id`: id del token en el ubatch actual (encode: cada token del prompt; decode: el token generado).
- `layer`: 0..n_layer-1.
- `ne0`: número de expertos seleccionados (top-k; 8 para Qwen3 MoE).
- `e_i`: índice del experto seleccionado (0..127 para Qwen3 MoE).

**Nota sobre repeticiones:** el runtime (llama-cli con chat template) procesa algunos
token-ids múltiples veces (prompt raw + template + decodes redundantes). Cada línea del
trace es una OBSERVACIÓN REAL de activación (token, capa, expertos) — para el análisis
de locality se conservan todas (es una muestra empírica del tráfico real).

## Archivos

- `llama-moe-tracer.patch` — diff completo del fork (84 líneas, 3 archivos).
- Fork: `/home/loonbac/Projects/tools/llama.cpp-b10333-fork/` (build en `build/bin/`).
- Binary: `build/bin/llama-cli` (y llama-bench/llama-server con el mismo patch).

## Reproducibilidad

```bash
cd /home/loonbac/Projects/tools/llama.cpp-b10333-fork/build/bin
LLAMA_TRACE_MOE=/tmp/trace.txt ./llama-cli -m <modelo-gguf> -ngl 0 -st -no-cnv \
  -p "<prompt>" -n <N> -t 8 --no-display-prompt
# validar
awk '{if (NF != $3+3) bad++} END {print "malformadas:", bad+0}' /tmp/trace.txt
```

## Próximo paso

E002d completo: capturar traces del **Qwen3-235B** (el modelo ancla) y de Qwen3-30B-A3B
con múltiples prompts → dataset para E006.3 (distribución) y E006.1 (Oracle Cache).
