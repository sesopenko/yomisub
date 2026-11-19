import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from yomisub.whisper import prepare_transcriber


class WhisperTests(unittest.TestCase):
    @patch("yomisub.whisper.shutil.which", return_value=None)
    def test_missing_executable_reports_setup_hint(self, which):
        with self.assertRaisesRegex(RuntimeError, "whisper-cli is missing from PATH"):
            prepare_transcriber()
        which.assert_called_once_with("whisper-cli")

    @patch("yomisub.whisper.shutil.which", return_value="/tools/whisper-cli")
    @patch("yomisub.whisper.subprocess.run")
    def test_transcribe_builds_command_and_returns_srt_path(self, run, which):
        transcribe = prepare_transcriber()
        result = transcribe(Path("audio.wav"), Path("model.bin"), "ja", Path("transcript"))

        which.assert_called_once_with("whisper-cli")
        run.assert_called_once_with([
            "/tools/whisper-cli", "--model", "model.bin", "--file", "audio.wav",
            "--language", "ja", "--output-srt", "--output-file", "transcript",
        ], stdout=subprocess.DEVNULL, check=True)
        self.assertEqual(result, Path("transcript.srt"))

    @patch("yomisub.whisper.shutil.which", return_value="/tools/whisper-cli")
    @patch("yomisub.whisper.subprocess.run")
    def test_transcription_failure_keeps_process_error_as_cause(self, run, which):
        process_error = subprocess.CalledProcessError(1, "whisper-cli")
        run.side_effect = process_error
        transcribe = prepare_transcriber()

        with self.assertRaisesRegex(RuntimeError, "whisper-cli failed to transcribe") as caught:
            transcribe(Path("audio.wav"), Path("model.bin"), "ja", Path("transcript"))
        self.assertIs(caught.exception.__cause__, process_error)
