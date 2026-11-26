from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from editorial_fixtures import evidence, segment
from yomisub.application import SubtitleEditor
from yomisub.bundle import BundleStore
from yomisub.layout import CuePlanner
from yomisub.ports import AudioFile
from yomisub.publication import FilePublisher, Publication
from yomisub.writers import AssWriter, SrtWriter


class PublicationTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.video = self.root/"clip.mkv"
        self.tx = Publication(self.video, "ja")
        self.runs = {}
        for label in ("one", "two"):
            ev = evidence([segment("a", label, 10, 900)])
            result = SubtitleEditor(CuePlanner(), SrtWriter(), AssWriter()).render(ev)
            bundle = self.root/(label + ".zip")
            audio = self.root/"fixture.wav"
            audio.write_bytes(b"fixture")
            BundleStore().save(bundle, ev, tuple(AudioFile(s, audio) for s in ev.sources),
                               result.plan, result.findings)
            self.runs[label] = result.srt, result.ass, bundle

    def publish(self, label):
        return FilePublisher().publish(self.video, "ja", *self.runs[label])

    def visible(self):
        return [p.read_bytes() if p.exists() else None for p in self.tx.paths]

    def test_each_replacement_rolls_back_every_prior_set(self):
        real_replace = os.replace
        for count in (0, 1, 3):
            for i, path in enumerate(self.tx.paths):
                if i < count:
                    path.write_bytes(f"old{i}".encode())
            old = self.visible()
            for stop in range(3):
                def fail(src, dest):
                    if Path(src).name == f"new-{stop}":
                        raise OSError("interrupted")
                    return real_replace(src, dest)

                with self.subTest(count=count, stop=stop), patch("os.replace", side_effect=fail):
                    with self.assertRaisesRegex(OSError, "interrupted"):
                        self.publish("one")
                self.assertEqual(old, self.visible())

    def crash(self, phase, label):
        program = """
import os, sys
from pathlib import Path
import yomisub.publication as pub
from yomisub.bundle import BundleStore
from yomisub.application import SubtitleEditor
from yomisub.layout import CuePlanner
from yomisub.writers import AssWriter, SrtWriter
video,bundle=map(Path, sys.argv[1:3])
phase=sys.argv[3]
replace,mark=os.replace,pub.mark
def interrupt_rename(src,dest):
    replace(src,dest)
    if Path(src).name==phase:
        os._exit(72)
def interrupt_mark(directory,name):
    mark(directory,name)
    if name==phase:
        os._exit(72)
pub.os.replace,pub.mark=interrupt_rename,interrupt_mark
ev=BundleStore().load(bundle)
result=SubtitleEditor(CuePlanner(), SrtWriter(), AssWriter()).render(ev)
pub.FilePublisher().publish(video, 'ja', result.srt, result.ass, bundle)
"""
        run = subprocess.run([sys.executable, "-c", program, self.video, self.runs[label][2], phase])
        self.assertEqual(run.returncode, 72)

    def test_crash_before_and_after_commit_marker_and_fresh_writer_retry(self):
        self.tx.paths[0].write_bytes(b"legacy")
        old = self.visible()
        self.crash("new-2", "one")
        self.crash("new-0", "two")
        for _ in range(2):
            with self.tx.locked():
                self.assertEqual(self.visible(), old)
        self.crash("committed", "one")
        for _ in range(2):
            with self.tx.locked():
                self.assert_run("one")

    def assert_run(self, label):
        srt, ass, bundle = self.runs[label]
        self.assertEqual(self.visible(), [srt, ass, bundle.read_bytes()])

    def test_competing_writers_finish_with_one_complete_run(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            for paths in pool.map(self.publish, self.runs):
                self.assertEqual(paths, self.tx.paths)
        with ZipFile(self.tx.paths[2]) as archive:
            doc = json.loads(archive.read("manifest.json"))
        segment = doc["evidence"]["transcripts"][0]["segments"][0]
        self.assert_run(segment["text"])
