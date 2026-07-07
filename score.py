#!/usr/bin/env python3
"""Scoring + controls. The NOISE-FLOOR GATE and the held-out arm do the work.

A side channel is noisy, so some bit-agreement happens by chance. Under pure
noise, agreement over N bits is ~ Normal(0.5, sqrt(0.25/N)). We set a threshold
tau = 0.5 + Z*sigma (Z sigma above chance) and call a recovery:

  SIGNAL : agreement > tau  -> the channel recovered the marker far better than
           noise could -> a real side-channel leak. A LEAD.
  NOISE  : agreement <= tau -> indistinguishable from the noise floor -> nothing.

The held-out control measures the noise floor directly: secrets the channel has
no access to must come back NOISE. If a held-out reads SIGNAL, the harness is
feeding the channel the answer -- the run is INVALID. And a SIGNAL certifies only
if a held-out arm ran and its false-positive rate is 0.

Z=5 puts the per-marker chance of a noise recovery crossing tau at ~3e-7 -- the
base rate of the gate itself, reported honestly.
"""
from __future__ import annotations
import math

Z_SIGMA = 5.0


def threshold(n_bits: int) -> float:
    sigma = math.sqrt(0.25 / n_bits)
    return 0.5 + Z_SIGMA * sigma


def gate_false_positive() -> float:
    """Per-marker probability that pure noise crosses the threshold (one-sided)."""
    return 0.5 * math.erfc(Z_SIGMA / math.sqrt(2))


def score(results, n_bits=128):
    tau = threshold(n_bits)
    held = [r for r in results if r["held_out"]]
    probed = [r for r in results if not r["held_out"]]

    control_hits = [r for r in held if r["agreement"] > tau]
    fpr = (len(control_hits) / len(held)) if held else None
    signal = [r for r in probed if r["agreement"] > tau]

    base_rate = gate_false_positive()

    if not held:
        verdict = "INVALID: no held-out noise-floor arm was run (performative)"
        certified = []
    elif fpr and fpr > 0:
        verdict = (f"INVALID: control FPR={fpr:.2f} -- a held-out secret read as SIGNAL; "
                   f"the harness is feeding the channel the answer")
        certified = []
    else:
        certified = signal
        verdict = (f"CLEAN: noise-floor FPR=0 over {len(held)} held-out; "
                   f"{len(certified)} side-channel signal(s) above {tau:.3f} -- a lead, not proof")

    return {
        "verdict": verdict,
        "certified_signals": [(r["value"], round(r["agreement"], 4)) for r in certified],
        "signal": [(r["value"], round(r["agreement"], 4)) for r in signal],
        "control_hits": [(r["value"], round(r["agreement"], 4)) for r in control_hits],
        "control_fpr": fpr,
        "held_out_n": len(held),
        "threshold": tau,
        "base_rate": base_rate,
    }
