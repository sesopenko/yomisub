"""Verify offline corrections separately from automatic acceptance scores."""

import argparse
from hashlib import file_digest
import json
from pathlib import Path

from yomisub.bundle import BundleStore
from yomisub.layout import CuePlanner
from yomisub.replay import read_corrections, replay
from .acceptance import check_ass, check_srt
from .score import normalized, score_phrases


def digest(path):
    with path.open("rb") as src:
        return file_digest(src, "sha256").hexdigest()


def check_review(directory, destination, name, make_edits):
    bundle = directory / f"{name}.ja.yomisub.zip"
    original = digest(bundle)
    bundle_id, ev, plan, _ = BundleStore().read(bundle)
    edits = make_edits(ev, plan)
    out = destination / name
    out.mkdir(parents=True, exist_ok=True)
    correction = out / "edits.json"
    correction.write_text(json.dumps({"bundle": bundle_id, "edits": edits}, ensure_ascii=False, indent=2))
    decisions = read_corrections(correction, bundle_id, ev, plan)
    result = replay(bundle, out, correction)
    corrected = CuePlanner().plan(ev, decisions)
    displays = check_srt(result.srt, corrected)
    check_ass(result.ass, corrected)
    if digest(bundle) != original:
        raise RuntimeError("Correction changed input bundle")
    return corrected, displays


def fight(ev, plan):
    refs = (("こうします", "A"), ("そう", "B"), ("耐えられる?", "B"))
    edits = []
    for text, owner in refs:
        phrase, = [p for p in plan.phrases if normalized(p.text) == normalized(text)]
        edits.append(dict(id=f"fight-{len(edits)}", target=phrase.id, listener="Sean (recorded research)",
                          field="owner", value=owner))
    return edits


def song(ev, plan):
    def sample(second):
        return int((second-ev.clock.playback_offset)*ev.clock.sample_rate)
    return [dict(id="instrumental", target=ev.scan.run.id, listener="Sean (recorded research)",
                 field="note", start=sample(19), end=sample(29), value="Verified instrumental break."),
            dict(id="chorus", target=ev.scan.run.id, listener="Sean (recorded research)", field="note",
                 start=sample(78), end=min(ev.clock.frames, sample(ev.clock.playback_duration)),
                 value="Chorus audible, words unresolved.")]


def staggered_fixture(ev, plan):
    # The constructed tracks establish the two voices and texts. These display
    # intervals exercise layout only. They are not human phrase-edge annotations.
    edits = []
    cases = [("広場", 12.5, 16.375, "A"), ("ただ酒", 14, 19, "B")]
    for surface, start, end, owner in cases:
        matches = [p for p in plan.phrases if ev.clock.playback_time(p.interval.start) >= 12
                   and surface in p.text]
        if not matches:
            raise ValueError(f"Missing {surface} in fixture mix")
        phrase = matches[0]
        for field, value in (("owner", owner), ("start", int(start*ev.clock.sample_rate)),
                             ("end", int(end*ev.clock.sample_rate))):
            edits.append(dict(id=f"fixture-{owner}-{field}", target=phrase.id,
                              listener="layout fixture", field=field, value=value))
        for other in matches[1:]:
            edits.append(dict(id=f"fixture-duplicate-{len(edits)}", target=other.id,
                              listener="layout fixture", field="suppress"))
    return edits


def three_voice_fixture(ev, plan):
    return [dict(id=f"fixture-{voice}", target=ev.scan.run.id, listener="three-voice layout fixture",
                 field="add", start=ev.clock.sample_rate, end=2*ev.clock.sample_rate,
                 owner=voice, value=text)
            for voice, text in (("A", "駅まで。"), ("B", "待って。"), ("C", "こっち。"))]


def report(directory, destination):
    _, displays = check_review(directory, destination, "S01E03", fight)
    ref = json.loads(Path(__file__).with_name("references.json").read_text())["cases"]["S01E03"]["phrases"]
    fight_results = score_phrases(ref, displays, owner_map={"A": "A", "B": "B"})
    if any(r.get("ownership") != "correct" for r in fight_results.values()):
        raise ValueError("Corrected A/B/B did not survive both exports")
    corrected, _ = check_review(directory, destination, "S01E02", song)
    notes = {f.id:f.reason for f in corrected.findings if f.id in ("chorus", "instrumental")}
    if len(notes) != 2:
        raise ValueError("Missing interval notes")
    fixture, _ = check_review(directory, destination, "mix", staggered_fixture)
    phrases = {p.id:p for p in fixture.phrases}
    active = []
    for time in (13, 15, 17, 20):
        state, = [s for s in fixture.states if s.interval.clock.playback_time(s.interval.start) <= time
                  < s.interval.clock.playback_time(s.interval.end)]
        active.append([(phrases[l.phrase_id].owner.label, l.number) for l in state.lanes])
    if [[voice for voice, _ in row] for row in active] != [["A"], ["A", "B"], ["B"], []]:
        raise ValueError(f"Unexpected staggered fixture states: {active}")
    if active[0][0] != active[1][0] or active[1][1] != active[2][0]:
        raise ValueError("Continuing phrase changed lane")
    crowded, _ = check_review(directory, destination, "S01E10-multi-speakers", three_voice_fixture)
    fixture_ids = {"fixture-A", "fixture-B", "fixture-C"}
    if not any(fixture_ids <= {l.phrase_id for l in s.lanes} for s in crowded.states):
        raise ValueError("A listener-supplied third phrase was lost")
    if not any(fixture_ids <= set(f.evidence_ids) and f.id.startswith("crowding-") for f in crowded.findings):
        raise ValueError("Missing crowding diagnostic")
    return {"corrected_fight": fight_results, "corrected_song_notes": notes,
            "staggered_layout_fixture": active, "three_voice_layout_fixture": "three distinct lanes and crowding finding"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("fresh_output_directory", type=Path)
    args = parser.parse_args()
    print(json.dumps(report(args.directory, args.fresh_output_directory), ensure_ascii=False, indent=2))
