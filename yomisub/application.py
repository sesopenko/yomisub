"""Generation and offline replay share the same editorial and rendering operations."""

from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from .domain import ListenerDecision, ReviewFinding
from .ports import (
    AudioPreparation, CuePlan, Evidence, EvidenceStore, GenerationRequest, GenerationResult,
    Grouper, Placement, Planner, Progress, Publisher, Refinement, Refiner, ReplayOutput,
    ReplayRequest, ReplayResult, Scanner, Stage, StageError, Transcriber, Writer,
)


@dataclass(frozen=True)
class Export:
    plan: CuePlan
    srt: bytes
    ass: bytes
    findings: tuple[ReviewFinding, ...]


@dataclass
class SubtitleEditor:
    planner: Planner
    srt: Writer
    ass: Writer

    def render(self, evidence: Evidence, corrections: tuple[ListenerDecision, ...] = ()) -> Export:
        plan = self.planner.plan(evidence, evidence.decisions + corrections)
        srt = self.srt.render(plan)
        ass = self.ass.render(plan)
        findings = {item.id: item for item in (*plan.findings, *srt.findings, *ass.findings)}
        return Export(plan, srt.data, ass.data, tuple(findings.values()))


@dataclass
class GenerateSubtitles:
    placement: Placement
    audio: AudioPreparation
    asr: Transcriber
    scanner: Scanner
    refiner: Refiner
    grouper: Grouper
    editor: SubtitleEditor
    store: EvidenceStore
    publisher: Publisher

    def __call__(self, request: GenerationRequest, progress: Progress) -> GenerationResult:
        progress("Checking model runtimes...")
        scan_target = self.placement.resolve(Stage.DIARIZATION)
        self.scanner.preflight(scan_target)
        asr_target = self.placement.resolve(Stage.BASELINE_ASR)
        self.asr.preflight(request.model, asr_target, progress)
        language = request.stream.language
        with TemporaryDirectory(prefix="yomisub-") as directory:
            work = Path(directory)
            progress("Preparing audio...")
            track = self.audio.prepare(request, work)
            progress("Transcribing the selected track...")
            baseline = self.asr.transcribe(track.mix, language, request.model, asr_target, work)
            progress("Analyzing speakers...")
            scan = self.scanner.scan(track, scan_target, work)
            try:
                extra = self.refiner.refine(request, track, scan, work, progress)
            except StageError as error:
                finding = ReviewFinding("refinement-failed", str(error), (scan.run.id,))
                extra = Refinement(findings=(finding,))

            transcripts = (baseline, *extra.transcripts)
            files = (track.original, track.mix, *extra.files)
            groups = tuple(group for run in transcripts for group in self.grouper.group(run, language))
            evidence = Evidence(
                request.video.stem, request.stream, track.clock, tuple(file.source for file in files),
                transcripts, scan, extra.runs, groups, extra.findings, planner_version=2,
            )
            progress("Preparing subtitle outputs...")
            export = self.editor.render(evidence)
            bundle = work / "evidence.zip"
            self.store.save(bundle, evidence, files, export.plan, export.findings)
            paths = self.publisher.publish(request.video, language, export.srt, export.ass, bundle)
            return GenerationResult(*paths, export.findings, extra.findings)


@dataclass
class ReplaySubtitles:
    editor: SubtitleEditor
    store: EvidenceStore
    output: ReplayOutput

    def __call__(self, request: ReplayRequest) -> ReplayResult:
        return self.replay_evidence(self.store.load(request.bundle), request)

    def replay_evidence(self, evidence: Evidence, request: ReplayRequest) -> ReplayResult:
        export = self.editor.render(evidence, request.corrections)
        paths = self.output.write(
            request.output_directory, evidence.stem, evidence.stream.language, export.srt, export.ass,
        )
        return ReplayResult(*paths, export.findings)
