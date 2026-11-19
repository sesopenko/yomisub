import unittest
from datetime import timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import srt

from yomisub.subtitles import write_subtitles

TRANSCRIPT = """1
00:00:01,000 --> 00:00:02,000
こんにちは

2
00:00:05,000 --> 00:00:13,000
またね

"""


class SubtitleTests(unittest.TestCase):
    def setUp(self):
        self.directory = Path(self.enterContext(TemporaryDirectory()))
        self.transcript = self.directory / "transcript.srt"
        self.transcript.write_text(TRANSCRIPT, encoding="utf-8")
        self.video = self.directory / "episode.01.mkv"
        self.destination = self.directory / "episode.01.ja.srt"

    def test_writes_unicode_and_adjusts_cue_ends(self):
        self.destination.write_text("old subtitles", encoding="utf-8")
        output = write_subtitles(self.transcript, self.video, "ja")
        self.assertEqual(output, self.destination)
        subtitles = list(srt.parse(output.read_text(encoding="utf-8")))

        self.assertEqual([cue.content for cue in subtitles], ["こんにちは", "またね"])
        self.assertEqual([cue.start for cue in subtitles], [
            timedelta(seconds=1), timedelta(seconds=5),
        ])
        self.assertEqual([cue.end for cue in subtitles], [
            timedelta(seconds=2.5), timedelta(seconds=11),
        ])

    def test_failed_publish_preserves_destination_and_cleans_up(self):
        self.destination.write_bytes(b"existing subtitles")
        with patch.object(Path, "replace", side_effect=OSError("failed to publish")):
            with self.assertRaisesRegex(OSError, "failed to publish"):
                write_subtitles(self.transcript, self.video, "ja")

        self.assertEqual(self.destination.read_bytes(), b"existing subtitles")
        self.assertEqual(list(self.directory.glob(".yomisub-*")), [])
