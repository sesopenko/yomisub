"""Run real AMD acceptance media through the same factory as GTK."""

import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
from time import monotonic

from yomisub.audio import FFmpegAudio
from yomisub.ports import GenerationRequest
from yomisub.production import build_generator


def generate(inputs, output, names):
    cases = json.loads(Path(__file__).with_name("references.json").read_text())["cases"]
    output.mkdir(parents=True, exist_ok=True)
    application = build_generator()
    for name in names or cases:
        case = cases[name]
        source = (inputs / case["local_input"]).resolve(strict=True)
        with source.open("rb") as recording:
            if hashlib.file_digest(recording, "sha256").hexdigest() != case["sha256"]:
                raise ValueError(f"Unexpected source hash for {name}")
        video = output / (name + source.suffix)
        if not video.exists():
            video.symlink_to(source)
        if not video.samefile(source):
            raise ValueError(f"Evaluation path {video} already points to another recording")
        track = FFmpegAudio().list_tracks(video)[case["audio_ordinal"]]
        if track.index != case["stream_index"]:
            raise ValueError(f"Selected track changed on {video}")
        # Several controls are WAVs without a container language tag.
        request = GenerationRequest(video, replace(track, language="ja"), model="medium")
        started = monotonic()
        application(request, lambda message: print(name, message, flush=True))
        (output / (name + ".time")).write_text(f"{monotonic() - started:.3f}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_root", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("cases", nargs="*")
    args = parser.parse_args()
    generate(args.input_root, args.output, args.cases)
