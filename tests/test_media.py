import json
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from yomisub.media import AudioTrack, extract_audio, probe_audio_tracks
from yomisub.workflow import format_track_label, make_generation_request


class MediaTests(unittest.TestCase):
    @patch("yomisub.media.subprocess.run")
    def test_probe_preserves_stream_indices_and_audio_order(self, run):
        video = Path("two tracks.mkv")
        run.return_value.stdout = json.dumps({
            "streams": [
                {"index": 1, "tags": {"language": "jpn"}},
                {"index": 4, "tags": {"language": "ENG"}},
                {"index": 5},
            ],
        })
        tracks = probe_audio_tracks(video)
        self.assertEqual(tracks, [
            AudioTrack(1, 0, "jpn"),
            AudioTrack(4, 1, "ENG"),
            AudioTrack(5, 2, "und"),
        ])
        self.assertEqual([format_track_label(track) for track in tracks], [
            "Track 1 (jpn)", "Track 4 (ENG)", "Track 5 (und)",
        ])
        run.assert_called_once_with([
            "ffprobe", "-v", "error", "-select_streams", "a",
            "-show_entries", "stream=index:stream_tags=language", "-of", "json", str(video),
        ], capture_output=True, text=True, check=True)

        run.reset_mock()
        selected = make_generation_request(video, tracks, 1, "tiny")
        audio_path = Path("audio.wav")
        extract_audio(selected.video_path, selected.audio_ordinal, audio_path)

        self.assertEqual(selected.lang_code, "en")
        run.assert_called_once_with([
            "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-i", str(video),
            "-map", "0:a:1", "-ac", "1", "-ar", "16000",
            "-c:a", "pcm_s16le", str(audio_path),
        ], check=True)

    @patch("yomisub.media.subprocess.run")
    def test_probe_returns_no_tracks_for_empty_output(self, run):
        for stdout in ("{}", '{"streams": []}'):
            with self.subTest(stdout=stdout):
                run.return_value.stdout = stdout
                self.assertEqual(probe_audio_tracks(Path("silent.mkv")), [])

    @patch("yomisub.media.subprocess.run")
    def test_probe_propagates_process_and_parse_errors(self, run):
        video = Path("broken.mkv")
        run.side_effect = subprocess.CalledProcessError(1, "ffprobe")
        with self.assertRaises(subprocess.CalledProcessError):
            probe_audio_tracks(video)

        run.side_effect = None
        run.return_value.stdout = "invalid JSON"
        with self.assertRaises(json.JSONDecodeError):
            probe_audio_tracks(video)
