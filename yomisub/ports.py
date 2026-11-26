"""Application-owned interfaces. File handles and model processes stay in adapters."""

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Protocol

from .domain import (
    AudioSource, ListenerDecision, ModelRun, PlannedPhrase, RecordingClock,
    ReviewFinding, ScreenState, SelectedStream, TextSpan, TranscriptSegment, VoiceTurn,
)

type Progress = Callable[[str], None]


class Stage(StrEnum):
    BASELINE_ASR = "baseline_asr"
    RETRY_ASR = "retry_asr"
    DIARIZATION = "diarization"
    SEPARATION = "separation"
    STEM_ASR = "stem_asr"


class StageError(RuntimeError):
    """An external model operation or its preflight could not complete."""


@dataclass(frozen=True)
class Device:
    physical_id: str
    name: str
    stages: frozenset[Stage]


@dataclass(frozen=True)
class ExecutionTarget:
    provider: str
    physical_id: str
    runtime_index: int
    stage: Stage


class ComputeProvider(Protocol):
    name: str

    def devices(self) -> tuple[Device, ...]: ...
    def bind(self, stage: Stage, physical_id: str) -> ExecutionTarget: ...


class Placement(Protocol):
    def resolve(self, stage: Stage) -> ExecutionTarget: ...


@dataclass(frozen=True)
class GenerationRequest:
    video: Path
    stream: SelectedStream
    model: str = "medium"
    analyze_stems: bool = False


@dataclass(frozen=True)
class ReplayRequest:
    bundle: Path
    output_directory: Path
    corrections: tuple[ListenerDecision, ...] = ()


@dataclass(frozen=True)
class AudioFile:
    source: AudioSource
    path: Path


@dataclass(frozen=True)
class PreparedTrack:
    clock: RecordingClock
    original: AudioFile
    mix: AudioFile


class Tracks(Protocol):
    def list_tracks(self, video: Path) -> tuple[SelectedStream, ...]: ...


class AudioPreparation(Protocol):
    def prepare(self, request: GenerationRequest, work: Path) -> PreparedTrack: ...


@dataclass(frozen=True)
class Transcript:
    run: ModelRun
    segments: tuple[TranscriptSegment, ...]
    core_id: str | None = None
    context_only_segment_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class Scan:
    run: ModelRun
    turns: tuple[VoiceTurn, ...]


class Transcriber(Protocol):
    def preflight(self, model: str, target: ExecutionTarget, progress: Progress) -> None: ...

    def transcribe(self, audio: AudioFile, language: str, model: str, target: ExecutionTarget,
                   work: Path) -> Transcript: ...


class Scanner(Protocol):
    def preflight(self, target: ExecutionTarget) -> None: ...
    def scan(self, track: PreparedTrack, target: ExecutionTarget, work: Path) -> Scan: ...


@dataclass(frozen=True)
class Separation:
    run: ModelRun
    stems: tuple[AudioFile, AudioFile]


class Separator(Protocol):
    def separate(self, crop: AudioFile, target: ExecutionTarget, work: Path) -> Separation: ...


@dataclass(frozen=True)
class Refinement:
    files: tuple[AudioFile, ...] = ()
    transcripts: tuple[Transcript, ...] = ()
    runs: tuple[ModelRun, ...] = ()
    findings: tuple[ReviewFinding, ...] = ()


class Refiner(Protocol):
    def refine(self, request: GenerationRequest, track: PreparedTrack, scan: Scan,
               work: Path, progress: Progress) -> Refinement: ...


@dataclass(frozen=True)
class Grouping:
    segment_id: str
    surfaces: tuple[TextSpan, ...]
    cut_offsets: tuple[int, ...]
    strategy: str


class Grouper(Protocol):
    def group(self, transcript: Transcript, language: str) -> tuple[Grouping, ...]: ...


@dataclass(frozen=True)
class Evidence:
    stem: str
    stream: SelectedStream
    clock: RecordingClock
    sources: tuple[AudioSource, ...]
    transcripts: tuple[Transcript, ...]
    scan: Scan
    other_runs: tuple[ModelRun, ...]
    groups: tuple[Grouping, ...]
    findings: tuple[ReviewFinding, ...]
    decisions: tuple[ListenerDecision, ...] = ()


@dataclass(frozen=True)
class CuePlan:
    phrases: tuple[PlannedPhrase, ...]
    states: tuple[ScreenState, ...]
    findings: tuple[ReviewFinding, ...]


class Planner(Protocol):
    def plan(self, evidence: Evidence, decisions: tuple[ListenerDecision, ...]) -> CuePlan: ...


@dataclass(frozen=True)
class Rendered:
    data: bytes
    findings: tuple[ReviewFinding, ...] = ()


class Writer(Protocol):
    def render(self, plan: CuePlan) -> Rendered: ...


class EvidenceStore(Protocol):
    def save(self, destination: Path, evidence: Evidence, files: tuple[AudioFile, ...],
             plan: CuePlan, open_findings: tuple[ReviewFinding, ...]) -> None: ...
    def load(self, bundle: Path) -> Evidence: ...


class Publisher(Protocol):
    def publish(self, video: Path, language: str, srt: bytes, ass: bytes,
                bundle: Path) -> tuple[Path, Path, Path]: ...


class ReplayOutput(Protocol):
    def write(self, directory: Path, stem: str, language: str, srt: bytes,
              ass: bytes) -> tuple[Path, Path]: ...


@dataclass(frozen=True)
class GenerationResult:
    srt: Path
    ass: Path
    bundle: Path
    findings: tuple[ReviewFinding, ...]


@dataclass(frozen=True)
class ReplayResult:
    srt: Path
    ass: Path
    findings: tuple[ReviewFinding, ...]
