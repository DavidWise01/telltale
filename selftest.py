#!/usr/bin/env python3
"""Verify-first self-test. Simulate side channels and prove the harness (1) reads
a leaky channel as SIGNAL for the probed secrets and NOISE for the held-out floor;
(2) reads a pure-noise channel as NOISE for everything (no false leak); (3) catches
a harness that feeds the channel the answer (held-out reads SIGNAL -> INVALID);
(4) refuses a run with no noise-floor arm; (5) sizes the threshold sanely. Seeded,
so it is deterministic. No network.
"""
from __future__ import annotations
from canary import make_probed, make_held_out
from registry import Registry
from channel import Channel
from harness import run_panel
from score import threshold, gate_false_positive

fails = 0
def check(cond, msg):
    global fails
    print(("ok  · " if cond else "FAIL· ") + msg)
    fails += 0 if cond else 1


def build(n_probed=3, n_held=3):
    reg = Registry()
    probed = [make_probed(channel="timing") for _ in range(n_probed)]
    held = [make_held_out() for _ in range(n_held)]
    for c in probed + held:
        reg.add(c)
    return reg, probed, held


# 1. A LEAKY channel: it has access to the probed secrets (a real leak), not the held-out.
reg, probed, held = build()
leaky = Channel(access_to=[c.value for c in probed], per_bit_accuracy=0.85, probes=15, seed=1)
v = run_panel(reg, leaky)
check(v["control_fpr"] == 0, f"held-out noise floor stays NOISE, FPR 0 (got {v['control_fpr']})")
check(len(v["certified_signals"]) == 3, f"all 3 probed secrets read as SIGNAL (got {len(v['certified_signals'])})")
check("CLEAN" in v["verdict"], "verdict CLEAN when the noise floor holds")
check(all(ag > v["threshold"] for _, ag in v["certified_signals"]), "each signal exceeds the threshold")

# 2. A PURE-NOISE channel (access to nothing): everything is NOISE, no false leak.
reg2, probed2, _ = build()
noise = Channel(access_to=[], per_bit_accuracy=0.85, probes=15, seed=2)
v2 = run_panel(reg2, noise)
check(len(v2["certified_signals"]) == 0, "a channel with no access reads all NOISE (no false signal)")
check(v2["control_fpr"] == 0, "noise channel: held-out floor also NOISE")

# 3. A CHEATING harness: the channel has access to EVERYTHING, including the held-out floor.
reg3, probed3, held3 = build()
cheat = Channel(access_to=[e["value"] for e in reg3.entries], per_bit_accuracy=0.85, probes=15, seed=3)
v3 = run_panel(reg3, cheat)
check(bool(v3["control_fpr"]) and v3["control_fpr"] > 0, f"held-out reads SIGNAL -> FPR>0 ({v3['control_fpr']})")
check("INVALID" in v3["verdict"], "cheating harness -> verdict INVALID")
check(len(v3["certified_signals"]) == 0, "invalid run certifies nothing")

# 4. Performative guard: no held-out noise floor -> INVALID.
reg4 = Registry()
for _ in range(3):
    reg4.add(make_probed())
leaky4 = Channel(access_to=[e["value"] for e in reg4.entries], per_bit_accuracy=0.85, probes=15, seed=4)
v4 = run_panel(reg4, leaky4)
check("INVALID" in v4["verdict"], "no noise-floor arm -> INVALID (performative guard)")

# 5. Threshold sanity: tau is above chance and the 5-sigma gate FP is tiny.
check(0.5 < threshold(128) < 0.9, f"threshold for 128 bits is a sane {threshold(128):.3f}")
check(gate_false_positive() < 1e-6, f"5-sigma per-marker false-positive is tiny ({gate_false_positive():.1e})")

print("\n" + ("SOME CHECKS FAILED" if fails else "all telltale-harness checks passed"))
raise SystemExit(1 if fails else 0)
