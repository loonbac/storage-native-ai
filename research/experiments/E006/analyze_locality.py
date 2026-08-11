#!/usr/bin/env python3
"""
E006.3 — Análisis de distribución de reutilización de expertos (reproducible).

Uso: python3 analyze_locality.py <trace-file> [--bytes-per-expert MB] [--n-experts 128]

Definiciones operacionales (directiva metodológica del ciclo 2):
  - Línea de trace: <token_id> <layer> <k> <e0..e_{k-1}>  (una observación real de activación)
  - activaciones_brutas(token) = k * n_layers        (todas las selecciones)
  - expertos_unicos(token)    = |union de expertos activados en el token|
  - bytes_brutos/token  = activaciones_brutas * bytes_por_experto   (sin caché)
  - bytes_unicos/token  = expertos_unicos * bytes_por_experto       (mínimo necesario)
  - tráfico_redundante_intra-token = bytes_brutos - bytes_unicos    (duplicados por capa)
  - locality temporal: hit rate de una caché que retiene los expertos de los últimos W tokens
    (por capa: la caché de un experto es por capa)
"""
import sys, os
from collections import Counter, defaultdict

def load_trace(path):
    lines = []
    with open(path) as f:
        for ln in f:
            p = ln.split()
            if len(p) < 4:
                continue
            tok, layer, k = int(p[0]), int(p[1]), int(p[2])
            exps = [int(x) for x in p[3:3+k]]
            lines.append((tok, layer, tuple(exps)))
    return lines

def main():
    path = sys.argv[1]
    bpe_mb = float(sys.argv[2]) if len(sys.argv) > 2 else 2.92  # MB por experto (30B Q4)
    n_exp = 128
    trace = load_trace(path)
    print(f"=== E006.3 locality analysis ===")
    print(f"trace: {path}")
    print(f"líneas: {len(trace)} | bytes/experto: {bpe_mb:.2f} MB | expertos: {n_exp}")

    # --- agrupar por token-procesamiento (secuencia de líneas; el mismo token-id puede repetirse) ---
    # reconstruir la secuencia de capas por (token-id, ocurrencia): usamos el orden de líneas
    # cada "procesamiento" = todas las capas de un token. Asumimos que las líneas vienen
    # agrupadas por capa en el encode y por capa en cada decode; reconstruimos por capa.
    layers = sorted(set(l for _, l, _ in trace))
    n_layers = len(layers)

    # mapear (token_id) -> lista de capas observadas
    per_token = defaultdict(list)
    for tok, layer, exps in trace:
        per_token[tok].append((layer, exps))

    # procesamientos: asumimos que por cada (token, capa) hay 1 activación; juntamos por token
    # (los token-ids repetidos corresponden a procesamientos distintos; los tratamos como
    # observaciones independientes en la secuencia global)
    seq = []  # lista de (token_id, layer, expertos) en orden
    seq = trace

    # --- 1) activaciones brutas y únicas por token-procesamiento ---
    # cada token-procesamiento = 1 línea por capa (48 líneas con el mismo token-id consecutivas
    # en encode; en decode 1 línea por capa del token actual). Reconstruimos procesamientos
    # como grupos de líneas con el MISMO token-id consecutivas por capa.
    unicos_por_tok = []
    i = 0
    n_layers_seq = n_layers
    while i < len(seq):
        tok0 = seq[i][0]
        # recoger todas las líneas consecutivas del mismo token-id
        j = i
        seen = set()
        while j < len(seq) and seq[j][0] == tok0:
            seen.update(seq[j][2])
            j += 1
        # solo contar si vimos al menos 2 capas distintas (procesamiento completo)
        capas_vistas = {seq[x][1] for x in range(i, j)}
        if len(capas_vistas) >= 2:
            unicos_por_tok.append(len(seen))
        i = j
    n_proc = len(unicos_por_tok)
    print(f"\n--- 1) por token-procesamiento (procesamientos completos: {n_proc}) ---")
    print(f"activaciones brutas/token: {8*n_layers} (k=8 × {n_layers} capas)")
    print(f"expertos únicos/token:     {sum(unicos_por_tok)/n_proc:.1f} de {n_exp}")
    mb_brutos = 8 * n_layers * bpe_mb
    mb_unicos_avg = sum(unicos_por_tok)/n_proc * bpe_mb
    print(f"bytes brutos/token:        {mb_brutos:.0f} MB  (sin caché)")
    print(f"bytes únicos/token:        {mb_unicos_avg:.0f} MB  (mínimo necesario, dedupe intra-token)")
    print(f"redundancia intra-token:   {(mb_brutos - mb_unicos_avg)/mb_brutos*100:.1f}% de las activaciones repiten un experto ya usado en el token")

    # --- 2) distribución de frecuencias global ---
    freq = Counter()
    for tok, layer, exps in seq:
        freq.update(exps)
    total_act = sum(freq.values())
    sorted_freq = sorted(freq.values(), reverse=True)
    print(f"\n--- 2) distribución de frecuencias (global, {len(freq)}/{n_exp} expertos usados) ---")
    for pct, label in [(0.01, "top-1%"), (0.05, "top-5%"), (0.10, "top-10%"), (0.25, "top-25%")]:
        n_top = max(1, int(n_exp * pct))
        covered = sum(sorted_freq[:n_top])
        print(f"  {label} ({n_top} expertos): {covered/total_act*100:.1f}% de las activaciones")
    gini_like = 1 - sum(sorted_freq) / (len(sorted_freq) * max(sorted_freq)) if sorted_freq else 0
    print(f"  max frecuencia: {max(freq.values())} | media: {total_act/len(freq):.1f} | ratio max/media: {max(freq.values())/(total_act/len(freq)):.1f}x")

    # --- 3) working set por ventana de W tokens (expertos distintos, por capa) ---
    print(f"\n--- 3) working set por ventana (expertos distintos activados en los últimos W tokens) ---")
    # construir secuencia temporal por capa: para cada capa, la lista de expertos en orden
    by_layer = defaultdict(list)
    for tok, layer, exps in seq:
        by_layer[layer].append(exps)
    for W in [1, 8, 32, 128]:
        ws = []
        # por capa: expertos distintos en ventana deslizante W (promedio sobre el trace)
        for layer in range(n_layers):
            exps_layer = by_layer.get(layer, [])
            for i in range(len(exps_layer) - W + 1):
                win = set()
                for e in exps_layer[i:i+W]:
                    win.update(e)
                ws.append(len(win))
        ws_avg = sum(ws)/len(ws) if ws else 0
        print(f"  W={W}: {ws_avg:.0f} expertos distintos promedio por capa (de 128) = {ws_avg/128*100:.0f}%")
        # bytes: expertos distintos × capas × bpe
        mb_ws = ws_avg * n_layers * bpe_mb / 1024
        print(f"        ≈ {mb_ws:.0f} MB si todo el working set de {W} tokens estuviera residente")

    # --- 4) reuse distance (distancia entre activaciones consecutivas del mismo experto, por capa) ---
    print(f"\n--- 4) reuse distance por capa (activaciones consecutivas del mismo experto) ---")
    dists = []
    for layer in range(n_layers):
        last = {}
        exps_layer = by_layer.get(layer, [])
        for i, exps in enumerate(exps_layer):
            for e in exps:
                if e in last:
                    dists.append(i - last[e])
                last[e] = i
    if dists:
        dists.sort()
        for pct in [0.25, 0.5, 0.75, 0.9]:
            print(f"  P{pct*100:.0f}: {dists[int(len(dists)*pct)]} tokens entre re-activaciones")
        print(f"  P95: {dists[int(len(dists)*0.95)]} | max: {dists[-1]}")

    # --- 5) locality temporal: caché simple de los últimos W tokens (hit rate) ---
    print(f"\n--- 5) hit rate de caché temporal (por capa: retener expertos de los últimos W tokens) ---")
    for W in [1, 4, 8, 32]:
        hits = 0; total = 0
        for layer in range(n_layers):
            cache = set()
            exps_layer = by_layer.get(layer, [])
            for i, exps in enumerate(exps_layer):
                for e in exps:
                    total += 1
                    if e in cache:
                        hits += 1
                # update cache con los expertos de este token (LRU aproximado por ventana)
                if i >= W:
                    # quitar los expertos del token i-W
                    for e in exps_layer[i-W]:
                        cache.discard(e)
                cache.update(exps)
        print(f"  W={W}: hit rate {hits/total*100:.1f}%  (→ tráfico {(1-hits/total)*8*n_layers*bpe_mb:.0f} MB/token)")

if __name__ == "__main__":
    main()
