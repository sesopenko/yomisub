"""Time PixIT on a Radeon and export the actual sources on a mono 16 kHz input clock."""

import argparse
import json
import os
import shlex
from pathlib import Path
from time import monotonic

import numpy as np
import soundfile as sf


def project_token():
    token = os.environ.get("HUGGING_FACE_TOKEN") or os.environ.get("HF_TOKEN")
    dotenv = Path(__file__).resolve().parents[1] / ".env"
    if token or not dotenv.exists():
        return token
    for line in dotenv.read_text().splitlines():
        key, _, value = line.partition("=")
        if key.strip().removeprefix("export ") == "HUGGING_FACE_TOKEN":
            fields = shlex.split(value, comments=True)
            return fields[0] if len(fields) == 1 else None
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wav", type=Path)
    parser.add_argument("output", type=Path, help="New directory for this run")
    parser.add_argument("--speakers", type=int, help="Supply a known recording-wide count")
    args = parser.parse_args()
    if args.speakers is not None and args.speakers < 1:
        parser.error("--speakers must be positive")
    audio, rate = sf.read(args.wav, dtype="float32")
    if rate != 16000 or audio.ndim != 1 or audio.size == 0:
        parser.error("Input must be a nonempty 16 kHz mono WAV")
    if args.output.exists():
        parser.error("Choose a new output directory for this run")

    os.environ.setdefault("MIOPEN_FIND_MODE", "FAST")
    import torch
    from pyannote.audio import Pipeline

    if not torch.version.hip or not torch.cuda.is_available():
        parser.error("This benchmark requires a ROCm build of PyTorch and a visible Radeon")
    torch.set_num_threads(4)
    started = monotonic()
    pipeline = Pipeline.from_pretrained(
        "pyannote/speech-separation-ami-1.0@9486b106945ae0cc0784041a08bfcdba5edadfb9",
        use_auth_token=project_token(),
    )
    if pipeline is None:
        parser.error("PixIT weights are unavailable to this Hugging Face environment")
    pipeline.to(torch.device("cuda"))
    models = (pipeline._segmentation.model, pipeline._embedding.classifier_.mods)
    devices = [next(model.parameters()).device.type for model in models]
    if devices != ["cuda", "cuda"]:
        raise RuntimeError("The separator and speaker embedding must both use the GPU")
    torch.cuda.synchronize()
    loaded = monotonic()
    print(f"Loaded PixIT on {torch.cuda.get_device_name(0)} in {loaded-started:.2f} s", flush=True)

    # With pyannote.audio 3.3.2 this grid retains integer cluster indices. It is
    # updated in place by the pipeline when the ASR collar is applied.
    grid = None

    def capture(step, artifact, **kwargs):
        nonlocal grid
        if step == "discrete_diarization":
            grid = artifact

    torch.cuda.reset_peak_memory_stats()
    source = {"uri": args.wav.stem, "sample_rate": rate, "waveform": torch.from_numpy(audio[None])}
    count = {} if args.speakers is None else {"num_speakers": args.speakers}
    turns, sources = pipeline(source, hook=capture, **count)
    torch.cuda.synchronize()
    seconds = monotonic() - loaded
    labels = turns.labels()
    stats = {"torch": torch.__version__, "hip": torch.version.hip, "gpu": torch.cuda.get_device_name(0),
             "gpu_arch": torch.cuda.get_device_properties(0).gcnArchName,
             "miopen_find_mode": os.environ["MIOPEN_FIND_MODE"], "supplied_speakers": args.speakers,
             "rate": rate, "input_frames": len(audio), "load_seconds": loaded - started,
             "pipeline_seconds": seconds, "real_time_factor": seconds * rate / len(audio),
             "peak_allocated_bytes": torch.cuda.max_memory_allocated(), "labels": labels,
             "native_source_frames": 0, "columns": {}, "labels_without_source": list(labels)}
    args.output.mkdir(parents=True)
    with (args.output / "turns.rttm").open("w") as f:
        turns.write_rttm(f)
    if sources is not None:
        data = sources.data
        sample_clock = sources.sliding_window
        if (not np.isfinite(data).all() or abs(sample_clock.start) >= 1 / rate
                or not np.isclose(1 / sample_clock.step, rate)):
            raise ValueError("Invalid sample values or an unexpected output clock")
        ann = pipeline.to_annotation(grid, min_duration_on=0.0, min_duration_off=0.0)
        ids = dict(zip(ann.labels(), labels, strict=True))
        gain = min(1.0, 0.99 / max(float(np.max(np.abs(data))), 1e-9))
        for index in range(data.shape[1]):
            name = ids.get(index, f"UNLABELED_COLUMN_{index:02d}")
            pcm = np.zeros_like(audio)
            n = min(len(audio), len(data))
            pcm[:n] = data[:n, index] * gain
            sf.write(args.output / f"{name}.wav", pcm, rate, subtype="PCM_16")
            stats["columns"][int(index)] = name
        stats.update(native_source_frames=len(data), export_gain=gain,
                     labels_without_source=[label for label in labels if label not in stats["columns"].values()])
    (args.output / "metrics.json").write_text(json.dumps(stats, indent=2) + "\n")
    print(json.dumps(stats, ensure_ascii=False))


if __name__ == "__main__":
    main()
