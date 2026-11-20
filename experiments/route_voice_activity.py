"""Scan recordings and prepare sample-aligned inputs for the overlap routing experiment."""

import argparse
import json
import os
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from time import monotonic

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

from benchmark_sepformer_rocm import separate

RATE = 16000
PADDING = 2 * RATE


def activity_spans(turns, frames):
    """Partition the entire recording at changes in active recording-local IDs."""
    edges = defaultdict(Counter)
    for start, end, speaker in turns:
        if start < end:
            edges[start][speaker] += 1
            edges[end][speaker] -= 1
    active = Counter()
    spans = []
    previous = 0
    for edge in sorted({0, frames, *edges}):
        labels = sorted(label for label, count in active.items() if count > 0)
        if previous < edge:
            if spans and spans[-1][2] == labels:
                spans[-1][1] = edge
            else:
                spans.append([previous, edge, labels])
        active.update(edges[edge])
        previous = edge
    return spans


def routes(spans):
    """Keep contiguous non-overlap audio together so medium can use sentence context."""
    blocks = []
    for start, end, ids in spans:
        overlap = ids if len(ids) > 1 else []
        if blocks and blocks[-1][2] == overlap:
            blocks[-1][1] = end
        else:
            blocks.append([start, end, overlap])
    return blocks


def unit_embedding(embed, signal):
    import torch

    if len(signal) < RATE or np.max(np.abs(signal)) < 1e-6:
        return None
    value = embed(torch.from_numpy(signal[None, None]))[0]
    norm = np.linalg.norm(value)
    return value / norm if np.isfinite(norm) and norm > 0 else None


def get_references(spans, audio, embed, ids):
    refs = {}
    for label in ids:
        solo = [(a, b) for a, b, labels in spans if labels == [label]]
        if solo:
            a, b = max(solo, key=lambda interval: interval[1] - interval[0])
            mid = (a + b) // 2
            a, b = max(a, mid - 2 * RATE), min(b, mid + 2 * RATE)
            refs[label] = (a, b, unit_embedding(embed, audio[a:b]))
    return refs


def match_sources(tracks, ids, refs, embed):
    # Require both independent solo references and opposed, distinct preferences.
    guesses = [None, None]
    scores = []
    for track in tracks:
        vector = unit_embedding(embed, track)
        row = {}
        for label in ids:
            ref = refs.get(label)
            if ref and ref[2] is not None and vector is not None:
                row[label] = float(vector @ ref[2])
        scores.append(row)
    if all(len(row) == 2 for row in scores):
        best = [max(row, key=row.get) for row in scores]
        if len(set(best)) == 2 and all(row[label] >= 0.35 and
                max(row.values()) - min(row.values()) >= 0.10 for row, label in zip(scores, best)):
            guesses = best
    return guesses, scores


def prepare(path, out, pipeline, separator, stream):
    import torch

    out.mkdir()
    started = monotonic()
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", path, "-map", stream,
                    "-ac", "1", "-ar", str(RATE), "-c:a", "pcm_s16le", out / "mix.wav"], check=True)
    audio, _ = sf.read(out / "mix.wav", dtype="float32")
    scan_start = monotonic()
    ann = pipeline({"uri": path.stem, "waveform": torch.from_numpy(audio[None]), "sample_rate": RATE})
    torch.cuda.synchronize()
    scan_seconds = monotonic() - scan_start
    turns = [[max(0, round(seg.start * RATE)), min(len(audio), round(seg.end * RATE)), label]
             for seg, _, label in ann.itertracks(yield_label=True)]
    spans = activity_spans(turns, len(audio))
    ids = sorted({label for _, _, labels in spans if len(labels) == 2 for label in labels})
    embed = pipeline._embedding
    refs = get_references(spans, audio, embed, ids)
    jobs = []
    blocks = []
    for i, (a, b, labels) in enumerate(routes(spans)):
        name = f"block-{i:02d}"
        block = dict(start=a, end=b, speakers=labels)
        blocks.append(block)
        if not labels:
            if any(voices and start < b and end > a for start, end, voices in spans):
                sf.write(out / f"{name}.wav", audio[a:b], RATE, subtype="PCM_16")
                jobs.append(dict(name=name, model="medium", kind="mix", start=a, end=b))
            continue
        if len(labels) != 2 or b - a > 12 * RATE:
            block["review"] = "outside the two-source, 12-second-core experiment"
            continue
        left, right = max(0, a - PADDING), min(len(audio), b + PADDING)
        block.update(context_start=left, context_end=right)
        sf.write(out / f"{name}-context.wav", audio[left:right], RATE, subtype="PCM_16")
        stats = separate(separator, out / f"{name}-context.wav", out / name)
        block["separator_seconds"] = stats["inference_seconds"]
        cores = []
        for index in (1, 2):
            stem, _ = sf.read(out / name / f"source-{index}.wav", dtype="float32")
            wide = resample_poly(stem, 2, 1)[:right-left]
            peak = np.max(np.abs(wide))
            if peak > 1:
                wide /= peak
            core = wide[a-left:b-left]
            cores.append(core)
            for kind, signal, start, end in (("core", core, a, b), ("context", wide, left, right)):
                file = f"{name}-src{index}-{kind}"
                sf.write(out / f"{file}.wav", signal, RATE, subtype="PCM_16")
                jobs.append(dict(name=file, model="large", kind=kind, block=i, source=index,
                                 start=start, end=end))
        block["candidate_ids"], block["cosines"] = match_sources(cores, labels, refs, embed)
        # Compare identical context without separation or a bandwidth limit.
        jobs.append(dict(name=f"{name}-context", model="large", kind="context-mix",
                         block=i, start=left, end=right))
    manifest = dict(input=str(path.resolve()), stream=stream, frames=len(audio), rate=RATE,
                    turns=turns, spans=spans, blocks=blocks, jobs=jobs, scan_seconds=scan_seconds,
                    prepare_seconds=monotonic()-started,
                    reference_samples={k: [a, b] for k, (a, b, _) in refs.items()})
    (out / "routes.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(path.name, f"{scan_seconds:.2f}s scan,", [(round(x["start"]/RATE, 3),
          round(x["end"]/RATE, 3), x["speakers"]) for x in blocks if x["speakers"]], flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("separator", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("inputs", type=Path, nargs="+")
    parser.add_argument("--stream", default="0:a:0", help="FFmpeg audio stream selector")
    args = parser.parse_args()
    if len({p.stem for p in args.inputs}) != len(args.inputs):
        parser.error("Each input must have a distinct stem")
    args.output.mkdir(parents=True, exist_ok=False)
    os.environ.setdefault("PYANNOTE_CACHE", str(Path.home() / ".cache/torch/pyannote"))
    os.environ.setdefault("MPLCONFIGDIR", str(args.output.resolve() / "mpl"))
    os.environ.update(HF_HUB_OFFLINE="1", MIOPEN_FIND_MODE="FAST", TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD="1")
    import torch
    from pyannote.audio import Pipeline
    from speechbrain.inference.separation import SepformerSeparation

    if not torch.version.hip or not torch.cuda.is_available():
        raise RuntimeError("The experiment requires ROCm and a visible AMD GPU")
    torch.set_num_threads(4)
    started = monotonic()
    pipe = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1").to(torch.device("cuda"))
    model = SepformerSeparation.from_hparams(source=str(args.separator.resolve()), run_opts={"device": "cuda:0"})
    if not all(p.is_cuda for mod in (pipe._segmentation.model, pipe._embedding.model_, model.mods)
               for p in mod.parameters()):
        raise RuntimeError("Model parameters must be on the GPU")
    if model.hparams.sample_rate != 8000 or model.hparams.num_spks != 2:
        raise ValueError("Expected the two-source 8 kHz WHAMR model")
    info = dict(gpu=torch.cuda.get_device_name(0), hip=torch.version.hip, load_seconds=monotonic()-started)
    (args.output / "runtime.json").write_text(json.dumps(info, indent=2) + "\n")
    print(info, flush=True)
    for path in args.inputs:
        prepare(path, args.output / path.stem, pipe, model, args.stream)


if __name__ == "__main__":
    main()
