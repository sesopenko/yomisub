import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.request import urlopen

MODEL_URL = "https://huggingface.co/ggerganov/whisper.cpp/resolve/main"
MODELS = ("tiny", "base", "small", "medium", "large-v2")
DEFAULT_MODEL = "medium"


def get_model_path(model_name, report_status, *, cache_dir=None):
    if cache_dir is None:
        cache_dir = Path.home() / ".cache" / "yomisub" / "models"
    model_path = cache_dir / f"ggml-{model_name}.bin"
    if model_path.is_file():
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
        download_path.replace(model_path)
    return model_path
