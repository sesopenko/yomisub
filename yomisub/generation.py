from collections.abc import Callable
from pathlib import Path
from tempfile import TemporaryDirectory

from .workflow import GenerationRequest, ReportStatus

type Transcribe = Callable[[Path, Path, str, Path], Path]


def generate_subtitles(
    request: GenerationRequest,
    report_status: ReportStatus,
    *,
    extract_audio: Callable[[Path, int, Path], None],
    get_model_path: Callable[[str, ReportStatus], Path],
    prepare_transcriber: Callable[[], Transcribe],
    write_subtitles: Callable[[Path, Path, str], Path],
) -> Path:
    transcribe = prepare_transcriber()

    with TemporaryDirectory(prefix="yomisub-") as temp_dir:
        audio_path = Path(temp_dir) / "audio.wav"
        output_stem = Path(temp_dir) / "transcript"

        report_status("Extracting audio...")
        extract_audio(request.video_path, request.audio_ordinal, audio_path)

        model_path = get_model_path(request.model_name, report_status)
        report_status("Transcribing with whisper.cpp...")
        transcript_path = transcribe(audio_path, model_path, request.lang_code, output_stem)

        report_status("Generating subtitles...")
        return write_subtitles(transcript_path, request.video_path, request.lang_code)
