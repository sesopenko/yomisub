import io
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from yomisub.models import MODEL_URL, get_model_path


class DownloadResponse(io.BytesIO):
    def __init__(self, content, content_length):
        super().__init__(content)
        self.headers = {}
        if content_length is not None:
            self.headers["Content-Length"] = str(content_length)


class ModelCacheTests(unittest.TestCase):
    def setUp(self):
        self.cache_dir = Path(self.enterContext(TemporaryDirectory())) / "models"
        self.model_path = self.cache_dir / "ggml-tiny.bin"
        self.messages = []
        self.urlopen = self.enterContext(patch("yomisub.models.urlopen"))

    def resolve_model(self):
        return get_model_path("tiny", self.messages.append, cache_dir=self.cache_dir)

    def test_cache_hit_reuses_existing_file(self):
        self.cache_dir.mkdir()
        self.model_path.write_bytes(b"cached model")

        self.assertEqual(self.resolve_model(), self.model_path)
        self.assertEqual(self.messages, [])
        self.urlopen.assert_not_called()

    def test_download_publishes_model_with_or_without_content_length(self):
        for content_length in (5, None):
            with self.subTest(content_length=content_length):
                self.messages.clear()
                self.urlopen.reset_mock()
                self.urlopen.return_value = DownloadResponse(b"model", content_length)

                self.assertEqual(self.resolve_model(), self.model_path)
                self.assertEqual(self.model_path.read_bytes(), b"model")
                self.assertEqual(list(self.cache_dir.iterdir()), [self.model_path])
                self.assertEqual(self.messages, ["Downloading the tiny model..."])
                self.urlopen.assert_called_once_with(f"{MODEL_URL}/ggml-tiny.bin", timeout=60)
                self.model_path.unlink()

    def test_empty_and_truncated_downloads_leave_no_cache_entry(self):
        for content, content_length in ((b"", None), (b"partial", 20)):
            with self.subTest(content=content):
                self.urlopen.return_value = DownloadResponse(content, content_length)

                with self.assertRaisesRegex(RuntimeError, "tiny model download was incomplete"):
                    self.resolve_model()

                self.assertEqual(list(self.cache_dir.iterdir()), [])

    def test_interrupted_download_cleans_up_and_can_be_retried(self):
        class InterruptedResponse(DownloadResponse):
            def read(self, size):
                if self.tell():
                    raise OSError("connection dropped")
                return super().read(3)

        self.urlopen.return_value = InterruptedResponse(b"model", 5)
        with self.assertRaisesRegex(OSError, "connection dropped"):
            self.resolve_model()
        self.assertEqual(list(self.cache_dir.iterdir()), [])

        self.urlopen.return_value = DownloadResponse(b"model", 5)
        self.assertEqual(self.resolve_model().read_bytes(), b"model")
