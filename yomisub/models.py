from functools import lru_cache
import hashlib
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.request import urlopen

MODEL_URL = "https://huggingface.co/ggerganov/whisper.cpp/resolve/main"
MODELS = ("tiny", "base", "small", "medium", "large-v2")
DEFAULT_MODEL = "medium"


# Published GGML file identities in whisper.cpp 231638a0 models/README.md.
CHECKPOINTS = {
    "tiny": "bd577a113a864445d4c299885e0cb97d4ba92b5f",
    "base": "465707469ff3a37a2b9b8d8f89f2f99de7299dac",
    "small": "55356645c2b361a969dfd0ef2c5a50d530afd8d5",
    "medium": "fd9727b6e1217c2f614f9b698455c4ffd82463b4",
    "large-v2": "0f4c8e34f21cf1a914c59d8b3ce882345ad349d6",
    "large-v3": "ad82bf6a9043ceed055076d0fd39f5f186ff8062",
}


@lru_cache(maxsize=32)
def _digest(path, algorithm, fingerprint):
    with path.open("rb") as source:
        return hashlib.file_digest(source, algorithm).hexdigest()


def digest(path, algorithm):
    info = path.stat()
    return _digest(path, algorithm, (info.st_dev, info.st_ino, info.st_size, info.st_ctime_ns))


def _verify(path, expected):
    if expected is not None and digest(path, "sha1") != expected:
        raise ValueError(f"Incorrect Whisper checkpoint at {path}. Replace it with the full published model.")


def get_model_path(model_name, report_status, *, cache_dir=None, expected_sha1=None):
    if model_name not in CHECKPOINTS:
        raise ValueError(f"Unknown multilingual Whisper checkpoint {model_name!r}.")
    if cache_dir is None:
        cache_dir = Path.home() / ".cache" / "yomisub" / "models"
    model_path = cache_dir / f"ggml-{model_name}.bin"
    if model_path.is_file():
        _verify(model_path, expected_sha1)
        return model_path

    report_status(f"Downloading the {model_name} model...")
    cache_dir.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=cache_dir) as temp_dir:
        download_path = Path(temp_dir) / model_path.name
        with urlopen(f"{MODEL_URL}/{model_path.name}", timeout=60) as response:
            with download_path.open("wb") as download:
                shutil.copyfileobj(response, download)
            content_length = response.headers.get("Content-Length")
        size = download_path.stat().st_size
        if not size or (content_length is not None and size != int(content_length)):
            raise RuntimeError(f"The {model_name} model download was incomplete. Try again.")
        _verify(download_path, expected_sha1)
        download_path.replace(model_path)
    return model_path
