import json
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AudioTrack:
    stream_index: int
    audio_ordinal: int
    language_tag: str


def probe_audio_tracks(video_path: Path) -> list[AudioTrack]:
    result = subprocess.run([
        "ffprobe", "-v", "error",
        "-select_streams", "a",
        "-show_entries", "stream=index:stream_tags=language",
        "-of", "json",
        str(video_path),
    ], capture_output=True, text=True, check=True)

    streams = json.loads(result.stdout).get("streams", [])
    return [
        AudioTrack(
            stream_index=stream["index"],
            audio_ordinal=audio_ordinal,
            language_tag=stream.get("tags", {}).get("language", "und"),
        )
        for audio_ordinal, stream in enumerate(streams)
    ]


def extract_audio(video_path: Path, audio_ordinal: int, audio_path: Path) -> None:
    subprocess.run([
        "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-i", str(video_path),
        "-map", f"0:a:{audio_ordinal}", "-ac", "1", "-ar", "16000",
        "-c:a", "pcm_s16le", str(audio_path),
    ], check=True)
