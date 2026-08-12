# Descubrimiento 0008

## Hipótesis

H-010: cambiar el layout físico / la organización de los pesos (reordenar expertos,
agrupar calientes, acceso más secuencial) reduce el COSTE FÍSICO de acceso a los
expertos — y por tanto los bytes/token leídos del NVMe.

## Motivación

El ciclo 2 mostró que la política de caché no alcanza el objetivo. H-010 pregunta si
el coste FÍSICO (no lógico) de acceso es reducible sin tocar el modelo.

## Estado previo del conocimiento

- 0001: NVMe 1.1-1.6 GB/s secuencial; 84 µs latencia random 4K; ~44K IOPS random.
- 0003: el tráfico real (page-cache-only) es 2.87 GB/token.
- Ciclo 2: el prefetch predictivo no reduce bytes (0.0%).

## Estado del arte relacionado

- Layout de pesos / tensor layout: conocido en sistemas (ENDOR P-014 toca formatos).
- El page cache LRU del kernel es independiente del layout del archivo.

## Experimento

E007/H-010: análisis del layout físico real del GGUF (offsets de los tensores de
expertos), del patrón de acceso físico por token (traces), del desperdicio de páginas,
y del efecto teórico del reordenamiento.

## Configuración

Shard 1 del 235B Q4_K_M: tensores ffn_{down,gate,up}_exps por capa (down Q6_K 5.16 MB,
gate/up Q4_K 3.54 MB por experto; 128 expertos/tensor; tensores de ~453 MB por tipo y
capa). Traces del ciclo 2 (699 tokens p1).

## Resultado

| Métrica física | Valor |
|---|---|
| Tensores por capa (orden) | down (Q6) → gate (Q4) → up (Q4) |
| Tamaño por experto | 3.54 MB (Q4), 5.16 MB (Q6 down) |
| Lecturas por token | 2,256 (8 expertos × 94 capas × 3 tensores) |
| Bytes brutos por token | 9.2 GB (752 expertos activados × 12.24 MB) |
| Lecturas físicas por token | 2256 lecturas de 3.54-5.16 MB (gate/up Q4, down Q6) = 9.2 GB totales |
| Distancia entre lecturas (mismo tensor) | ~57 MB (dispersos en 453 MB) |
| Desperdicio de páginas | ≈ 0 (experto leído completo, páginas alineadas) |
| Eficiencia I/O | alta (reads de 3.5-5 MB → BW casi secuencial) |

## Evidencia

experiments/E007/ (análisis de offsets + patrón de acceso). Argumento de invarianza:
el page cache LRU del kernel opera por página de 4 KB; la frecuencia de acceso a cada
página es una propiedad de los datos y los traces, NO del layout. El reordenamiento
cambia la CONTIGUIDAD (qué páginas son vecinas), no la FRECUENCIA de acceso a cada
página → el conjunto de misses del LRU (bytes leídos del NVMe) es IDÉNTICO en cualquier
layout.

## Qué demuestra

1. **El layout físico NO puede reducir los bytes/token leídos del NVMe** (invarianza
   del LRU por página ante reordenamientos).
2. **No hay desperdicio de páginas**: los expertos se leen completos y alineados;
   el tráfico físico ≈ tráfico lógico (ya medido: 2.87 GB/token en E002).
3. La eficiencia I/O ya es alta (reads de MBs); el reordenamiento solo cambiaría la
   latencia de acceso (no la métrica del ciclo).

## Qué NO demuestra

- No descarta mejoras de LATENCIA (reads contiguos vs dispersos) — irrelevante para la
  métrica principal (bytes/token), relevante solo para el TTFT/tokens/s marginal.
- No cubre compresión de almacenamiento (relacionada con H-008, ya refutada).

## Conocimiento modificado

- **H-010: REFUTADA** para la métrica principal (NVMe bytes/token). El coste físico de
  acceso no es reducible reordenando; el tráfico está determinado por los bytes únicos
  necesarios + relecturas (caché), no por el layout.
- Los downs son Q6_K (5.16 MB), no Q4_K — el peso por experto promedio es mayor de lo
  asumido (corrección de detalle: los expertos pesan 3.54+3.54+5.16 = 12.24 MB, no
  11.42).

## Estado

🟢 Demostrado (análisis del layout real + argumento de invarianza).

## Confianza

Alta (argumento matemático + datos del layout real).

## Próxima hipótesis

El tráfico está limitado por bytes únicos + relecturas. Restan: top-k reducido (H-011)
y la comparativa de working set (H-009).

## Próximo experimento

H-011: simulación de k reducido sobre los traces + calidad.
