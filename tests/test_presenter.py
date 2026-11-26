from pathlib import Path
import unittest
from unittest.mock import Mock

from yomisub.domain import ReviewFinding, SelectedStream
from yomisub.ports import GenerationResult, StageError
from yomisub.presenter import run_job, selected_request


class PresenterTests(unittest.TestCase):
    def test_request_preserves_chosen_track_model_and_optional_analysis(self):
        tracks = [SelectedStream(2, 0, "eng", "mono"), SelectedStream(5, 1, " JPN ", "stereo")]
        request = selected_request(Path("clip.mkv"), tracks, 1, "tiny", True)
        self.assertEqual((request.stream, request.model, request.analyze_stems),
                         (SelectedStream(5, 1, "ja", "stereo"), "tiny", True))
        with self.assertRaises(ValueError):
            selected_request(request.video, tracks, -1, "tiny")

    def test_pending_issue_count_paths_diagnostic_and_retry(self):
        adapter, ui = Mock(), Mock()
        finding = ReviewFinding("mix-retry-1-failed", "Optional model unavailable", ("cue1", "cue2"))
        result = GenerationResult(*(Path("clip.ja." + ext) for ext in ("srt", "ass", "yomisub.zip")), (finding,))
        adapter.side_effect = [StageError("Install the speaker worker"), result]
        for _ in range(2):
            run_job(adapter, Mock(), ui.status, ui.error, ui.finished)
        ui.error.assert_called_once_with("Install the speaker worker")
        self.assertEqual(ui.finished.call_count, 2)
        message = ui.status.call_args.args[0]
        for text in ("1 item to review", "Optional model unavailable", *map(str, (result.srt, result.ass, result.bundle))):
            self.assertIn(text, message)
