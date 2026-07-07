#!/usr/bin/env python3
"""The side channel = Detection + Comparison.

A side channel recovers each bit of a secret with some per-bit accuracy p:
  p = 0.5  -> pure noise (the channel tells you nothing)
  p > 0.5  -> a leaky channel (each measurement is right more often than chance)

You take K independent measurements ("probes") and MAJORITY-VOTE each bit, which
sharpens a weak-but-real bias into a confident estimate. The recovered string is
then compared to the marker; `agreement` is the fraction of bits that match.

Critically, a channel that has NO access to a given secret recovers it at chance
(agreement ~ 0.5) no matter how many probes you take -- that is the noise floor
the held-out control measures.
"""
from __future__ import annotations
import random


def recover(true_bits, per_bit_accuracy, probes, rng, has_access=True):
    """Recover a bit-string from a simulated side channel.

    If has_access is False, the channel sees no signal and every measurement is a
    coin flip (accuracy 0.5) regardless of per_bit_accuracy -- the noise floor.
    Returns the recovered bits (majority vote over `probes` measurements).
    """
    acc = per_bit_accuracy if has_access else 0.5
    recovered = []
    for b in true_bits:
        votes = 0
        for _ in range(probes):
            measured = b if rng.random() < acc else (1 - b)
            votes += measured
        recovered.append(1 if votes * 2 > probes else 0)  # majority (ties -> 0)
    return recovered


def agreement(a, b):
    """Fraction of bits that match between two equal-length bit-strings."""
    if not a:
        return 0.0
    return sum(1 for x, y in zip(a, b) if x == y) / len(a)


class Channel:
    """A side channel under test. `access_to` is the set of marker values whose
    bits the channel can actually recover (a real leak); everything else it sees
    only as noise. `per_bit_accuracy` is how leaky it is when it does have access."""

    def __init__(self, access_to, per_bit_accuracy=0.85, probes=15, name="timing", seed=0):
        self.access = set(access_to)
        self.p = per_bit_accuracy
        self.probes = probes
        self.name = name
        self.rng = random.Random(seed)

    def read(self, canary_bits, value):
        return recover(canary_bits, self.p, self.probes, self.rng,
                       has_access=(value in self.access))
