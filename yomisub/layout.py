"""Lay out accepted phrases in stable recording-local speaker lanes."""

from collections import defaultdict
from fractions import Fraction
from itertools import count

from .domain import Lane, ReviewFinding, SampleInterval, ScreenState
from .ports import CuePlan
from .spotting import spot


def layout(clock, phrases):
    start = max(0,-clock.playback_offset * clock.sample_rate)
    end = min(clock.frames,(clock.playback_duration-clock.playback_offset) * clock.sample_rate)
    if end <= start:
        return (), ()
    starts, ends = defaultdict(list), defaultdict(list)
    rates, labels = {}, {}
    ordered = sorted(phrases,key=lambda p:(p.interval.start,p.id))
    for p in ordered:
        starts[p.interval.start].append(p)
        ends[p.interval.end].append(p)
        duration = Fraction(p.interval.end-p.interval.start,clock.sample_rate)
        rates[p.id] = len(p.text.strip()) / duration
        if p.owner and p.owner not in labels:
            labels[p.owner] = f"話者{len(labels)+1}"
    phrase_labels = {p.id:labels[p.owner] for p in ordered if p.owner and len(labels)>1}
    previous_lane, active = {}, {}
    states, findings = [], []
    times = sorted({start,end,*starts,*ends})
    for here, following in zip(times,times[1:]):
        for p in ends[here]:
            del active[p.id]
        busy = set(active.values())
        for p in starts[here]:
            lane = previous_lane.get(p.owner)
            if lane is None or lane in busy:
                lane = next(i for i in count() if i not in busy)
            active[p.id] = lane
            busy.add(lane)
            if p.owner:
                previous_lane[p.owner] = lane
        bounds = SampleInterval(clock,here,following)
        lanes = tuple(Lane(num,phrase_id,phrase_labels.get(phrase_id))
                      for phrase_id,num in sorted(active.items(),key=lambda pair:pair[1]))
        demand = sum((rates[l.phrase_id] for l in lanes),Fraction(0))
        states.append(ScreenState(bounds,lanes,demand))
        if len(lanes)>2:
            ids = tuple(l.phrase_id for l in lanes)
            findings.append(ReviewFinding(f"crowding-{here}-{following}","Three or more simultaneous phrases.",
                                          ids,bounds))
    return tuple(states),tuple(findings)


class CuePlanner:
    def plan(self,evidence,decisions):
        result = spot(evidence,decisions)
        phrases = tuple(sorted(result.phrases,key=lambda p:(p.interval.start,p.id)))
        states,findings = layout(evidence.clock,phrases)
        return CuePlan(phrases,states,result.findings+findings,result.candidates)
