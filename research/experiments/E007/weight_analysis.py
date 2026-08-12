#!/usr/bin/env python3
"""
E007 — Análisis de pesos de expertos (H-007 sparsity + H-008 compressibilidad) v3.

CONSERVADO — reproduce las cifras finales del ciclo 3 (2026-08-11, tras corrección
de la auditoría). Dequantización Q4_K con layout ggml b10333 (d+0, dmin+2, scales+4,
qs+16), validada con token_embd (~0.005% ceros exactos).

Mide sobre el Qwen3-235B (shard 1, capas 0-18):
  1) sparsity por CAPA (ceros exactos y filas muertas del gate) — la sparsity es
     dependiente de la capa (capa 0 ~36%, capas medias <2%); la media ponderada del
     shard es ~4.5% (NO 36.5%).
  2) entropía de los nibbles qs (límite de compresión sin pérdida).
  3) control token_embd (ceros exactos tras dequantización).
  4) SVD del gate del experto más vivo (rango efectivo).

FALSACIONES (escritas ANTES):
  H-007: si la sparsity promedio del modelo (media por capa) < 10% → el skipping de
  filas muertas reduce <7% de los bytes → H-007 REFUTADA (la sparsity no es
  explotable a nivel de modelo; la capa 0 es una anomalía de entrenamiento).
  H-008: si el lossless (de la entropía) < 25% → la compresión sin entrenamiento no
  alcanza ni 2.87→2.2 GB/token de forma significativa → H-008 REFUTADA (el lossless
  es marginal; SeedLM requiere retrain).
"""
import sys
import numpy as np
from gguf import GGUFReader

def get_scale_min_k4(j, scales):
    if j < 4:
        return scales[j] & 63, scales[j + 4] & 63
    return (scales[j + 4] & 0xF) | ((scales[j - 4] >> 6) << 4), (scales[j + 4] >> 4) | ((scales[j] >> 6) << 4)

def deq_q4k_block(qs, scales, d_raw, dmin_raw):
    import struct
    d = np.frombuffer(struct.pack('<H', d_raw), dtype=np.float16)[0].astype(np.float32)
    dmin = np.frombuffer(struct.pack('<H', dmin_raw), dtype=np.float16)[0].astype(np.float32)
    out = np.empty(256, dtype=np.float32)
    is_ = 0
    for j in range(0, 256, 64):
        s0, m0 = get_scale_min_k4(is_ + 0, scales)
        s1, m1 = get_scale_min_k4(is_ + 1, scales)
        out[j:j+32] = d * s0 * (qs[:32] & 0x0F) - dmin * m0
        out[j+32:j+64] = d * s1 * (qs[:32] >> 4) - dmin * m1
        qs = qs[32:]
        is_ += 2
    return out

def dequantize_rows(data, offset, n_rows, row_vals=4096):
    """Dequantiza n_rows filas de row_vals valores desde offset. Layout b10333."""
    bpr = row_vals // 256
    row_bytes = bpr * 144
    out = np.empty(n_rows * row_vals, dtype=np.float32)
    for r in range(n_rows):
        base = offset + r * row_bytes
        for b in range(bpr):
            bb = base + b * 144
            d_raw = np.frombuffer(data, dtype=np.uint16, count=1, offset=bb + 0)[0]
            dmin_raw = np.frombuffer(data, dtype=np.uint16, count=1, offset=bb + 2)[0]
            scales = np.frombuffer(data, dtype=np.uint8, count=12, offset=bb + 4)
            qs = np.frombuffer(data, dtype=np.uint8, count=128, offset=bb + 16)
            out[r*row_vals + b*256 : r*row_vals + (b+1)*256] = deq_q4k_block(qs, scales, d_raw, dmin_raw)
    return out

def entropy_of_qs(data, offset, n_bytes_qs):
    """Entropía de los nibbles qs (4 bits) — límite de compresión SIN pérdida de los quants."""
    raw = np.frombuffer(data, dtype=np.uint8, count=n_bytes_qs, offset=offset)
    nib = np.concatenate([raw & 0x0F, raw >> 4])
    hist = np.bincount(nib, minlength=16).astype(float)
    hist = hist[hist > 0]
    p = hist / hist.sum()
    H = -np.sum(p * np.log2(p))
    return H, p[0] if len(p) > 0 else 0  # H, prob del nibble 0

def main():
    path = sys.argv[1]
    r = GGUFReader(path)
    data = r.data
    print(f"=== E007 v3 (conservado) — análisis de pesos ===")
    print(f"shard: {path.split('/')[-1]} | tensores: {len(r.tensors)}")

    # 0) CONTROL: token_embd (ceros exactos tras dequantización)
    emb = [t for t in r.tensors if 'token_embd' in t.name][0]
    v_emb = dequantize_rows(data, emb.data_offset, 20)
    print(f"\n[CONTROL] token_embd: ceros exactos = {(v_emb == 0).mean()*100:.4f}% | std={v_emb.std():.4f}")
    print(f"  (esperado ~0.005% — si fuera alto, la dequantización estaría mal)")

    # 1) sparsity por capa (gate, 128 expertos, 30 filas c/u)
    gate_tensors = sorted([t for t in r.tensors if 'ffn_gate_exps' in t.name],
                          key=lambda t: int(t.name.split('.')[1]))
    print(f"\n=== 1) sparsity del gate por capa (shard 1, {len(gate_tensors)} capas) ===")
    zeros_by_layer = []
    for t in gate_tensors:
        layer = int(t.name.split('.')[1])
        erb = t.shape[1]; rb = (t.shape[0] // 256) * 144
        zs = []
        for e in range(128):
            v = dequantize_rows(data, t.data_offset + e * erb * rb, 30)
            zs.append((v == 0).mean())
        zeros_by_layer.append(np.mean(zs))
        print(f"  capa {layer:>3}: {np.mean(zs)*100:6.2f}%")
    zeros_by_layer = np.array(zeros_by_layer)
    mean_sparsity = zeros_by_layer.mean()
    print(f"  MEDIA PONDERADA (shard 1): {mean_sparsity*100:.2f}%")
    print(f"  capa 0: {zeros_by_layer[0]*100:.2f}% | capas medias: {zeros_by_layer[4:].mean()*100:.2f}%")

    # 2) entropía de los nibbles qs (gate, capa 0 y capa 9 — comparativa)
    print(f"\n=== 2) entropía de nibbles qs (compresión sin pérdida máx) ===")
    for layer in [0, 9]:
        t = [t for t in gate_tensors if f'blk.{layer}.ffn_gate_exps' in t.name][0]
        erb = t.shape[1]; rb = (t.shape[0] // 256) * 144
        # 100 filas del experto 45 (vivo) -> bytes qs = 100 * rb * (128/144)
        qs_bytes_per_row = rb * 128 // 144
        H, p0 = entropy_of_qs(data, t.data_offset + 45 * erb * rb, 100 * qs_bytes_per_row)
        print(f"  capa {layer} gate: H = {H:.3f} bits/valor (de 4) → lossless máx {(4-H)/4*100:.1f}% | P(nibble 0)={p0*100:.1f}%")

    # 3) SVD del gate del experto más vivo de la capa 0
    print(f"\n=== 3) SVD gate experto 45 (capa 0, filas vivas) ===")
    t0 = [t for t in gate_tensors if 'blk.0.ffn_gate_exps' in t.name][0]
    erb = t0.shape[1]; rb = (t0.shape[0] // 256) * 144
    vg = dequantize_rows(data, t0.data_offset + 45 * erb * rb, 1536).reshape(1536, 4096)
    ng = np.linalg.norm(vg, axis=1); med = np.median(ng[ng > 0])
    live = ng >= 0.01 * med
    Wl = vg[live].T
    s = np.linalg.svd(Wl, compute_uv=False)
    s2 = s**2; cum = np.cumsum(s2) / s2.sum()
    k99 = int(np.searchsorted(cum, 0.99)) + 1
    print(f"  filas vivas: {live.sum()}/1536 | rango 99% energía: {k99}/{len(s)} ({k99/len(s)*100:.1f}%)")

    # 4) FALSACIONES
    print(f"\n=== FALSACIONES ===")
    red = 2 * mean_sparsity / 3  # skipping de filas muertas: gate+up = 2/3 del FFN
    print(f"H-007: sparsity media {mean_sparsity*100:.2f}% → reducción de bytes FFN ≈ {red*100:.1f}%")
    print(f"  {'<10% → H-007 REFUTADA (la capa 0 es anomalía; el modelo no es esparso)' if mean_sparsity < 0.10 else '≥10% → PARCIAL'}")
    # Falsación H-008: usar la entropía de la capa Densa (9) — representativa del modelo.
    # La capa 0 (36.5% sparsity) es una anomalía y NO debe decidir el veredicto.
    t9 = [t for t in gate_tensors if 'blk.9.ffn_gate_exps' in t.name][0]
    erb9 = t9.shape[1]; rb9 = (t9.shape[0] // 256) * 144
    qs_bpr9 = rb9 * 128 // 144
    H9, _ = entropy_of_qs(data, t9.data_offset + 45 * erb9 * rb9, 100 * qs_bpr9)
    lossless9 = (4 - H9) / 4
    print(f"H-008: entropía capa densa 9 = {H9:.3f} bits → lossless máx {lossless9*100:.1f}%")
    print(f"  {'<25% → H-008 REFUTADA (compresión sin retrain marginal)' if lossless9 < 0.25 else '≥25% → revisar'}")

if __name__ == '__main__':
    main()
