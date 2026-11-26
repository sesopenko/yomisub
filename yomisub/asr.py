"""Continuous, multilingual whisper.cpp observations. No cue or speaker decisions."""

from functools import cache
import json
from pathlib import Path
import shutil
import subprocess
from typing import Protocol
from uuid import uuid4

from .domain import ModelRun, RawTiming, TextPiece, TextSpan, TranscriptSegment
from .models import CHECKPOINTS, digest, get_model_path
from .ports import AudioFile, ExecutionTarget, StageError, Transcript
from .vulkan import check_cli


class WhisperRunner(Protocol):
    def invoke(self, executable, args, target: ExecutionTarget) -> subprocess.CompletedProcess: ...


def raw_time(record):
    edges = record.get("offsets", {})
    return RawTiming(edges.get("from"), edges.get("to"), "milliseconds")


def parse_transcript(document, run):
    if document["model"]["multilingual"] is not True:
        raise ValueError("Expected a multilingual Whisper checkpoint.")
    # whisper.cpp's multilingual vocabulary increments token_eot from 50256.
    eot = 50257
    segments = []
    for n, seg in enumerate(document["transcription"]):
        segment_id = f"{run.id}:s{n}"
        raw = seg["tokens"]
        text = seg["text"]
        reconstructs = ''.join(t["text"] for t in raw if t["id"] < eot) == text
        pieces = []
        cursor = 0
        for i, token in enumerate(raw):
            surface = token["text"]
            span = None
            if reconstructs and token["id"] < eot:
                span = TextSpan(cursor, cursor + len(surface))
                cursor = span.end
            dtw = token.get("t_dtw", -1)
            pieces.append(TextPiece(f"{segment_id}:t{i}", token["id"], surface, span,
                                    raw_time(token), token.get("p"), dtw if dtw >= 0 else None))
        segments.append(TranscriptSegment(segment_id, run.id, text, raw_time(seg), tuple(pieces)))
    return Transcript(run, tuple(segments))


@cache
def cli_build(executable, binary_sha):
    check_cli(executable, ("--device", "--output-json-full", "--language", "--output-file"))
    result = subprocess.run([str(executable), "--version"], text=True, capture_output=True, check=True)
    return f"{(result.stdout + result.stderr).strip()} sha256:{binary_sha}"


class WhisperJSON:
    def __init__(self, runner: WhisperRunner, executable=None, cache_dir=None):
        self.runner = runner
        self.executable = executable
        self.cache_dir = cache_dir

    def _resources(self, model, progress):
        executable = self.executable or shutil.which("whisper-cli")
        if not executable:
            raise StageError("Add Vulkan-enabled whisper-cli to PATH as described in README.md.")
        if model not in CHECKPOINTS:
            raise StageError(f"Unknown multilingual checkpoint {model!r}.")
        try:
            executable = Path(executable)
            build = cli_build(executable, digest(executable, "sha256"))
            weights = get_model_path(model, progress, cache_dir=self.cache_dir, expected_sha1=CHECKPOINTS[model])
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
            raise StageError(f"Check the Whisper runtime and {model} checkpoint: {error}") from error
        return executable, build, weights

    def preflight(self, model, target, progress):
        self._resources(model, progress)

    def transcribe(self, audio: AudioFile, language, model, target, work):
        executable, build, weights = self._resources(model, lambda message: None)
        run_id = f"{target.stage}-{uuid4().hex}"
        output = work / run_id
        options = ("-l", language, "-bs", "5", "-bo", "5", "-ojf")
        self.runner.invoke(executable, ["-m", str(weights), "-f", str(audio.path), "-of", str(output),
                                        *options], target)
        run = ModelRun(run_id, audio.source.id, "whisper.cpp", build, f"{model}:sha1:{CHECKPOINTS[model]}",
                       options, target.provider, target.physical_id)
        try:
            return parse_transcript(json.loads(output.with_suffix(".json").read_bytes()), run)
        except (OSError, KeyError, TypeError, ValueError) as error:
            raise StageError(f"Invalid full JSON from whisper-cli for {audio.source.id}: {error}") from error
