"""FFmpeg track selection, decoded PCM preparation and sample-exact excerpt mapping."""

from fractions import Fraction
import json
from math import ceil, floor
from pathlib import Path
import subprocess
import wave

from .domain import AudioSource, RecordingClock, SelectedStream
from .ports import AudioFile, GenerationRequest, PreparedTrack
from .workflow import normalize_lang_code


class ClockError(ValueError):
    """The decoded PCM cannot be related reliably to the playback timeline."""


def probe(path, *args):
    result = subprocess.run(
        ["ffprobe", "-v", "error", *args, "-of", "json", str(path)],
        check=True, capture_output=True, text=True,
    )
    return json.loads(result.stdout)


def selected_streams(streams):
    return tuple(
        SelectedStream(s["index"], i, normalize_lang_code(s.get("tags", {}).get("language", "und")),
                       s.get("channel_layout") or f"{s['channels']} channels")
        for i, s in enumerate(x for x in streams if x["codec_type"] == "audio")
    )


def decoded_origin(frames, rate, time_base):
    """Accept container tick rounding, rejecting gaps or trims our WAV cannot represent."""
    origin = None
    samples = 0
    for frame in frames:
        try:
            timestamp = int(frame["best_effort_timestamp"]) * time_base
            count = int(frame["nb_samples"])
        except (KeyError, ValueError) as error:
            raise ClockError("Selected audio has no decoded sample timestamp or count.") from error
        if origin is None:
            origin = timestamp
        if abs(timestamp - origin - Fraction(samples, rate)) > time_base or count <= 0:
            raise ClockError("Selected audio has a discontinuity in its decoded sample clock.")
        samples += count
    if origin is None:
        raise ClockError("Selected audio contains no decoded frames.")
    return origin, samples


def video_span(path, stream):
    base = Fraction(stream["time_base"])
    if "start_pts" in stream and "duration_ts" in stream:
        return int(stream["start_pts"]) * base, int(stream["duration_ts"]) * base
    packets = probe(path, "-select_streams", str(stream["index"]),
                    "-show_entries", "packet=pts,duration")["packets"]
    try:
        start = min(int(p["pts"]) for p in packets)
        end = max(int(p["pts"]) + int(p["duration"]) for p in packets)
    except (ValueError, KeyError) as error:
        raise ClockError("Video playback origin or duration is unavailable.") from error
    return start * base, (end - start) * base


def write_pcm(source, path, *options):
    subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
                    "-i", str(source), *options, "-c:a", "pcm_s16le", str(path)], check=True)


def audio_dimensions(path):
    with wave.open(str(path), "rb") as src:
        return src.getframerate(), src.getnframes(), src.getnchannels()


class FFmpegAudio:
    def list_tracks(self, video: Path) -> tuple[SelectedStream, ...]:
        return selected_streams(probe(video, "-show_streams")["streams"])

    def prepare(self, request: GenerationRequest, work: Path) -> PreparedTrack:
        streams = probe(request.video, "-show_streams")["streams"]
        selected = next((s for s in selected_streams(streams)
                         if (s.index, s.audio_ordinal) == (request.stream.index, request.stream.audio_ordinal)), None)
        if selected is None:
            raise ClockError("Selected audio stream has changed. Choose the track again.")
        stream = next(s for s in streams if s["index"] == selected.index)
        native = int(stream["sample_rate"])
        frames = probe(request.video, "-select_streams", str(selected.index), "-show_entries",
                       "frame=best_effort_timestamp,nb_samples")["frames"]
        first, count = decoded_origin(frames, native, Fraction(stream["time_base"]))
        video = next((s for s in streams if s["codec_type"] == "video"
                      and not s.get("disposition", {}).get("attached_pic")), None)
        origin, duration = video_span(request.video, video) if video else (first, Fraction(count, native))
        original = work / "original.wav"
        mix = work / "mix.wav"
        write_pcm(request.video, original, "-map", f"0:{selected.index}")
        if audio_dimensions(original) != (native, count, stream["channels"]):
            raise ClockError("Decoded audio dimensions differ from the probed frame clock.")
        write_pcm(original, mix, "-map", "0:a:0", "-ac", "1", "-ar", "16000")
        rate, mix_count, channels = audio_dimensions(mix)
        if channels != 1 or rate != 16000 or abs(mix_count - Fraction(count * rate, native)) > 1:
            raise ClockError("Resampled mix does not share the selected audio timeline.")
        clock = RecordingClock(native, count, first - origin, duration, origin)
        return PreparedTrack(clock, AudioFile(AudioSource("original", None, native, count), original),
                             AudioFile(AudioSource("mix", "original", rate, mix_count), mix))


def extract_crop(parent: AudioFile, request_clock: AudioSource, start, end,
                 clock: RecordingClock, path: Path, source_id: str) -> AudioFile:
    """Read outward-rounded parent samples for a half-open request on any derived clock."""
    requested = (request_clock.recording_sample(start, clock), request_clock.recording_sample(end, clock))
    src = parent.source
    def local(sample):
        return (sample - src.origin) * src.sample_rate / clock.sample_rate + src.leading_padding + src.delay
    left = max(0, floor(local(requested[0])))
    right = min(src.frames, ceil(local(requested[1])))
    if end <= start or right <= left:
        raise ClockError("Requested excerpt lies outside the available recording.")
    with wave.open(str(parent.path), "rb") as source, wave.open(str(path), "wb") as destination:
        destination.setparams(source.getparams())
        source.setpos(left)
        destination.writeframes(source.readframes(right - left))
    actual = AudioSource(source_id, src.id, src.sample_rate, right - left,
                         src.recording_sample(left, clock), requested_recording_bounds=requested)
    return AudioFile(actual, path)
