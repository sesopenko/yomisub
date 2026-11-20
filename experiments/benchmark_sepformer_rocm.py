"""Measure the two-output WHAMR SepFormer on mono 16 kHz research excerpts."""

import argparse
import json
import os
from pathlib import Path
from time import monotonic

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly


def separate(model, path, output):
    import torch

    samples, rate = sf.read(path, dtype="float32")
    if rate != 16000 or samples.ndim != 1 or not len(samples):
        raise ValueError(f"Expected a nonempty mono 16 kHz recording in {path}")
    narrowband = resample_poly(samples, 1, 2)
    batch = torch.from_numpy(narrowband[None]).to(model.device)
    torch.cuda.synchronize()
    torch.cuda.reset_peak_memory_stats()
    started = monotonic()
    with torch.inference_mode():
        estimates = model.separate_batch(batch)
    torch.cuda.synchronize()
    seconds = monotonic() - started
    if not estimates.is_cuda or estimates.shape != (1, len(narrowband), 2):
        raise ValueError(f"Unexpected device or output shape for {path}")
    tracks = estimates[0].cpu().numpy()
    if not np.isfinite(tracks).all():
        raise ValueError(f"Non-finite estimate for {path}")
    output.mkdir()
    sf.write(output / "mix-8k.wav", narrowband, 8000, subtype="FLOAT")
    for index, track in enumerate(tracks.T, start=1):
        sf.write(output / f"source-{index}.wav", track, 8000, subtype="FLOAT")
    return {
        "input": str(path), "frames_16k": len(samples), "frames_8k": len(narrowband),
        "inference_seconds": seconds, "peak_allocated_bytes": torch.cuda.max_memory_allocated(),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", type=Path, help="Local WHAMR inference YAML and three checkpoints")
    parser.add_argument("output", type=Path, help="Fresh directory for this run")
    parser.add_argument("wav", type=Path, nargs="+")
    args = parser.parse_args()
    if len({path.stem for path in args.wav}) != len(args.wav) or args.output.exists():
        parser.error("Choose distinct input stems and a new output directory")

    os.environ.setdefault("MIOPEN_FIND_MODE", "FAST")
    import torch
    from speechbrain.inference.separation import SepformerSeparation

    if not torch.version.hip or not torch.cuda.is_available():
        parser.error("This benchmark requires ROCm and a visible Radeon")
    torch.set_num_threads(4)
    started = monotonic()
    model = SepformerSeparation.from_hparams(source=str(args.model.resolve()), run_opts={"device": "cuda:0"})
    if model.hparams.sample_rate != 8000 or model.hparams.num_spks != 2:
        raise ValueError("Expected the two-speaker 8 kHz configuration")
    if not all(p.is_cuda for p in model.mods.parameters()):
        raise RuntimeError("Some separator parameters are off the GPU")
    torch.cuda.synchronize()
    results = {
        "load_seconds": monotonic() - started, "gpu": torch.cuda.get_device_name(0),
        "architecture": torch.cuda.get_device_properties(0).gcnArchName, "hip": torch.version.hip,
        "torch": torch.__version__, "clips": {},
    }
    print(f"Loaded separator on {results['gpu']} ({results['architecture']})", flush=True)
    args.output.mkdir(parents=True)
    for path in args.wav:
        stats = separate(model, path, args.output / path.stem)
        results["clips"][path.stem] = stats
        (args.output / "metrics.json").write_text(json.dumps(results, indent=2) + "\n")
        print(path.stem, stats, flush=True)


if __name__ == "__main__":
    main()
