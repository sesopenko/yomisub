from datetime import timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

import srt


def write_subtitles(transcript_path: Path, video_path: Path, lang_code: str) -> Path:
    subtitles = list(srt.parse(transcript_path.read_text(encoding="utf-8")))
    for subtitle in subtitles:
        subtitle.end = min(
            subtitle.end + timedelta(seconds=0.5),
            subtitle.start + timedelta(seconds=6),
        )

    srt_path = video_path.with_name(f"{video_path.stem}.{lang_code}.srt")
    with TemporaryDirectory(prefix=".yomisub-", dir=srt_path.parent) as temp_dir:
        output_path = Path(temp_dir) / srt_path.name
        output_path.write_text(srt.compose(subtitles), encoding="utf-8")
        output_path.replace(srt_path)
    return srt_path
