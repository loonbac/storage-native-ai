# Descubrimiento 0010

## Hipótesis

H-009: el problema del 235B proviene de la escala del espacio de expertos; modelos con
menor working set logran mejor relación capacidad/tráfico. Distinguir propiedad de la
arquitectura de propiedad específica del Qwen3-235B.

## Motivación

Si la relación working-set/tamaño es una propiedad de la arquitectura Qwen3-MoE, la
reducción de working set requiere modelos más chicos (con su trade-off de calidad) —
no es un problema específico del 235B.

## Estado previo del conocimiento

- 0004: working set W=32: 30B → 44-53 expertos/capa (35-42%); 235B → ~50 (39%).
- 0008: peso corregido por experto del 235B = 12.24 MB (down Q6_K 5.16 + gate/up 3.54).

## Estado del arte relacionado

- MoE fine-grained (DeepSeekMoE): arquitecturas con más expertos pequeños.
- La literatura de MoE scale: el working set crece con el modelo.

## Experimento

E007/H-009: consolidación de los datos existentes (traces del ciclo 2 de ambos
modelos) en una tabla comparativa: working set por token/ventana, bytes únicos/token,
relaciones WS/model-size y WS/VRAM, tráfico teórico mínimo (simulador Oracle a 12 y
44 GB). Sin descargas nuevas.

## Configuración

Simulador del ciclo 2 (cache_simulator.py) sobre traces de 30B (4 prompts, 1196
tokens) y 235B (2 prompts, 1198 tokens). Pesos: 2.92 MB (30B Q4) y 12.24 MB (235B).

## Resultado

| Métrica | Qwen3-30B-A3B | Qwen3-235B-A22B |
|---|---|---|
| Capas / expertos / top-k | 48 / 128 / 8 | 94 / 128 / 8 |
| Activaciones/token | 384 | 752 |
| Working set W=32 (por capa) | 44-53 (35-42%) | ~50 (39%) |
| Working set absoluto W=32 | ~7.0 GB | ~57.5 GB |
| Modelo de expertos | 17.9 GB | 137.3 GB |
| **Relación WS/model-size** | **~39%** | **~42%** |
| Working set / VRAM (12 GB) | 0.58 | 4.8 |
| **Tráfico mínimo Oracle @12 GB** | **16.9 MB/token** | 4598 MB/token |
| **Tráfico mínimo Oracle @44 GB** | **13.3 MB/token** | 1157 MB/token |

## Evidencia

cache_simulator.py (reproducible), traces del ciclo 2, 0004, 0008.

## Qué demuestra

1. **La relación working-set/model-size es CONSTANTE (~40%)** entre el 30B y el 235B
   → es una propiedad de la ARQUITECTURA Qwen3-MoE (escala lineal), no del 235B.
2. **El objetivo de tráfico (≤37.5 MB/token) ES alcanzable con modelos cuyo working
   set cabe en la jerarquía**: el 30B da 13.3 MB/token @44 GB e incluso 16.9 MB/token
   con solo 12 GB de caché (¡su working set de 7 GB cabe en VRAM!).
3. **La propiedad limitante es la ESCALA**: el 235B tiene working set 57.5 GB > 44 GB
   disponibles → 1157 MB/token. Cualquier modelo con working set ≤ jerarquía alcanza
   el objetivo de TRÁFICO.

## Qué NO demuestra

- No demuestra que exista un modelo de CALIDAD DE FRONTERA con working set pequeño
  (el 30B no es frontera). Requeriría modelos nuevos (no justificado sin literatura
  que los sugiera — no hay descargas nuevas en este ciclo).
- La calidad del 30B vs 235B no se comparó formalmente (obvio: el 235B es superior).

## Conocimiento modificado

- **H-009: PARCIAL** — la propiedad es de escala (WS ∝ tamaño, relación ~40%
  constante); el objetivo de tráfico se alcanza con modelos que caben en la jerarquía
  (30B: 13-17 MB/token); la calidad es el trade-off fundamental. No hay arquitectura
  sub-lineal identificada en los modelos disponibles.
- Combinación con H-007/H-011 en el 235B (corregido): 2.87 × 0.97 (sparsity 4.53%) ×
  0.50 (k=4) ≈ 1.39 GB/token — el 235B sigue ~37× sobre el objetivo por su escala
  (el efecto de la sparsity es marginal tras la corrección).

## Estado

🟢 Demostrado (comparativa con datos existentes).

## Confianza

Alta (métricas del ciclo 2 consolidadas; relación constante verificada).

## Próxima hipótesis

La frontera calidad/working-set: ¿existe una arquitectura con calidad de frontera y
working set ≤ 44 GB? NO TESTEABLE en este ciclo sin modelos nuevos (experimento
futuro: evaluar un MoE fine-grained de ~100B con working set menor si la literatura
lo justifica).

## Próximo experimento

Ciclo cerrado: entregable final (task-8) — veredictos consolidados + autoauditoría.
