from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
import wave
from zipfile import ZipFile

from editorial_fixtures import evidence, segment
from yomisub.application import SubtitleEditor
from yomisub.bundle import BundleError, BundleStore
from yomisub.layout import CuePlanner
from yomisub.ports import AudioFile, Grouping
from yomisub.replay import read_corrections, replay
from yomisub.writers import SrtWriter, AssWriter


class BundleTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.bundle = self.root / "moved.zip"
        store = BundleStore()
        self.original = evidence(
            [segment("p", "明日。行く", 0, 1000, [("明日。", 10, 300), ("行く", 400, 900)])],
            [(0, 1000, "A"), (1400, 2000, "B")], groups=[Grouping("p", (), (3,), "saved")],
        )
        self.editor = SubtitleEditor(CuePlanner(), SrtWriter(), AssWriter())
        self.render = self.editor.render(self.original)
        with TemporaryDirectory(dir=self.root) as work:
            wav = Path(work) / "input.wav"
            with wave.open(str(wav), "wb") as f:
                f.setparams((1, 2, 1000, 10000, "NONE", ""))
                f.writeframes(bytes(20000))
            archive = Path(work) / "clip.ja.yomisub.zip"
            store.save(archive, self.original, tuple(AudioFile(s, wav) for s in self.original.sources),
                       self.render.plan, self.render.findings)
            archive.rename(self.bundle)
        self.id, self.saved, self.plan, _ = store.read(self.bundle)
        self.edits = self.root / "edits.json"

    def correct(self, rows):
        self.edits.write_text(json.dumps({"bundle": self.id, "edits": [
            {"listener": "reviewer", "id": f"edit-{i}", "target": "p", **row} for i, row in enumerate(rows)
        ]}))

    def test_relocated_replay_without_site_packages_or_inference(self):
        dest = self.root / "offline"
        subprocess.run([sys.executable, "-S", "-m", "yomisub.replay", str(self.bundle), str(dest)],
                       check=True, capture_output=True)
        self.assertEqual((dest/"clip.ja.srt").read_bytes(), self.render.srt)
        self.assertEqual((dest/"clip.ja.ass").read_bytes(), self.render.ass)
        self.assertEqual(self.saved, self.original)
        with self.assertRaises(FileExistsError):
            replay(self.bundle, dest)

    def test_correction_length_timing_new_voice_note_and_trace(self):
        digest = sha256(self.bundle.read_bytes()).digest()
        turn = self.saved.scan.turns[-1].id
        self.correct([{"field": "wording", "value": "明日行こう"},
                      {"field": "end", "value": 850},
                      {"field": "add", "target": turn, "value": "うん", "start": 1400, "end": 1950, "owner": "B"},
                      {"field": "note", "target": "scan", "value": "Silence", "start": 2100, "end": 3000}])
        changed = replay(self.bundle, self.root / "corrected", self.edits)
        self.assertIn("明日行こう", changed.srt.read_text())
        self.assertIn("うん", changed.ass.read_text())
        edits = read_corrections(self.edits, self.id, self.saved, self.plan)
        export = self.editor.render(self.saved, edits)
        first, second = export.plan.phrases
        self.assertEqual((first.interval.start, first.interval.end), (10, 850))
        self.assertTrue({"edit-0", "edit-1", "p"} <= set(first.evidence_ids))
        self.assertEqual(second.evidence_ids, ("edit-2", turn))
        self.assertIn("edit-3", {f.id for f in changed.findings})
        self.assertEqual(sha256(self.bundle.read_bytes()).digest(), digest)
        self.assertEqual(BundleStore().load(self.bundle), self.original)

    def test_timed_subdivisions_and_invalid_batch_preserve_destinations(self):
        self.correct([{"field": "wording", "value": "だから", "parts": [
            {"text": "だ", "start": 10, "end": 100}, {"text": "から", "start": 350, "end": 450}]}])
        result = replay(self.bundle, self.root, self.edits)
        self.assertIn("00:00:00,350 --> 00:00:00,450", result.srt.read_text())
        result.ass.unlink()
        for edits in [
            [{"field": "start", "target": "missing", "value": 1}],
            [{"field": "start", "value": 9999}],
            [{"field": "end", "value": 50}, {"field": "end", "value": 99}],
            [{"field": "suppress"}, {"field": "owner", "value": "A"}],
            [{"field": "add", "start": -1, "end": 100, "value": "声"}],
        ]:
            data = result.srt.read_bytes()
            self.correct(edits)
            with self.subTest(edits=edits), self.assertRaises(BundleError):
                replay(self.bundle, self.root, self.edits)
            self.assertEqual(result.srt.read_bytes(), data)
            self.assertFalse(result.ass.exists())

    def test_corrupt_version_missing_audio_and_broken_source(self):
        with ZipFile(self.bundle) as data:
            members = {name: data.read(name) for name in data.namelist()}
        for change in ["version", "audio", "source", "corrupt"]:
            broken = self.root / (change + ".zip")
            raw = dict(members)
            manifest = json.loads(raw["manifest.json"])
            if change == "version":
                manifest["planner"] += 1
            if change == "source":
                manifest["evidence"]["scan"]["run"]["source_id"] = "absent"
            if change == "audio":
                del raw["audio/0000.wav"]
            raw["manifest.json"] = json.dumps(manifest).encode()
            with ZipFile(broken, "w") as out:
                for name, payload in raw.items():
                    out.writestr(name, payload)
            if change == "corrupt":
                broken.write_bytes(b"invalid")
            with self.subTest(change=change), self.assertRaisesRegex(BundleError, change + ".*Restore"):
                replay(broken, self.root / "unused")
