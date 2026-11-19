from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

import pycountry

from .media import AudioTrack


@dataclass(frozen=True)
class GenerationRequest:
    video_path: Path
    audio_ordinal: int
    lang_code: str
    model_name: str


type ReportStatus = Callable[[str], None]
type GenerateSubtitles = Callable[[GenerationRequest, ReportStatus], Path]


def format_track_label(track: AudioTrack) -> str:
    return f"Track {track.stream_index} ({track.language_tag})"


def normalize_lang_code(code: str) -> str:
    code = code.lower()
    if len(code) == 2:
        return code

    try:
        language = pycountry.languages.get(alpha_3=code)
        if language and hasattr(language, "alpha_2"):
            return language.alpha_2
    except LookupError:
        pass
    return code


def make_generation_request(
    video_path: Path,
    tracks: Sequence[AudioTrack],
    selected_index: int,
    model_name: str,
) -> GenerationRequest:
    language_error = "Could not determine the language of the selected audio track."
    if not 0 <= selected_index < len(tracks):
        raise ValueError(language_error)

    track = tracks[selected_index]
    lang_code = normalize_lang_code(track.language_tag.strip())
    if (
        lang_code == "und"
        or len(lang_code) not in (2, 3)
        or not lang_code.isascii()
        or not lang_code.isalpha()
    ):
        raise ValueError(language_error)

    return GenerationRequest(video_path, track.audio_ordinal, lang_code, model_name)


def run_generation(
    generate: GenerateSubtitles,
    request: GenerationRequest,
    *,
    report_status: ReportStatus,
    report_error: Callable[[str], None],
    on_finished: Callable[[], None],
) -> None:
    try:
        srt_path = generate(request, report_status)
        report_status(f"Subtitles saved to {srt_path}")
    except Exception as error:
        report_error(str(error))
    finally:
        on_finished()
