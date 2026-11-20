"""Decode prepared routes on Vulkan and export machine-draft ASS plus evidence."""

import argparse
import json
import subprocess
from pathlib import Path
from time import monotonic


def decode_batch(cli, model, jobs, directory, group):
    if not jobs:
        return 0.0
    args = [cli, "-m", model, "-l", "ja", "-t", "3", "-bs", "5", "-bo", "5", "-ojf"]
    for job in jobs:
        args.extend(["-f", directory / (job.get("wav", job["name"]) + ".wav"),
                     "-of", directory / job["name"]])
    log = directory / f"{group}.log"
    start = monotonic()
    with log.open("w") as handle:
        subprocess.run(args, stdout=handle, stderr=subprocess.STDOUT, check=True)
    seconds = monotonic() - start
    if "using Vulkan0 backend" not in log.read_text():
        raise RuntimeError(f"Missing evidence of Vulkan acceleration in {log}")
    return seconds


def read_hypotheses(job, manifest, directory):
    result = json.loads((directory / (job["name"] + ".json")).read_text())
    expected = (24, 80) if job["model"] == "medium" else (32, 128)
    if (result["model"]["text"]["layer"], result["model"]["mels"]) != expected:
        raise ValueError(f"Unexpected Whisper checkpoint for {job['name']}")
    hypotheses = []
    for segment in result["transcription"]:
        text = segment["text"].strip()
        if not text:
            continue
        origin = job["start"]
        rate = manifest["rate"]
        raw = [origin + round(segment["offsets"][k] * rate / 1000) for k in ("from", "to")]
        start, end = max(origin, raw[0]), min(job["end"], raw[1])
        speaker, lane = None, 0
        if job["kind"] == "core":
            block = manifest["blocks"][job["block"]]
            lane = job["source"] - 1
            speaker = block["candidate_ids"][lane]
            label = speaker or f"source {job['source']}?"
        else:
            owners = sorted({label for a, b, label in manifest["turns"] if a < end and b > start})
            speaker = owners[0] if len(owners) == 1 else None
            label = speaker or "?"
        hypotheses.append(dict(text=text, raw_samples=raw, start=start, end=end,
                               bounded=raw != [start, end], speaker_candidate=speaker,
                               label=label, lane=lane))
    return hypotheses


def ass_time(centiseconds):
    minutes, cs = divmod(centiseconds, 6000)
    hours, minutes = divmod(minutes, 60)
    return f"{hours}:{minutes:02d}:{cs // 100:02d}.{cs % 100:02d}"


def write_draft(path, jobs, rate):
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1280
PlayResY: 720
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Voice,Noto Sans CJK JP,34,&H00FFFFFF,&H00FFFFFF,&H00101010,&H80000000,0,0,0,0,100,100,0,0,1,2,1,2,35,35,20,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [header]
    for job in jobs:
        if job["kind"] not in ("core", "mix"):
            continue
        for h in job["hypotheses"]:
            a, b = (round(h[k] * 100 / rate) for k in ("start", "end"))
            if a >= b:
                continue
            y = 625 if h["lane"] == 1 else 680
            text = h["text"].replace("\\", "＼").replace("{", "｛").replace("}", "｝").replace("\n", " ")
            label = h["label"].replace("SPEAKER_", "voice ")
            lines.append(f"Dialogue: 0,{ass_time(a)},{ass_time(b)},Voice,,0,0,0,,"
                         f"{{\\pos(640,{y})}}[{label}] {text}\n")
    path.write_text("".join(lines))


def transcribe(directory, args):
    manifest = json.loads((directory / "routes.json").read_text())
    jobs = manifest["jobs"]
    timings = {}
    for group, model, kinds in (("routed-medium", args.medium, {"mix"}),
                                ("routed-large", args.large, {"core"}),
                                ("context-comparison", args.large, {"context", "context-mix"})):
        batch = [job for job in jobs if job["kind"] in kinds]
        timings[group] = decode_batch(args.cli, model, batch, directory, group)
    for size, model in (("medium", args.medium), ("large", args.large)):
        name = f"baseline-{size}"
        job = dict(name=name, wav="mix", model=size, kind="baseline", start=0, end=manifest["frames"])
        timings[name] = decode_batch(args.cli, model, [job], directory, name)
        jobs.append(job)
    for job in jobs:
        job["hypotheses"] = read_hypotheses(job, manifest, directory)
    write_draft(directory / "routed.ass", jobs, manifest["rate"])
    (directory / "results.json").write_text(json.dumps(dict(seconds=timings, jobs=jobs),
                                                      ensure_ascii=False, indent=2) + "\n")
    print(directory.name, {k: round(v, 2) for k, v in timings.items()}, flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cli", type=Path)
    parser.add_argument("medium", type=Path)
    parser.add_argument("large", type=Path)
    parser.add_argument("directories", type=Path, nargs="+")
    args = parser.parse_args()
    for directory in args.directories:
        transcribe(directory, args)


if __name__ == "__main__":
    main()
