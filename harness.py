#!/usr/bin/env python3
"""Orchestrator: registry + a channel -> recover each secret -> score -> report.

The claim is statistical, not causal: a SIGNAL says 'the bits of this secret came
back off this channel far better than the noise floor allows' -- so the channel
carries information about it. It is a LEAD that a side channel leaks the secret;
it does not prove the mechanism (timing vs power vs cache) or that anyone is
exploiting it. Low-bandwidth, noisy, and easy to fool yourself with -- hence the
held-out noise floor on every run.
"""
from __future__ import annotations
from canary import to_bits
from registry import Registry
from channel import Channel, agreement
from score import score


def run_panel(registry: Registry, channel: Channel):
    results = []
    for e in registry.entries:
        true_bits = to_bits(e["value"])
        recovered = channel.read(true_bits, e["value"])
        results.append({
            "value": e["value"],
            "held_out": e["held_out"],
            "agreement": agreement(true_bits, recovered),
        })
    n_bits = len(to_bits(registry.entries[0]["value"])) if registry.entries else 128
    return score(results, n_bits=n_bits)


def report(v: dict) -> str:
    lines = [
        "# Telltale report", "", v["verdict"], "",
        f"held-out noise-floor : {v['held_out_n']}",
        f"control FPR          : {v['control_fpr']}",
        f"signal threshold tau : {v['threshold']:.3f}",
        f"gate base-rate (5-sigma): {v['base_rate']:.2e}",
        f"certified signals    : {len(v['certified_signals'])}",
    ]
    for val, ag in v["certified_signals"]:
        lines.append(f"  - {val[:16]}... agreement {ag:.3f}")
    return "\n".join(lines)
