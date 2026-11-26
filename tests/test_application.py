import subprocess
import sys
import unittest
from fractions import Fraction
from pathlib import Path
from unittest.mock import Mock

from adapter_contracts import check_binding, check_scan, check_transcript
from yomisub.application import GenerateSubtitles, ReplaySubtitles, SubtitleEditor
from yomisub.domain import (
    AudioSource, ListenerDecision, ModelRun, RecordingClock, ReviewFinding, SelectedStream,
)
from yomisub.ports import (
    AudioFile, CuePlan, Device, ExecutionTarget, GenerationRequest, PreparedTrack, Refinement,
    Rendered, ReplayRequest, Scan, Stage, StageError, Transcript,
)


class FakeProvider:
    name = "test"

    def devices(self):
        return (Device("pci:test", "Test", frozenset(Stage)),)

    def bind(self, stage, physical_id):
        return ExecutionTarget(self.name, physical_id, 0, stage)

    def resolve(self, stage):
        return self.bind(stage, "pci:test")


class ApplicationTests(unittest.TestCase):
    def setUp(self):
        self.request = GenerationRequest(Path("video.mkv"), SelectedStream(2, 1, "ja", "stereo"))
        self.original = AudioFile(AudioSource("original", None, 44100, 44100), Path("original.wav"))
        self.mix = AudioFile(AudioSource("mix", "original", 16000, 16000), Path("mix.wav"))
        track = PreparedTrack(RecordingClock(44100, 44100, Fraction(0), Fraction(1)),
                              self.original, self.mix)
        run = ModelRun("baseline", "mix", "test", "1", "test-model", (), "test", "pci:test")
        scan_run = ModelRun("scan", "mix", "test", "1", "diarizer", (), "test", "pci:test")
        self.adapters = Mock()
        self.adapters.audio.prepare.return_value = track
        self.adapters.asr.transcribe.return_value = Transcript(run, ())
        self.adapters.scanner.scan.return_value = Scan(scan_run, ())
        self.adapters.refiner.refine.return_value = Refinement()
        self.adapters.grouper.group.return_value = ()
        self.adapters.planner.plan.side_effect = lambda evidence, edits: CuePlan((), (), evidence.findings)
        self.adapters.srt.render.return_value = Rendered(b"srt")
        self.adapters.ass.render.return_value = Rendered(b"ass")
        self.adapters.publisher.publish.return_value = tuple(Path(name) for name in (
            "video.ja.srt", "video.ja.ass", "video.ja.yomisub.zip",
        ))
        self.editor = SubtitleEditor(self.adapters.planner, self.adapters.srt, self.adapters.ass)
        self.generate = GenerateSubtitles(
            FakeProvider(), self.adapters.audio, self.adapters.asr, self.adapters.scanner,
            self.adapters.refiner, self.adapters.grouper, self.editor, self.adapters.store,
            self.adapters.publisher,
        )

    def test_generation_and_replay_use_same_planner_and_saved_evidence(self):
        result = self.generate(self.request, Mock())
        evidence = self.adapters.store.save.call_args.args[1]
        check_binding(self, self.generate.placement, Stage.BASELINE_ASR, "pci:test")
        check_transcript(self, evidence.transcripts[0], self.mix.source)
        check_scan(self, evidence.scan, self.mix.source)
        self.assertEqual(evidence.sources, (self.original.source, self.mix.source))
        self.assertEqual(result.bundle, Path("video.ja.yomisub.zip"))
        self.adapters.store.load.return_value = evidence
        self.adapters.output.write.return_value = (Path("out/a.srt"), Path("out/a.ass"))
        replay = ReplaySubtitles(self.editor, self.adapters.store, self.adapters.output)
        note = ListenerDecision("note-1", "mix", "listener", "note", "reviewed")
        replayed = replay(ReplayRequest(result.bundle, Path("out"), (note,)))
        self.assertEqual(replayed.srt, Path("out/a.srt"))
        self.adapters.planner.plan.assert_called_with(evidence, (note,))
        self.assertEqual(evidence.decisions, ())
        self.adapters.asr.transcribe.assert_called_once()
        self.adapters.scanner.scan.assert_called_once()

    def test_scan_failure_stops_publication(self):
        self.adapters.scanner.scan.side_effect = StageError("scan failed")
        with self.assertRaisesRegex(StageError, "scan failed"):
            self.generate(self.request, Mock())
        self.adapters.store.save.assert_not_called()
        self.adapters.publisher.publish.assert_not_called()

    def test_required_preflight_stops_before_media_preparation(self):
        self.adapters.scanner.preflight.side_effect = StageError("missing weights")
        with self.assertRaisesRegex(StageError, "missing weights"):
            self.generate(self.request, Mock())
        self.adapters.audio.prepare.assert_not_called()

    def test_optional_failure_retains_baseline_and_counts_distinct_open_findings(self):
        self.adapters.refiner.refine.side_effect = StageError("retry unavailable")
        shared = ReviewFinding("loss-1", "unrepresentable interval", ("state-1", "state-2"))
        self.adapters.srt.render.return_value = Rendered(b"srt", (shared, shared))
        result = self.generate(self.request, Mock())
        self.assertEqual([finding.id for finding in result.findings], ["refinement-failed", "loss-1"])
        _, evidence, _, _, saved_findings = self.adapters.store.save.call_args.args
        self.assertEqual(saved_findings, result.findings)
        self.assertEqual(evidence.transcripts, (self.adapters.asr.transcribe.return_value,))

    def test_imports_work_without_site_packages(self):
        subprocess.run([sys.executable, "-S", "-c", "import yomisub.application"], check=True)
