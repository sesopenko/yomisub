"""Score delivered subtitles against frozen references and check export fidelity."""

import argparse
from collections import Counter
from datetime import timedelta
from fractions import Fraction
from html import unescape
import json
from pathlib import Path
import re

import srt

from yomisub.activity import overlap_cores
from yomisub.bundle import BundleStore
from .score import Display, interval_result, map_owners, overlap_events, paired, score_phrases


def edge(interval, point, scale):
    clock = interval.clock
    value = clock.playback_time(getattr(interval, point)) * scale + Fraction(1, 2)
    return min(int(clock.playback_duration * scale), max(0, int(value)))


def check_srt(path, plan):
    phrases = {p.id: p for p in plan.phrases}
    actual = list(srt.parse(path.read_text(encoding="utf8")))
    expected = [st for st in plan.states if st.lanes and edge(st.interval, "start", 1000) < edge(st.interval, "end", 1000)]
    displays = []
    for cue, state in zip(actual, expected, strict=True):
        a, b = (point // timedelta(milliseconds=1) for point in (cue.start, cue.end))
        if [a, b] != [edge(state.interval, k, 1000) for k in ("start", "end")]:
            raise ValueError(f"{path}: inconsistent screen-state timing")
        for line, lane in zip(cue.content.splitlines(), state.lanes, strict=True):
            phrase = phrases[lane.phrase_id]
            prefix = f"【{lane.label}】" if lane.label else ""
            if unescape(line) != prefix + phrase.text.strip():
                raise ValueError(f"{path}: text or label differs from planned line")
            text = unescape(line)[len(prefix):]
            owner = phrase.owner.label if phrase.owner else None
            displays.append(Display(a, b, text, owner))
    return displays


def ass_time(text):
    h, m, s = text.split(":")
    return int((3600*int(h) + 60*int(m) + Fraction(s))*100)


def check_ass(path, plan):
    lines = [l.split(",", 9) for l in path.read_text().splitlines() if l.startswith("Dialogue:")]
    phrases = [p for p in plan.phrases if edge(p.interval, "start", 100) < edge(p.interval, "end", 100)]
    lanes = {l.phrase_id:l for st in plan.states for l in st.lanes}
    coordinates = {}
    for line, phrase in zip(lines, phrases, strict=True):
        if list(map(ass_time, line[1:3])) != [edge(phrase.interval, k, 100) for k in ("start", "end")]:
            raise ValueError(f"{path}: ASS phrase timing differs")
        prefix = f"【{lanes[phrase.id].label}】" if lanes[phrase.id].label else ""
        position = re.match(r"^\{\\pos\((\d+),(\d+)\)\}", line[-1])
        if position is None:
            raise ValueError(f"{path}: ASS event has no fixed lane")
        lane = lanes[phrase.id].number
        point = position.groups()
        if coordinates.setdefault(lane, point) != point or len(set(coordinates.values())) != len(coordinates):
            raise ValueError(f"{path}: ASS lanes moved or collided")
        text = line[-1][position.end():]
        text = text.replace(r"\N", "\n").replace(r"\{", "{").replace(r"\}", "}").replace("\u2060", "")
        if text != prefix + phrase.text.strip():
            raise ValueError(f"{path}: ASS text or label differs")


def score_case(directory, name, ref):
    stem = directory / f"{name}.ja"
    bundle = Path(str(stem) + ".yomisub.zip")
    _, ev, plan, findings = BundleStore().read(bundle)
    displays = check_srt(Path(str(stem) + ".srt"), plan)
    check_ass(Path(str(stem) + ".ass"), plan)
    refs = ref["phrases"]
    first = score_phrases(refs, displays)
    mapping = map_owners([(first[r["id"]].get("display_owner"), r.get("owner")) for r in refs])
    scores = score_phrases(refs, displays, owner_map=mapping)
    events = [[round(ev.clock.playback_time(s)*1000) for s in (c.interval.start, c.interval.end)]
              for c in overlap_cores(ev.scan, ev.clock)]
    model_runs = [t.run for t in ev.transcripts] + [ev.scan.run, *ev.other_runs]
    wordless = [(edge(f.interval, "start", 1000), edge(f.interval, "end", 1000))
                for f in findings if f.interval and f.id.endswith(("-unresolved", "-wordless"))]
    expected_events = ref["waveform_overlap_ms"]
    review_checks = {}
    if name == "S01E01":
        def owners_in(a, b):
            return {p.owner for p in plan.phrases if p.owner and
                    a <= ev.clock.playback_time(p.interval.start) < b}
        review_checks["aside_recurs"] = bool(owners_in(25, 30) & owners_in(39, 40))
        review_checks["aside_wording_flagged"] = any(f.id.endswith("-wording") and f.interval and
            39 <= ev.clock.playback_time(f.interval.start) < 40 for f in findings)
    if name == "S01E02":
        review_checks["closing_chorus"] = interval_result(
            (78000, int(ev.clock.playback_duration*1000)), displays,
            [(edge(f.interval, "start", 1000), edge(f.interval, "end", 1000)) for f in findings
             if f.interval and f.id.startswith("untranscribed-")])
    return {
        "review_checks": review_checks,
        "input_sha256": ref["sha256"], "stream": [ev.stream.index, ev.stream.audio_ordinal, ev.stream.language],
        "wall_seconds": float((directory / (name+".time")).read_text()), "distinct_findings": len(findings),
        "runs": [{"source": r.source_id, "engine": r.engine, "build": r.build, "options": r.options,
                  "backend": r.backend, "device": r.device_id,
                  "model_revision": r.model_revision, "seconds": r.elapsed_seconds,
                  "peak_allocated_bytes": r.peak_allocated_bytes} for r in model_runs],
        "verified_export_parity": True, "phrase_scores": scores, "owner_mapping": mapping,
        "owners": dict(Counter(r.get("ownership") for r in scores.values() if r["recovered"])),
        "observed_overlap_ms": events,
        "overlap": overlap_events(expected_events, events) if expected_events is not None else None,
        "verified_no_dialogue": [[a,b,interval_result((a,b), displays, wordless)] for a,b in ref["verified_no_dialogue_ms"]],
    }


def report(directory):
    here = Path(__file__).parent
    refs = json.loads((here / "references.json").read_text())["cases"]
    legacy = json.loads((here / "legacy-scores.json").read_text())
    cases = {name: score_case(directory, name, ref) for name, ref in refs.items()}
    before, after = {}, {}
    for name, data in cases.items():
        before.update({name+"/"+k:v for k,v in legacy[name].items()})
        after.update({name+"/"+k:v for k,v in data["phrase_scores"].items()})
    comparison = paired(before, after)
    exchange = cases["S01E01"]
    gates = {
        "legacy_recovered_ids_preserved": comparison["coverage_pass"],
        "paired_independent_edges_improved": comparison["timing_pass"],
        "ordinary_exchange": exchange["owners"] == {"correct": 2} and len(exchange["owner_mapping"]) == 2,
        "recurring_voice_and_uncertain_spelling": all(exchange["review_checks"].values()),
        "constructed_overlaps": all(cases[name]["overlap"]["hits"] == 1 and
                                    cases[name]["overlap"]["false_positives"] == 0 for name in ("mix", "together")),
        "alternating_control": not cases["serial"]["observed_overlap_ms"],
        "instrumental_break_clear": all(outcome != "displayed" for _, _, outcome in cases["S01E02"]["verified_no_dialogue"]),
        "closing_chorus_unresolved": cases["S01E02"]["review_checks"]["closing_chorus"] == "abstained",
        "both_exports_match_plan": all(c["verified_export_parity"] for c in cases.values()),
    }
    return {"cases": cases, "paired": comparison, "automatic_gates": gates}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    result = report(args.directory)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if all(result["automatic_gates"].values()) else 1)
