# Metodología del Ciclo 2 (directivas del usuario, 2026-08-11)

Prioridad absoluta del ciclo:

```text
medir → entender → falsificar → descubrir → implementar → medir nuevamente
```

**H-006 es una hipótesis A FALSIFICAR, no la solución.** Reglas:

1. Antes de implementar una caché real, determinar el **límite teórico de bytes mínimos
   desde almacenamiento por token** según los expertos realmente activados. Distinguir
   siempre: bytes únicos necesarios / reutilizables / repetidos / de expertos / de
   no-expertos / tráfico extra del runtime.
2. **Definición operacional exacta de NVMe bytes/token**, conservada durante todo el
   ciclo. No mezclar: lecturas del dispositivo, solicitudes del runtime, page-cache
   hits, bytes únicos. Métricas válidas distintas → medir por separado.
3. El **Oracle Cache debe respetar las restricciones reales** de granularidad y
   capacidad de caché. Prohibido darle ventaja artificial imposible para una
   implementación real.
4. Separar siempre: **rendimiento / tráfico / memoria / calidad**. Reducir tráfico NO
   es mejora si degrada la salida.
5. Si el Oracle muestra que la locality no puede acercarse a 37.5 MB/token → **NO
   forzar E006**. Determinar qué propiedad lo impide y generar la siguiente familia de
   hipótesis.
6. Si el Oracle muestra locality suficiente → investigar la MEJOR forma de explotarla
   (LRU, LFU, frecuencia, prefetch, predicción, routing-aware, u otra estrategia
   descubierta).
7. No limitarse a técnicas conocidas. Si el problema está mal planteado → proponer
   arquitectura diferente. La literatura define el estado del arte, no el límite del
   espacio de soluciones.
8. Contradicción con conocimiento previo → no borrar: registrar contradicción,
   evidencia, hipótesis afectada, actualizar estado.
9. Idea nueva potencialmente importante → **detener la optimización rutinaria** y
   diseñar el experimento de mayor valor informativo.
10. No optimizar hacia 40 tok/s por sí mismos. Descubrir primero el **límite
    fundamental de reducción de tráfico**. 40 tok/s es consecuencia deseada, no el
    objetivo científico inmediato.

Regla adicional: **nunca convertir "la implementación actual no puede hacerlo" en
"el objetivo es imposible"**. Si una vía falla: identificar qué supuesto falló,
conservar el conocimiento, buscar otra vía — salvo demostración física/matemática/lógica.

Un resultado negativo bien demostrado que elimine una familia de soluciones ES un
resultado exitoso.
