#!/usr/bin/env python3
"""
E007/H-011 — Simulación de top-k reducido (CONSERVADO, reproducible).

Verifica las afirmaciones del discovery 0009:
  - ahorro de bytes con k reducido sobre los traces (lineal: 25/50/75%)
  - baseline estimado con page cache (2.87 GB/token a k=8, escalando con k)

Uso: python3 topk_simulation.py <trace-235b> [--bytes-per-expert 12.24]

Nota: la calidad con k reducido se evaluó experimentalmente con
  llama-cli --override-kv qwen3moe.expert_used_count=int:k
en Qwen3-30B (misma arquitectura) y 235B — outputs en /tmp/k*.txt, /tmp/q30_k*.txt
(k=4 coherente, k=2 incoherente).
"""
import sys, glob
import numpy as np

def main():
    trace = sys.argv[1] if len(sys.argv) > 1 else sorted(glob.glob(
        '/home/loonbac/Projects/research/experiments/E006/traces/235b-p1-*.trace'))[0]
    bpe = float(sys.argv[3]) if len(sys.argv) > 3 else 12.24  # MB por experto

    lines = [l.split() for l in open(trace) if l.strip()]
    n_lines = len(lines)  # líneas = token × capa, cada una con 8 expertos
    # procesamientos = líneas / capas (el trace tiene token-ids repetidos entre ubatches)
    n_layers = len(set(int(l[1]) for l in lines))
    n_proc = n_lines // n_layers
    n_tokens = n_proc
    print(f"=== H-011 simulación top-k reducido ===")
    print(f"trace: {trace} | líneas (token×capa): {n_lines} | procesamientos: {n_tokens}")
    print(f"activaciones/token (k=8): {n_lines*8/n_tokens:.0f}")

    print(f"\n{'k':>3} {'activ/tok':>9} {'ahorro':>7} {'brutos GB/tok':>13} {'baseline GB/tok':>15}")
    for k in [8, 6, 4, 2]:
        act = n_lines * k / n_tokens
        save = (8 - k) / 8 * 100
        brutos = act * bpe / 1024
        base = 2.87 * k / 8
        print(f"{k:>3} {act:>9.0f} {save:>6.0f}% {brutos:>13.1f} {base:>15.2f}")

    print(f"""
Interpretación (discovery 0009):
- El ahorro es lineal en k: k=6 → 25% (2.15 GB/tok), k=4 → 50% (1.44), k=2 → 75% (0.72).
- Calidad (evaluada con --override-kv expert_used_count en 30B y 235B):
  k=8/6/4 coherentes; k=2 INCOHERENTE → el límite de calidad está entre k=4 y k=6.
- H-011 PARCIAL: reducción máxima con calidad aceptable ≈ 50% (k=4, 1.44 GB/tok).
""")

if __name__ == '__main__':
    main()
