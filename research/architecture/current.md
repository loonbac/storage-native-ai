# Arquitectura actual

Estado del conocimiento arquitectónico en el momento actual de la investigación.
Se actualiza con cada descubrimiento; el historial de cambios va en `history.md`.

## Punto de partida (baseline del estado del arte)

- **Arquitectura dominante**: Transformer (atención + FFN), con variantes MoE
  (Mixture-of-Experts) para escalar parámetros totales manteniendo activos bajos.
- **Ejecución convencional**: todos los pesos en VRAM; GPU como único dispositivo de cómputo.
- **Inferencia fuera de VRAM**: técnicas existentes de offloading (CPU+GPU, streaming,
  mmap) con penalizaciones de 1-2 órdenes de magnitud en velocidad.
- **Problema central para este proyecto**: el tráfico de pesos desde almacenamiento
  masivo (~1.1–1.6 GB/s NVMe) impone ~28–39 MB/token a 40 tok/s, mientras los modelos
  actuales activan miles de millones de parámetros por token.

## Restricciones del hardware real (medidas)

| Recurso | Capacidad | Ancho de banda |
|---|---|---|
| VRAM | 12 GB (RTX 3060) | ~360 GB/s GDDR6 |
| RAM | 32 GB | ~40-50 GB/s DDR4 |
| NVMe | 222 GB libres | 1.1–1.6 GB/s secuencial medido, ~84 µs random 4K |

## Ramas de investigación abiertas

```text
                    OBJETIVO
                       │
       ┌───────────────┼────────────────┐
       ↓               ↓                ↓
  Weight Streaming    MoE offloading  Nueva arquitectura
       │               │                │
  Prefetch           Routing          ...
       │               │                │
  Caching            Sparsity         ...
       │               │                │
       └───────────────┼────────────────┘
                       ↓
                  combinaciones
```

Ninguna rama está comprometida todavía. Ver `alternatives.md` para las propuestas.
