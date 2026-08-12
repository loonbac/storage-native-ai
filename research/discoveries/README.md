# Descubrimientos

Cada descubrimiento importante se documenta como `XXXX.md` (0001, 0002, ...) con el formato
obligatorio de la sección 13 del proyecto:

```markdown
# Descubrimiento XXXX

## Hipótesis
¿Qué creíamos que podía ocurrir?

## Motivación
¿Por qué investigamos esto?

## Estado previo del conocimiento
¿Qué sabíamos antes?

## Estado del arte relacionado
¿Qué trabajos existentes están relacionados?

## Experimento
¿Qué hicimos exactamente?

## Configuración
Hardware:
Software:
Modelo:
Versión:
Parámetros:
Cuantización:
VRAM:
RAM:
SSD:
Configuración:

## Resultado
Datos medidos.

## Evidencia
Logs, métricas, benchmarks, resultados y referencias.

## Qué demuestra
Qué podemos afirmar con seguridad.

## Qué NO demuestra
Qué conclusiones NO podemos extraer.

## Conocimiento modificado
¿Qué cambió respecto al conocimiento anterior?

## Estado
Demostrado / Plausible / Desconocido / Actualmente inviable / Imposibilidad demostrada

## Confianza
Alta / Media / Baja

## Próxima hipótesis
¿Qué debemos investigar después?

## Próximo experimento
¿Cuál es el experimento con mayor valor informativo?
```

## Índice

| ID | Título | Estado | Fecha |
|---|---|---|---|
| 0001 | Ancho de banda NVMe medido (fio) | 🟢 Demostrado | 2026-08-11 |
| 0002 | Ancho de banda PCIe H2D medido (~26.7 GB/s) | 🟢 Demostrado | 2026-08-11 |
| 0003 | Qwen3-235B desde NVMe: 0.4 t/s, NVMe saturado, 2.87 GB/token, locality 78% | 🟢 Demostrado | 2026-08-11 |
| 0004 | Locality Qwen3-MoE: real y estable, distribución plana, working set amplio | 🟢 Demostrado | 2026-08-11 |
| 0005 | Oracle Cache: H-006 refutada (933 MB/token @44GB, 25× el objetivo) | 🟢 Demostrado | 2026-08-11 |
| 0006 | Sparsity de pesos del 235B: media 4.53% (capa 0 anomalía 36.5%) — H-007 refutada | 🟢 Demostrado | 2026-08-11 |
| 0007 | Compresibilidad: lossless 2-12% en capas densas, sin low-rank (H-008 refutada) | 🟢 Demostrado | 2026-08-11 |
| 0008 | Layout físico: invarianza LRU por página (H-010 refutada) | 🟢 Demostrado | 2026-08-11 |
| 0009 | Top-k reducido: k=4 −50% con calidad (H-011 parcial); k=2 incoherente | 🟢 Demostrado | 2026-08-11 |
| 0010 | Working set ∝ escala (~40% constante); 30B alcanza 13.3 MB/token | 🟢 Demostrado | 2026-08-11 |
