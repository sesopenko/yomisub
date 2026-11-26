"""Recording-local evidence and editorial values shared by generation and replay."""

from dataclasses import dataclass
from fractions import Fraction
from typing import Literal


@dataclass(frozen=True)
class SelectedStream:
    index: int
    audio_ordinal: int
    language: str
    channel_layout: str


@dataclass(frozen=True)
class RecordingClock:
    """Sample zero is the first retained frame of the selected audio stream."""

    sample_rate: int
    frames: int
    playback_offset: Fraction
    playback_duration: Fraction

    def __post_init__(self):
        if self.sample_rate <= 0 or self.frames < 0 or self.playback_duration < 0:
            raise ValueError("Invalid recording clock")

    def playback_time(self, sample: Fraction | int) -> Fraction:
        return self.playback_offset + Fraction(sample, self.sample_rate)


@dataclass(frozen=True)
class AudioSource:
    """Origin is in recording samples. Padding and delay are in local frames."""

    id: str
    parent_id: str | None
    sample_rate: int
    frames: int
    origin: Fraction = Fraction(0)
    leading_padding: int = 0
    trailing_padding: int = 0
    delay: int = 0
    column: int | None = None

    def __post_init__(self):
        if self.sample_rate <= 0 or min(self.frames, self.leading_padding, self.trailing_padding) < 0:
            raise ValueError("Invalid source dimensions")
        if self.leading_padding + self.trailing_padding > self.frames:
            raise ValueError("Padding exceeds source length")

    def recording_sample(self, frame: int | Fraction, clock: RecordingClock) -> Fraction:
        local = frame - self.leading_padding - self.delay
        return self.origin + Fraction(local * clock.sample_rate, self.sample_rate)


@dataclass(frozen=True)
class RawTiming:
    """Unmodified endpoints on the source clock, including unusable observations."""

    start: Fraction | None
    end: Fraction | None
    unit: Literal["milliseconds", "seconds", "samples"]


@dataclass(frozen=True)
class SampleInterval:
    """A positive half-open interval measured on the recording clock."""

    clock: RecordingClock
    start: Fraction
    end: Fraction

    def __post_init__(self):
        if not 0 <= self.start < self.end <= self.clock.frames:
            raise ValueError("Interval exceeds recording bounds or has unordered edges")

    @property
    def playable(self) -> bool:
        return (self.clock.playback_time(self.start) >= 0
                and self.clock.playback_time(self.end) <= self.clock.playback_duration)


@dataclass(frozen=True)
class ModelRun:
    id: str
    source_id: str
    engine: str
    build: str
    model_revision: str
    options: tuple[str, ...]
    backend: str
    device_id: str


@dataclass(frozen=True)
class TextSpan:
    """Half-open Python Unicode code-point offsets into the original segment."""

    start: int
    end: int

    def __post_init__(self):
        if not 0 <= self.start <= self.end:
            raise ValueError("Invalid text span")


@dataclass(frozen=True)
class TextPiece:
    id: str
    token_id: int
    surface: str
    span: TextSpan | None
    timing: RawTiming
    probability: float | None = None
    dtw_ticks: int | None = None


@dataclass(frozen=True)
class TranscriptSegment:
    id: str
    run_id: str
    text: str
    timing: RawTiming
    pieces: tuple[TextPiece, ...]


@dataclass(frozen=True)
class Voice:
    run_id: str
    label: str


@dataclass(frozen=True)
class VoiceTurn:
    id: str
    voice: Voice
    timing: RawTiming
    interval: SampleInterval | None


@dataclass(frozen=True)
class Attribution:
    voice: Voice | None
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class PhraseCandidate:
    id: str
    text: str
    evidence_ids: tuple[str, ...]
    interval: SampleInterval | None
    owners: tuple[Attribution, ...] = ()


@dataclass(frozen=True)
class ListenerDecision:
    id: str
    target_id: str
    listener: str
    field: Literal["wording", "owner", "start", "end", "suppress", "note"]
    value: str | Voice | int | None


@dataclass(frozen=True)
class PlannedPhrase:
    id: str
    text: str
    owner: Voice | None
    interval: SampleInterval
    evidence_ids: tuple[str, ...]

    def __post_init__(self):
        if not self.interval.playable:
            raise ValueError("Phrase lies outside playable video")


@dataclass(frozen=True)
class Lane:
    number: int
    phrase_id: str


@dataclass(frozen=True)
class ScreenState:
    interval: SampleInterval
    lanes: tuple[Lane, ...]


@dataclass(frozen=True)
class ReviewFinding:
    id: str
    reason: str
    evidence_ids: tuple[str, ...]
    interval: SampleInterval | None = None
