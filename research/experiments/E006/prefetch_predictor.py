#!/usr/bin/env python3
"""
E006.5 — Prefetch predictivo: predictor + accuracy + efecto en tráfico.

Uso: python3 -u prefetch_predictor.py <trace...> --bytes-per-expert MB --capacities "GB,..."

Predictores (por capa, predicen los expertos del token t+1 dados los anteriores):
  - last:    los expertos del token anterior (locality temporal inmediata)
  - window:  los top-K expertos más frecuentes en la ventana de los últimos W tokens
  - bigram:  para cada experto del token actual, los que más frecuentemente lo SUCEDEN (co-ocurrencia)

Métricas:
  - precision: de los expertos pre-cargados, cuántos realmente se activan en t+1
  - recall:    de los expertos activados en t+1, cuántos fueron pre-cargados
  - tráfico NVMe/token con LRU+prefetch: lecturas de prefetch (aciertos y fallos) + misses de activación
    (un experto pre-cargado que se activa evita un miss; uno que no, es tráfico desperdiciado)
"""
import sys, argparse, heapq
from collections import defaultdict, Counter, deque, OrderedDict

def load_trace(path):
    seq = []
    cur = None; last_tok = None; layers_seen = 0
    with open(path) as f:
        for ln in f:
            p = ln.split()
            if len(p) < 4: continue
            tok, layer, k = int(p[0]), int(p[1]), int(p[2])
            exps = [int(x) for x in p[3:3+k]]
            if tok != last_tok or (layer == 0 and cur is not None and layers_seen > 1):
                if cur is not None and layers_seen >= 2:
                    seq.append(cur)
                cur = [(layer, e) for e in exps]
                layers_seen = 1; last_tok = tok
            else:
                cur.extend((layer, e) for e in exps)
                layers_seen += 1
    if cur is not None and layers_seen >= 2:
        seq.append(cur)
    return seq

def train_bigrams(seq, n_layers):
    """bigrams por capa: (prev_expert_set) -> Counter de expertos siguientes."""
    big = [defaultdict(Counter) for _ in range(n_layers)]
    prev = [None] * n_layers
    for tok in seq:
        cur = defaultdict(set)
        for layer, e in tok:
            cur[layer].add(e)
        for layer in range(n_layers):
            s = frozenset(cur.get(layer, ()))
            if prev[layer] is not None and s:
                big[layer][prev[layer]].update(s)
            if s:
                prev[layer] = s
    return big

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('traces', nargs='+')
    ap.add_argument('--bytes-per-expert', type=float, default=11.42)
    ap.add_argument('--capacities', type=str, default="12,44")
    ap.add_argument('--window', type=int, default=8)
    ap.add_argument('--k', type=int, default=16)  # expertos a pre-cargar por capa
    args = ap.parse_args()

    seq_all = []
    for t in args.traces:
        seq_all.extend(load_trace(t))
    n_proc = len(seq_all)
    n_layers = len(seq_all[0]) // 8
    bpe = args.bytes_per_expert
    K = args.k
    W = args.window

    # --- accuracy de los predictores ---
    print(f"=== E006.5 prefetch predictor ===")
    print(f"tokens: {n_proc} | capas: {n_layers} | prefetch K={K} expertos/capa | ventana W={W}")

    # por capa: secuencia de sets de expertos por token
    by_layer = defaultdict(list)
    for tok in seq_all:
        cur = defaultdict(set)
        for layer, e in tok:
            cur[layer].add(e)
        for layer in range(n_layers):
            by_layer[layer].append(cur.get(layer, set()))

    bigrams = train_bigrams(seq_all, n_layers)

    # baseline last-token
    acc = {'last': {'tp': 0, 'pred': 0, 'act': 0}, 'window': {'tp': 0, 'pred': 0, 'act': 0}, 'bigram': {'tp': 0, 'pred': 0, 'act': 0}}
    for layer in range(n_layers):
        wins = deque()
        prev_set = None
        for i, s in enumerate(by_layer[layer]):
            # predicciones para token i (a partir del 2º)
            if i > 0:
                # last
                pred_last = prev_set
                # window: top-K por frecuencia en ventana
                cnt = Counter()
                for w in wins: cnt.update(w)
                pred_window = set(x for x, _ in cnt.most_common(K))
                # bigram
                pred_bigram = set()
                if prev_set:
                    for e in prev_set:
                        for e2, c in bigrams[layer][frozenset(prev_set)].most_common(K // max(1, len(prev_set)) + 1):
                            pred_bigram.add(e2)
                for name, pred in [('last', pred_last), ('window', pred_window), ('bigram', pred_bigram)]:
                    acc[name]['pred'] += len(pred)
                    acc[name]['act'] += len(s)
                    acc[name]['tp'] += len(pred & s)
            # actualizar estado
            prev_set = s
            wins.append(s)
            if len(wins) > W: wins.popleft()

    print(f"\n--- accuracy (por capa, promedio sobre {n_proc} tokens) ---")
    for name in ['last', 'window', 'bigram']:
        a = acc[name]
        prec = a['tp'] / a['pred'] if a['pred'] else 0
        rec = a['tp'] / a['act'] if a['act'] else 0
        print(f"  {name:7s}: precision {prec*100:5.1f}% | recall {rec*100:5.1f}% | expertos/capa predichos {a['pred']/n_proc:.1f}")

    # --- tráfico con LRU+prefetch (best predictor) vs LRU puro ---
    print(f"\n--- tráfico NVMe/token: LRU puro vs LRU+prefetch (last) ---")
    for cap_gb in [float(x) for x in args.capacities.split(',')]:
        cap = int(cap_gb * 1024 / bpe)
        # LRU puro
        cache = OrderedDict()
        misses = 0
        for tok in seq_all:
            for layer, e in tok:
                if (layer, e) not in cache:
                    misses += 1
                    if len(cache) >= cap:
                        cache.pop(next(iter(cache)))
                cache[(layer, e)] = None
                cache.move_to_end((layer, e))
        # LRU + prefetch last-token: pre-cargar los expertos del token anterior (por capa)
        cache2 = OrderedDict()
        misses2 = 0
        prefetch_reads = 0
        prev_tok_exps = None
        for tok in seq_all:
            # prefetch: cargar los expertos del token anterior que no estén (por capa)
            if prev_tok_exps is not None:
                for layer, e in prev_tok_exps:
                    if (layer, e) not in cache2:
                        prefetch_reads += 1
                        if len(cache2) >= cap:
                            cache2.pop(next(iter(cache2)))
                        cache2[(layer, e)] = None
            # acceder el token actual
            for layer, e in tok:
                if (layer, e) not in cache2:
                    misses2 += 1
                    if len(cache2) >= cap:
                        cache2.pop(next(iter(cache2)))
                    cache2[(layer, e)] = None
                cache2[(layer, e)] = None
                cache2.move_to_end((layer, e))
            prev_tok_exps = set(tok)
        m1 = misses * bpe / n_proc
        m2 = (misses2 + prefetch_reads) * bpe / n_proc
        print(f"  {cap_gb:.0f}GB: LRU {m1:8.1f} MB/token | LRU+prefetch {m2:8.1f} MB/token "
              f"({'mejor' if m2 < m1 else 'peor'} por {(abs(m2-m1)/m1*100):.1f}%)")

if __name__ == '__main__':
    main()
