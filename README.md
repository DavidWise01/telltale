# telltale — did your marker leak through a side channel

A membership-detection harness for the **side-channel membrane**. Its siblings
catch your marker as text — published, in the weights, relayed, emitted by live
inference, or escaped from an enclave. telltale catches the one that is **never
text at all**: your marker reconstructed, one noisy bit at a time, from a covert
physical channel — token latency, power draw, cache timing, response length. A
*tell* is a sign you didn't mean to give.

## Why it's statistical, not exact-match

A side channel is **low-bandwidth and noisy**, so the exact string never appears.
The honest question isn't "did the marker show up" — it's **"do the recovered bits
agree with the marker far more than chance allows."**

- The channel recovers each bit with accuracy `p` (`0.5` = pure noise, `> 0.5` =
  leaky). You take `K` measurements and **majority-vote** each bit, sharpening a
  weak bias into a confident estimate.
- Under pure noise, agreement over `N` bits is `~ Normal(0.5, √(0.25/N))`. The
  gate sets a threshold `τ = 0.5 + 5·σ`. Agreement **above** `τ` is a **SIGNAL**;
  at or below is **NOISE**.

## The controls

1. **The noise floor (held-out).** Secrets the channel has no access to, recovered
   the same way. They must come back NOISE. If a held-out reads SIGNAL, the harness
   is feeding the channel the answer — the run is INVALID.
2. **The 5-σ gate.** A SIGNAL must beat chance by five sigma; the per-marker odds of
   pure noise crossing `τ` are `~3×10⁻⁷`, reported honestly as the gate's base rate.
3. **A lead, not proof.** A SIGNAL says the channel *carries information* about the
   marker — not which mechanism (timing / power / cache), and not that anyone is
   exploiting it.

## Files

| File | Closure-Loop layer | Role |
|------|--------------------|------|
| `canary.py` | Detection | 128-bit secrets, as bits |
| `registry.py` | Anchoring | probed secrets + the held-out noise floor |
| `channel.py` | Comparison | a simulated side channel: recover bits by majority vote |
| `score.py` | Witness | the noise-floor gate, the 5-σ threshold, certification |
| `harness.py` | Lineage | recover each secret → score; a statistical claim, not causal |
| `selftest.py` | — | seeded leaky/noise/cheating channels, no network |

## Verify first

```bash
python selftest.py
```

Proves, no network: a leaky channel reads the probed secrets as SIGNAL and the
held-out floor as NOISE (FPR 0); a pure-noise channel reads everything NOISE (no
false leak); a channel that also sees the held-out floor spikes FPR and the run is
refused; a run with no noise floor is refused; and the 5-σ threshold is sane.

## What a certified signal does and does not mean

Does: the bits of a marker came back off a channel **far better than the noise floor
allows**, with a held-out floor proving the channel isn't just handed the answer. The
channel **carries information** about your marker.

Does not: prove the mechanism, prove exploitation, or prove theft. Side channels are
real but noisy and low-bandwidth; this is a corroborable **lead**, and a negative
means little.

## Honest limits

- **A simulation, honestly labeled.** The channel here is modelled (per-bit accuracy
  + majority vote); against a real system you supply real measurements.
- **The noise floor is the whole safeguard** — never run without it, or you will read
  signal in noise.
- This is the **side-channel** membrane only. See the membrane map for the others.

---
David Lee Wise / ROOT0 / TriPod LLC · CC-BY-ND-4.0
