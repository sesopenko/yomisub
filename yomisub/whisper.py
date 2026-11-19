import shutil
import subprocess
from functools import partial


def prepare_transcriber():
    whisper_cli = shutil.which("whisper-cli")
    if whisper_cli is None:
        raise RuntimeError("whisper-cli is missing from PATH. Follow the setup in README.md.")
    return partial(_transcribe, whisper_cli)


def _transcribe(whisper_cli, audio_path, model_path, lang_code, output_stem):
    try:
        subprocess.run([
            whisper_cli, "--model", str(model_path), "--file", str(audio_path),
            "--language", lang_code, "--output-srt", "--output-file", str(output_stem),
        ], stdout=subprocess.DEVNULL, check=True)
    except subprocess.CalledProcessError as error:
        raise RuntimeError(
            "whisper-cli failed to transcribe the audio. See the terminal for details."
        ) from error
    return output_stem.with_suffix(".srt")
