"""Headless request and result presentation for the GTK worker."""

from dataclasses import replace

from .ports import GenerationRequest
from .workflow import normalize_lang_code


def selected_request(video, tracks, index, model, analyze_stems=False):
    if not 0 <= index < len(tracks):
        raise ValueError("Choose an audio track before generating subtitles.")
    stream = tracks[index]
    language = normalize_lang_code(stream.language.strip())
    if language == "und" or len(language) not in (2, 3) or not (language.isascii() and language.isalpha()):
        raise ValueError("Choose an audio track with a valid language tag.")
    return GenerationRequest(video, replace(stream, language=language), model, analyze_stems)


def result_message(result):
    count = len(result.findings)
    noun = "item" if count == 1 else "items"
    lines = [f"Saved subtitles and evidence. {count} {noun} to review.", str(result.srt), str(result.ass),
             str(result.bundle)]
    failures = [f.reason for f in result.findings if "failed" in f.id]
    if failures:
        lines.append(failures[0])
    return "\n".join(lines)


def run_job(generate, request, report_status, report_error, on_finished):
    try:
        result = generate(request, report_status)
        report_status(result_message(result))
    except Exception as error:
        report_error(str(error))
    finally:
        on_finished()
