from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock
import wave

from editorial_fixtures import evidence, segment
from yomisub.bundle import BundleStore
from yomisub.compute import ComputeConfig, Preference
from yomisub.ports import AudioFile, Device, ExecutionTarget, GenerationRequest, PreparedTrack, Stage, StageError
from yomisub.production import build_generator, ModelBackend


class ModelDevices:
    name = "controlled"

    def devices(self):
        return tuple(Device(id, "GPU", frozenset(Stage)) for id in ("first", "second"))

    def bind(self, stage, physical_id):
        return ExecutionTarget(self.name, physical_id, int(physical_id == "second"), stage)


class ProductionTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.video = Path(temp.name)/"sample.mkv"
        self.ev = evidence([segment("p", "yes", 10, 500)], [(0, 600, "A"), (300, 700, "B")])
        self.request = GenerationRequest(self.video, replace(self.ev.stream, language="en"))
        self.asr, self.scanner, self.audio = Mock(), Mock(), Mock()
        self.backend = ModelBackend(ModelDevices(), asr=self.asr, scanner=self.scanner)
        self.asr.transcribe.side_effect = self.transcribe
        self.audio.prepare.side_effect = self.prepare
        self.scanner.scan.side_effect = lambda track, target, work: replace(
            self.ev.scan, run=replace(self.ev.scan.run, device_id=target.physical_id))
        self.work = []

    def prepare(self, request, directory):
        self.work.append(directory)
        wav = directory/"fixture.wav"
        with wave.open(str(wav), "wb") as out:
            out.setparams((1, 2, 1000, 10000, "NONE", ""))
            out.writeframes(bytes(20000))
        return PreparedTrack(self.ev.clock, *(AudioFile(s, wav) for s in self.ev.sources))

    def transcribe(self, source, language, model, target, work):
        base = self.ev.transcripts[0]
        if target.stage == Stage.RETRY_ASR:
            raise StageError("retry model unavailable")
        return replace(base, run=replace(base.run, device_id=target.physical_id))

    def generator(self, speaker):
        config = ComputeConfig("first", {Stage.DIARIZATION: Preference(device=speaker)})
        return build_generator(backends=[self.backend], config=config, audio=self.audio)

    def test_one_and_split_placement_repeat_publication_and_optional_failure(self):
        for speaker in ("first", "second"):
            progress = []
            result = self.generator(speaker)(self.request, progress.append)
            self.assertTrue(result.srt.exists() and result.ass.exists())
            ev = BundleStore().load(result.bundle)
            self.assertEqual((ev.transcripts[0].run.device_id, ev.scan.run.device_id), ("first", speaker))
            self.assertTrue(any(f.reason == "retry model unavailable" for f in result.findings))
            self.assertTrue(any(f.reason == "retry model unavailable" for f in ev.findings))
            self.assertIn("yes", result.srt.read_text())
            self.assertTrue(any("Analyzing speakers" in stage for stage in progress))
            self.assertFalse(self.work[-1].exists())

    def test_setup_failure_and_scan_crash_preserve_previous_installation(self):
        generate = self.generator("first")
        old = self.video.with_suffix(".en.srt")
        old.write_bytes(b"legacy")
        self.scanner.preflight.side_effect = StageError("speaker setup")
        with self.assertRaisesRegex(StageError, "speaker setup"):
            generate(self.request, lambda msg: None)
        self.audio.prepare.assert_not_called()
        self.asr.preflight.assert_not_called()
        self.scanner.preflight.side_effect = None
        self.scanner.scan.side_effect = StageError("scan crash")
        with self.assertRaisesRegex(StageError, "scan crash"):
            generate(self.request, lambda msg: None)
        self.assertFalse(self.work[-1].exists())
        self.assertEqual(old.read_bytes(), b"legacy")
        self.assertFalse(self.video.with_suffix(".en.yomisub.zip").exists())
