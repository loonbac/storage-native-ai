#!/usr/bin/env python3
"""
E006.1 + E006.4 — Simulador de caché de expertos sobre traces reales.

Uso: python3 -u cache_simulator.py <trace...> --bytes-per-expert MB --capacities "GB,..."

Métricas (definición operacional):
  - unidad de caché: (layer, expert), pesa bytes_per_expert
  - secuencia: tokens; cada token activa k×n_layers unidades
  - SEMÁNTICA POR-TOKEN: al inicio del token se cuentan los misses (activados no residentes);
    los faltantes se leen (tráfico) y se insertan; la eviction solo ocurre para hacer espacio,
    nunca dentro del token sobre unidades ya residentes.
  - tráfico NVMe/token = n_misses × bytes_per_expert
  - hit rate = 1 − misses/activaciones

Políticas:
  - oracle: Belady MIN (heap lazy). LÍMITE TEÓRICO de cualquier política.
  - lru: Least Recently Used (dict + move_to_end, O(1))
  - lfu: Least Frequently Used (heap lazy por (count, last_use))
"""
import sys, argparse, heapq
from collections import defaultdict, OrderedDict

def load_trace(path):
    """Reconstruye tokens-procesamiento: grupo de líneas con el mismo token-id cubriendo ≥2 capas."""
    seq = []
    cur = None
    last_tok = None
    layers_seen = 0
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
                layers_seen = 1
                last_tok = tok
            else:
                cur.extend((layer, e) for e in exps)
                layers_seen += 1
    if cur is not None and layers_seen >= 2:
        seq.append(cur)
    return seq

class LRU:
    def __init__(self, cap):
        self.cap = cap
        self.cache = OrderedDict()
    def access_token(self, units):
        miss = [u for u in units if u not in self.cache]
        for u in miss:
            if len(self.cache) >= self.cap:
                # evictar el más antiguo (primera clave)
                self.cache.pop(next(iter(self.cache)))
            self.cache[u] = None
        for u in units:
            if u in self.cache:
                self.cache.move_to_end(u)
        return len(miss), len(units)

class LFU:
    def __init__(self, cap):
        self.cap = cap
        self.cache = {}
        self.count = defaultdict(int)
        self.last = {}
        self.heap = []  # (count, last_use, unit) lazy
        self.clock = 0
    def access_token(self, units):
        miss = [u for u in units if u not in self.cache]
        for u in miss:
            if len(self.cache) >= self.cap:
                while self.heap:
                    c, lu, hu = self.heap[0]
                    if hu in self.cache and self.count[hu] == c and self.last[hu] == lu:
                        break
                    heapq.heappop(self.heap)
                if self.heap:
                    _, _, hu = heapq.heappop(self.heap)
                    del self.cache[hu]
            self.cache[u] = None
            self.count[u] += 1
            self.last[u] = self.clock
            heapq.heappush(self.heap, (self.count[u], self.last[u], u))
            self.clock += 1
        for u in units:
            if u in self.cache:
                self.count[u] += 1
                self.last[u] = self.clock
                heapq.heappush(self.heap, (self.count[u], self.last[u], u))
                self.clock += 1
        return len(miss), len(units)

def oracle_sim(seq, capacity):
    """Belady MIN con heap lazy: evictar el de próximo uso más lejano."""
    use_positions = defaultdict(list)
    pos = 0
    for tok in seq:
        for u in tok:
            use_positions[u].append(pos)
            pos += 1
    for u in use_positions:
        use_positions[u].reverse()
    cache = {}
    heap = []
    misses = 0
    total = 0
    for tok in seq:
        total += len(tok)
        unique = set(tok)
        for u in unique:
            if u not in cache:
                misses += 1
        for u in unique:
            nu = use_positions[u][-1] if use_positions[u] else float('inf')
            if u not in cache:
                if len(cache) >= capacity:
                    while heap:
                        hn, hu = heap[0]
                        if hu in cache and cache[hu] == hn:
                            break
                        heapq.heappop(heap)
                    if heap:
                        hn, hu = heapq.heappop(heap)
                        del cache[hu]
                cache[u] = nu
            else:
                cache[u] = nu
            heapq.heappush(heap, (nu, u))
            if use_positions[u]:
                use_positions[u].pop()
    return misses, total

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('traces', nargs='+')
    ap.add_argument('--bytes-per-expert', type=float, default=2.92)
    ap.add_argument('--capacities', type=str, default="1,4,8,12,20,32,44,64")
    args = ap.parse_args()

    seq_all = []
    for t in args.traces:
        seq_all.extend(load_trace(t))
    n_proc = len(seq_all)
    bpe = args.bytes_per_expert
    caps_gb = [float(x) for x in args.capacities.split(',')]
    n_per_tok = len(seq_all[0]) if seq_all else 0

    print(f"=== cache simulator ===")
    print(f"traces: {len(args.traces)} | tokens-procesamiento: {n_proc} | activaciones/token: {n_per_tok}")
    print(f"bytes/experto: {bpe:.2f} MB | modelo de expertos: {n_per_tok//8*128*bpe/1024:.1f} GB")

    print(f"\n{'Cap':>5} {'#unid':>6} | {'ORACLE':>11} {'hit%':>6} | {'LRU':>11} {'hit%':>6} | {'LFU':>11} {'hit%':>6}")
    for cap_gb in caps_gb:
        cap_units = int(cap_gb * 1024 / bpe)
        om, ot = oracle_sim(seq_all, cap_units)
        lru = LRU(cap_units); lfu = LFU(cap_units)
        lm = lt = 0; fm = ft = 0
        for tok in seq_all:
            a, b = lru.access_token(tok); lm += a; lt += b
            a, b = lfu.access_token(tok); fm += a; ft += b
        def f(m, t):
            return f"{m*bpe/n_proc:8.1f}MB {100*(1-m/t):5.1f}%"
        print(f"{cap_gb:>4.0f}G {cap_units:>6} | {f(om, ot):>11} | {f(lm, lt):>11} | {f(fm, ft):>11}")

    print(f"\nReferencias: 12 GB = {int(12*1024/bpe)} unid (VRAM); 44 GB = {int(44*1024/bpe)} (VRAM+RAM)")
    print(f"Objetivo: 37.5 MB/token desde almacenamiento")

if __name__ == '__main__':
    main()
