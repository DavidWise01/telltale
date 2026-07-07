#!/usr/bin/env python3
"""Canary generation + anchor records for the TELLTALE harness.

TELLTALE watches the SIDE-CHANNEL membrane: your marker recovered NOT from any
text a model emitted, but from a covert physical channel -- token latency, power
draw, cache timing, response length. The marker is never output verbatim; it is
RECONSTRUCTED, one noisy bit at a time, from measurements. A tell is a sign you
did not mean to give.

Because a side channel is low-bandwidth and NOISY, the honest question is not
"did the exact string appear" (it never does) but "do the recovered bits agree
with the marker far more than chance allows". So a canary here is just a 128-bit
secret; the work is statistical.

  exposure:
    "probed"   : a real secret whose bits you try to recover from the channel.
    "held_out" : a secret you recover the SAME way but never planted in the
                 system under test -- the NOISE FLOOR. It must come back at
                 chance (~50% bit agreement). If it reads as signal, the harness
                 is cheating and the run is invalid.
"""
from __future__ import annotations
import secrets, hashlib
from dataclasses import dataclass

ENTROPY_BITS = 128
HEX_LEN = ENTROPY_BITS // 4        # 32 hex chars


def new_value(bits: int = ENTROPY_BITS) -> str:
    return secrets.token_hex(bits // 8)


def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def to_bits(hex_value: str) -> list[int]:
    """The marker as a list of 0/1 bits (MSB first)."""
    n = int(hex_value, 16)
    width = len(hex_value) * 4
    return [(n >> (width - 1 - i)) & 1 for i in range(width)]


@dataclass
class Canary:
    value: str
    exposure: str = "probed"          # probed | held_out
    channel: str = ""                 # which side channel (timing / power / cache)
    context: str = ""
    kind: str = "canary"

    def __post_init__(self):
        self.canonical = f"{self.kind}|{self.value}|{self.exposure}"
        self.hash = "sha256:" + sha256_hex(self.canonical)

    @property
    def held_out(self) -> bool:
        return self.exposure == "held_out"

    @property
    def bits(self) -> list[int]:
        return to_bits(self.value)

    def anchor(self) -> dict:
        return {
            "primitive": self.kind, "canonical": self.canonical, "hash": self.hash,
            "value": self.value, "exposure": self.exposure, "held_out": self.held_out,
            "channel": self.channel, "context": self.context,
        }


def make_probed(channel="timing", context="", value=None) -> Canary:
    return Canary(value or new_value(), exposure="probed", channel=channel, context=context)


def make_held_out(context="noise-floor") -> Canary:
    return Canary(new_value(), exposure="held_out", context=context)
