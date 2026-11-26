"""Validation of observed source-local times on the recording clock."""

from fractions import Fraction

from .domain import SampleInterval


def anchored_interval(timing, source, clock):
    if timing.start is None or timing.end is None:
        return None
    scale = {"milliseconds": Fraction(source.sample_rate, 1000),
             "seconds": source.sample_rate, "samples": 1}[timing.unit]
    left, right = timing.start * scale, timing.end * scale
    if not source.leading_padding <= left < right <= source.frames - source.trailing_padding:
        return None
    a, b = (source.recording_sample(x, clock) for x in (left, right))
    return SampleInterval(clock, a, b) if 0 <= a < b <= clock.frames else None
