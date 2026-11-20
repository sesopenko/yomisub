"""Extract an explicitly enrolled voice through a whole recording on Radeon."""

import argparse
import json
import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic

import numpy as np
import soundfile as sf


def load_release(directory):
    import torch

    sys.path.insert(0, str(directory.resolve()))
    from vi.infer import load_model

    if not torch.version.hip or not torch.cuda.is_available():
        raise RuntimeError("Scicom benchmark requires ROCm and a visible Radeon")
    model = load_model(directory, device="cuda:0")
    if not all(p.is_cuda for p in model.parameters()):
        raise RuntimeError("Some model parameters are off the GPU")
    return model


def extract(model, recording, enrollment, output):
    import torch

    reference, rate = sf.read(enrollment, dtype="float32")
    if rate != 16000 or reference.ndim != 1 or not len(reference):
        raise ValueError("Expected a nonempty mono 16 kHz enrollment")
    if output.exists():
        raise FileExistsError(output)
    device = next(model.parameters()).device
    hop = model.stft.hop
    delay = model.stft.win - hop
    chunk_hops = 100
    chunk = chunk_hops * hop
    elapsed = monotonic()
    torch.cuda.reset_peak_memory_stats()
    with TemporaryDirectory(dir=output.parent) as temp, torch.inference_mode(), sf.SoundFile(recording) as src:
        if src.samplerate != rate or src.channels != 1 or not len(src):
            raise ValueError("Expected a nonempty mono 16 kHz recording")
        frames = len(src)
        reference_tensor = torch.from_numpy(reference[None]).to(device)
        speaker = model.embed(reference_tensor, torch.tensor([len(reference)], device=device))
        state = model.stream_init(1, device, max_chunk=chunk_hops)
        # The publisher's causal WavLM release carries its context across chunks.
        # Keep the enrollment fixed, advance through silence and flush the delayed tail.
        temp_wav = Path(temp) / "voice.wav"
        with sf.SoundFile(temp_wav, mode="x", samplerate=rate, channels=1, subtype="FLOAT") as dest:
            for pos in range(0, frames + delay, chunk):
                block = src.read(chunk, dtype="float32")
                block = np.pad(block, (0, chunk - len(block)))
                y = model.stream_step(torch.from_numpy(block[None]).to(device), state, speaker)
                samples = y[0].float().cpu().numpy()
                if len(samples) != chunk or not np.all(np.isfinite(samples)):
                    raise ValueError("Invalid waveform returned by Scicom")
                start = max(delay - pos, 0)
                end = min(frames + delay - pos, chunk)
                dest.write(samples[start:end])
            if dest.tell() != frames:
                raise ValueError("Extracted voice is off the input clock")
        os.link(temp_wav, output)
    torch.cuda.synchronize()
    return {"input_frames": frames, "sample_rate": rate, "enrollment_frames": len(reference),
            "chunk_frames": chunk, "stream_delay_removed_samples": delay, "seconds": monotonic() - elapsed,
            "peak_allocated_bytes": torch.cuda.max_memory_allocated(), "gpu_arch": torch.cuda.get_device_properties(0).gcnArchName,
            "torch": torch.__version__, "hip": torch.version.hip}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", type=Path, help="Local Scicom GPU release with its vi package and weights")
    parser.add_argument("recording", type=Path)
    parser.add_argument("enrollment", type=Path)
    parser.add_argument("output", type=Path, help="New waveform path")
    args = parser.parse_args()
    os.environ.setdefault("MIOPEN_FIND_MODE", "FAST")
    os.environ.setdefault("VI_SERVE_BASELINE", "1")
    model = load_release(args.model)
    print(json.dumps(extract(model, args.recording, args.enrollment, args.output), indent=2))


if __name__ == "__main__":
    main()
