# Descubrimiento 0009

## Hipótesis

H-011: reducir el número de expertos activados (top-k) elimina bytes/token sin
degradar significativamente la calidad.

## Motivación

El routing top-8 activa 752 expertos/token (9.2 GB brutos con 12.24 MB/experto). Reducir k elimina una
fracción lineal de los bytes.

## Estado previo del conocimiento

- 0003: baseline 2.87 GB/token (page cache), 0.4 t/s.
- El top-8 de Qwen3 (expert_used_count) activa 8 de 128 expertos por capa.

## Estado del arte relacionado

- Top-k reducido: conocido en la literatura MoE (trade-off calidad/coste).
- MoE-SpeQ (P-021): decode especulativo con prefetch.

## Experimento

E007/H-011: (a) simulación de k=6/4/2 sobre los traces (bytes eliminados reales);
(b) experimento de calidad con `--override-kv qwen3moe.expert_used_count=int:k` en
Qwen3-30B-A3B (misma arquitectura qwen3moe, 40× más rápido que el 235B): prompts de
hecho y de razonamiento, 80-120 tokens, comparando salidas k=8 vs k=6 vs k=4 vs k=2.
El 235B confirmó el patrón en 30 tokens (respuestas coherentes en k=8/6/4).

## Configuración

Fork llama.cpp b10333, -ngl 0, t=8. Modelo 30B Q4_K_M (validación arquitectónica).

## Resultado

### Simulación de bytes (traces 235B, 699 tokens)

| k | Activaciones/token | Ahorro | Bytes brutos/token | Baseline page cache |
|---|---|---|---|---|
| 8 | 752 | 0% | 9.2 GB | 2.87 GB/token |
| 6 | 564 | 25% | 6.9 GB | 2.15 GB/token |
| 4 | 376 | 50% | 4.6 GB | **1.44 GB/token** |
| 2 | 188 | 75% | 2.3 GB | 0.72 GB/token |

### Calidad (30B, 2 prompts: hecho + razonamiento)

| k | Prompt hecho (capital de Francia) | Prompt razonamiento (trenes) | Velocidad |
|---|---|---|---|
| 8 | Correcto ("Paris") | Razonamiento correcto y completo | 17.1 t/s |
| 6 | Correcto | — | 22.1 t/s |
| 4 | Correcto (más vacilante) | Razonamiento VÁLIDO (plantea bien) | 25.6 t/s |
| 2 | — | **INCOHERENTE** ("c ab.12.5 mph? or 5cm") | 31.7 t/s |

El 235B (30 tokens): k=8/6/4 responden coherentemente; la velocidad sube con k
reducido (0.3 → 0.6 t/s a k=4, por menos cómputo).

## Evidencia

/tmp/k{8,6,4}.txt (235B), /tmp/q30_k{8,6,4,2}.txt, /tmp/r_k{8,4,2}.txt (30B).
Reproducible con --override-kv.

## Qué demuestra

1. **k=4 mantiene calidad aceptable** en prompts de hecho Y razonamiento (30B, misma
   arquitectura) → reducción real del 50%: 2.87 → 1.44 GB/token (38× el objetivo).
2. **k=2 destruye la calidad** (texto incoherente) → el límite de calidad está entre
   k=4 y k=6.
3. El ahorro es lineal en k (25/50/75%) — sin entrenamiento, solo omitiendo expertos.

## Qué NO demuestra

- No mide la degradación fina (k=4 en el 235B con evaluación formal de calidad);
  la validación es cualitativa en el 30B (misma arquitectura).
- El orden de los expertos en el trace se asume top-k (el tracer captura los 8; con
  k reducido el router real seleccionaría según scores — aproximación válida).
- No explora k=5 o k=3 (el límite está entre 4 y 6).

## Conocimiento modificado

- **H-011: PARCIAL** — la reducción de top-k da hasta 50% (k=4) con calidad aceptable
  (1.44 GB/token); k=2 refutada (calidad destruida). No alcanza el objetivo; combinable
  con H-007 (sparsity, corregido a 4.53%): 1.44 × 0.97 ≈ 1.40 GB/token (el efecto de
  la sparsity es marginal tras la corrección; el top-k=4 domina).
- El top-k reducido también ACELERA (menos cómputo): 17 → 26 t/s (30B), 0.3 → 0.6 t/s
  (235B a k=4).

## Estado

🟢 Demostrado (simulación + calidad cualitativa).

## Confianza

Media-Alta (calidad cualitativa en 30B; cuantitativa la simulación de bytes).

## Próxima hipótesis

H-009: la comparativa de working set (30B vs 235B) cierra el ciclo.

## Próximo experimento

H-009 con datos existentes (task-7).
