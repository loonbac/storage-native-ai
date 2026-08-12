#!/usr/bin/env python3
"""
E007/H-008 — Codebook k-means sobre pesos Q4 (CONSERVADO, reproducible).

Verifica: ¿puede un codebook comprimir los pesos Q4 con pérdida aceptable?
Resultado: NO — los Q4 ya tienen 16 niveles (4.8 bits); un codebook de <16 niveles
pierde precisión (RMS 8.1% del std a 5 bits) y uno de más niveles no comprime.
Uso: python3 codebook_analysis.py <gguf-shard1>
"""
import sys
import numpy as np
from weight_analysis import dequantize_rows, GGUFReader

def main():
    path = sys.argv[1]
    r = GGUFReader(path)
    data = r.data
    t = [t for t in r.tensors if 'blk.9.ffn_gate_exps' in t.name][0]
    erb = t.shape[1]; rb = (t.shape[0] // 256) * 144
    v = dequantize_rows(data, t.data_offset + 45 * erb * rb, 200)
    v = v[np.isfinite(v)]
    print(f"gate capa 9 experto 45: {len(v)} valores, std={v.std():.4f}")
    rng = np.random.RandomState(0)
    sample = v[rng.choice(len(v), 50000, replace=False)].astype(np.float32)
    for nb in [32, 128]:
        centroids = sample[rng.choice(len(sample), nb, replace=False)].copy()
        for _ in range(8):
            d2 = np.abs(sample[:, None] - centroids[None, :])
            labels = np.argmin(d2, axis=1)
            for c in range(nb):
                m = labels == c
                if m.sum() > 0:
                    centroids[c] = sample[m].mean()
        err = np.sqrt(((sample - centroids[labels])**2).mean())
        bits = np.log2(nb)
        print(f"  {nb} bins ({bits:.1f} bits vs Q4 4.8): RMS={err:.5f} "
              f"({err/v.std()*100:.1f}% del std) | compresión {4.8/bits:.2f}×")

if __name__ == '__main__':
    main()
