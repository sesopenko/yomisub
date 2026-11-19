import unittest
from pathlib import Path
from unittest.mock import Mock, call

from yomisub.generation import generate_subtitles
from yomisub.media import AudioTrack
from yomisub.workflow import GenerationRequest, make_generation_request, run_generation


class SelectionTests(unittest.TestCase):
    def test_request_normalizes_language_and_passes_through_valid_fallback(self):
        video = Path("episode.mkv")
        for tag, expected in ((" JPN ", "ja"), ("EN", "en"), ("AST", "ast")):
            with self.subTest(tag=tag):
                track = AudioTrack(5, 2, tag)
                self.assertEqual(
                    make_generation_request(video, [track], 0, "tiny"),
                    GenerationRequest(video, 2, expected, "tiny"),
                )

    def test_request_rejects_invalid_language_tags(self):
        for tag in ("und", "", "e", "en-US", "éé", "3n"):
            with self.subTest(tag=tag):
                track = AudioTrack(1, 0, tag)
                with self.assertRaisesRegex(ValueError, "Could not determine the language"):
                    make_generation_request(Path("video.mkv"), [track], 0, "tiny")

    def test_request_rejects_missing_selection(self):
        tracks = [AudioTrack(1, 0, "eng")]
        for available, index in (([], 0), (tracks, -1), (tracks, 1)):
            with self.subTest(available=available, index=index):
                with self.assertRaisesRegex(ValueError, "Could not determine the language"):
                    make_generation_request(Path("video.mkv"), available, index, "tiny")


class GenerationTests(unittest.TestCase):
    def setUp(self):
        self.request = GenerationRequest(Path("video.mkv"), 1, "ja", "tiny")
        self.effects = Mock()
        self.effects.prepare_transcriber.return_value = self.effects.transcribe
        self.effects.get_model_path.return_value = Path("ggml-tiny.bin")
        self.effects.write_subtitles.return_value = Path("video.ja.srt")
        self.effects.transcribe.side_effect = self.transcribe

    def transcribe(self, audio_path, model_path, lang_code, output_stem):
        self.assertTrue(audio_path.parent.is_dir())
        return output_stem.with_suffix(".srt")

    def generate(self, request, report_status):
        return generate_subtitles(
            request,
            report_status,
            extract_audio=self.effects.extract_audio,
            get_model_path=self.effects.get_model_path,
            prepare_transcriber=self.effects.prepare_transcriber,
            write_subtitles=self.effects.write_subtitles,
        )

    def run_worker(self):
        run_generation(
            self.generate,
            self.request,
            report_status=self.effects.status,
            report_error=self.effects.error,
            on_finished=self.effects.finished,
        )

    def test_workflow_runs_in_order_and_reports_success(self):
        self.effects.get_model_path.side_effect = self.resolve_model
        self.run_worker()

        audio_path = self.effects.extract_audio.call_args.args[2]
        output_stem = audio_path.with_name("transcript")
        self.assertEqual(audio_path.name, "audio.wav")
        self.assertEqual(self.effects.mock_calls, [
            call.prepare_transcriber(),
            call.status("Extracting audio..."),
            call.extract_audio(self.request.video_path, 1, audio_path),
            call.get_model_path("tiny", self.effects.status),
            call.status("Downloading the tiny model..."),
            call.status("Transcribing with whisper.cpp..."),
            call.transcribe(audio_path, Path("ggml-tiny.bin"), "ja", output_stem),
            call.status("Generating subtitles..."),
            call.write_subtitles(output_stem.with_suffix(".srt"), self.request.video_path, "ja"),
            call.status("Subtitles saved to video.ja.srt"),
            call.finished(),
        ])
        self.assertFalse(audio_path.parent.exists())

    def resolve_model(self, model_name, report_status):
        report_status(f"Downloading the {model_name} model...")
        return self.effects.get_model_path.return_value

    def test_workflow_reports_failure_and_finishes(self):
        self.effects.transcribe.side_effect = RuntimeError("transcription failed")
        self.run_worker()

        self.effects.write_subtitles.assert_not_called()
        self.assertEqual(self.effects.mock_calls[-2:], [
            call.error("transcription failed"),
            call.finished(),
        ])
        audio_path = self.effects.extract_audio.call_args.args[2]
        self.assertFalse(audio_path.parent.exists())

    def test_workflow_checks_for_transcriber_before_extracting_audio(self):
        self.effects.prepare_transcriber.side_effect = RuntimeError("executable missing")
        self.run_worker()

        self.assertEqual(self.effects.mock_calls, [
            call.prepare_transcriber(),
            call.error("executable missing"),
            call.finished(),
        ])
