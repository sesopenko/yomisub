"""Recording-local voice activity, independent of text or phrase ownership."""

from collections import Counter, defaultdict
from dataclasses import dataclass
from fractions import Fraction

from .domain import RawTiming, SampleInterval, Voice, VoiceTurn
from .ports import Scan, StageError


def read_rttm(text, uri, run, source, clock):
    turns = []
    if not isinstance(text, str):
        raise StageError("Speaker scan returned invalid RTTM.")
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        fields = line.split()
        if len(fields) != 10 or fields[0] != "SPEAKER":
            raise StageError("Speaker scan returned a malformed RTTM row.")
        if fields[1] != uri:
            continue
        try:
            start, duration = map(Fraction, fields[3:5])
        except (ValueError, ZeroDivisionError):
            raise StageError("Speaker scan returned invalid RTTM seconds.") from None
        if duration < 0 or fields[7] == "<NA>":
            raise StageError("Speaker scan returned an invalid duration or voice label.")
        end = start + duration
        left = max(0, source.recording_sample(start * source.sample_rate, clock))
        right = min(clock.frames, source.recording_sample(end * source.sample_rate, clock))
        interval = SampleInterval(clock, left, right) if left < right else None
        turns.append(VoiceTurn(f"{run.id}:turn{len(turns)}", Voice(run.id, fields[7]),
                               RawTiming(start, end, "seconds"), interval))
    return Scan(run, tuple(turns))


@dataclass(frozen=True)
class ActivitySpan:
    id: str
    interval: SampleInterval
    voices: tuple[Voice, ...]


def activity(scan, region):
    """Partition a candidate interval and coalesce adjacent equal active sets."""
    events = defaultdict(Counter)
    for turn in scan.turns:
        if turn.interval is None:
            continue
        left = max(region.start, turn.interval.start)
        right = min(region.end, turn.interval.end)
        if left < right:
            events[left][turn.voice] += 1
            events[right][turn.voice] -= 1
    spans = []
    active = Counter()
    previous = region.start
    for edge in sorted({region.start, region.end, *events}):
        if previous < edge:
            voices = tuple(sorted((v for v, n in active.items() if n > 0), key=lambda v: v.label))
            start = previous
            if spans and spans[-1].voices == voices:
                start = spans.pop().interval.start
            interval = SampleInterval(region.clock, start, edge)
            spans.append(ActivitySpan(f"{scan.run.id}:span:{start}:{edge}", interval, voices))
        active.update(events[edge])
        previous = edge
    return tuple(spans)


def overlap_cores(scan, clock):
    if not clock.frames:
        return ()
    return tuple(span for span in activity(scan, SampleInterval(clock, 0, clock.frames))
                 if len(span.voices) >= 2)


@dataclass(frozen=True)
class Coverage:
    per_voice: dict
    simultaneous: Fraction
    uncovered: Fraction


def coverage(scan, region):
    voices = Counter()
    shared = uncovered = Fraction(0)
    for span in activity(scan, region):
        duration = span.interval.end - span.interval.start
        for voice in span.voices:
            voices[voice] += duration
        if len(span.voices) > 1:
            shared += duration
        elif not span.voices:
            uncovered += duration
    return Coverage(dict(voices), shared, uncovered)
