"""Choose phrase edges on the recording clock and recheck the final owner."""

from dataclasses import dataclass

from .domain import PlannedPhrase, ReviewFinding, SampleInterval
from .reconcile import intersects, ownership, reconcile
from .timing import anchored_interval


@dataclass(frozen=True)
class Spotted:
    phrases: tuple
    candidates: tuple
    findings: tuple


def valid_pieces(segment, source, clock):
    """Keep usable lexical intervals and the reason for every dropped anchor."""
    intervals = {}
    problems = []
    for piece in segment.pieces:
        if piece.span is None:
            continue
        timing = piece.timing
        part = anchored_interval(timing,source,clock)
        enclosing = segment.timing
        if (part is None or timing.unit != enclosing.unit or enclosing.start is None or enclosing.end is None
                or timing.start < enclosing.start or timing.end > enclosing.end):
            problems.append(piece.id)
        else:
            intervals[piece.id] = part
    return intervals, problems


def timed_parts(segment, source, clock, group, changed):
    lexical = [p for p in segment.pieces if p.span is not None]
    intervals, invalid = valid_pieces(segment,source,clock)
    cuts = []
    permitted = set(group.cut_offsets) if group and not changed else set()
    for left, right in zip(lexical,lexical[1:]):
        a,b = intervals.get(left.id),intervals.get(right.id)
        if left.span.end == right.span.start and left.span.end in permitted and a and b and a.end <= b.start:
            cuts.append(left.span.end)
    offsets = [0,*cuts,len(segment.text)]
    return [(a,b,[p for p in lexical if a <= p.span.start and p.span.end <= b])
            for a,b in zip(offsets,offsets[1:])], intervals, invalid


def select_edge(name, edit, piece, enclosing):
    if edit is not None:
        return edit.value
    for interval in (piece, enclosing):
        if interval is not None:
            return getattr(interval, name)
    return None


def display_span(clock, start, end):
    if start is None or end is None or not 0 <= start < end <= clock.frames:
        return None
    left = max(start, -clock.playback_offset * clock.sample_rate)
    right = min(end, (clock.playback_duration-clock.playback_offset) * clock.sample_rate)
    return SampleInterval(clock,left,right) if left < right else None


def spot(evidence, decisions=()):
    result = reconcile(evidence,decisions)
    sources = {s.id:s for s in evidence.sources}
    segments = {seg.id:seg for t in evidence.transcripts for seg in t.segments}
    groups = {g.segment_id:g for g in evidence.groups}
    edits = {}
    for d in decisions:
        if d.field not in ("add", "note"):
            edits.setdefault(d.target_id,{})[d.field] = d
    phrases = []
    findings = [*evidence.findings,*result.findings]
    clock = evidence.clock
    for candidate in result.candidates:
        segment = segments[candidate.segment_id]
        source = sources[candidate.source_id]
        fields = edits.get(candidate.id,{})
        if "suppress" in fields or not candidate.text.strip():
            continue
        if candidate.text.strip() in {"[音楽]","[拍手]","[Music]","[Applause]","♪","（音楽）"}:
            continue
        group = groups.get(segment.id)
        if group and group.diagnostic:
            findings.append(ReviewFinding(segment.id+"-grouping",group.diagnostic,(segment.id,),candidate.interval))
        parts, valid, unusable = timed_parts(segment,source,clock,group,"wording" in fields)
        if unusable:
            findings.append(ReviewFinding(segment.id+"-anchors","Missing, unordered or out-of-bounds lexical timing.",
                                          tuple(unusable),candidate.interval))
        # Do not cut a phrase at a reversal relative to its other proposed boundaries.
        if len(parts) > 1:
            edges = [v for _,_,pieces in parts for v in (valid.get(pieces[0].id),valid.get(pieces[-1].id))]
            if any(a and b and a.start>b.start for a,b in zip(edges,edges[1:])):
                parts,_,_ = timed_parts(segment,source,clock,None,False)
        for n,(a,b,pieces) in enumerate(parts):
            id = candidate.id if len(parts)==1 else f"{candidate.id}:part{n}"
            part_fields = {**fields, **edits.get(id,{})}
            if "suppress" in part_fields:
                continue
            interval = candidate.interval
            first = valid.get(pieces[0].id) if pieces else None
            last = valid.get(pieces[-1].id) if pieces else None
            start_edit = part_fields.get("start") if n==0 or id in edits else None
            end_edit = part_fields.get("end") if n==len(parts)-1 or id in edits else None
            start = select_edge("start",start_edit,first,interval if n==0 else None)
            end = select_edge("end",end_edit,last,interval if n==len(parts)-1 else None)
            bounds = display_span(clock,start,end)
            if bounds is None:
                findings.append(ReviewFinding(id+"-timing","Phrase has no ordered, playable pair of timing anchors.",
                                              candidate.evidence_ids,candidate.interval))
                continue
            owner_edit = part_fields.get("owner")
            owners = ownership(evidence.scan,bounds,segment,source,{p.id for p in pieces})
            owner = owner_edit.value if owner_edit else owners[0].voice if owners else None
            previous = candidate.owners[0].voice if candidate.owners else None
            if not owner_edit and previous and owner != previous:
                owner = None
            if candidate.secondary and not (candidate.wording_supported and owner and (first or start_edit) and (last or end_edit)):
                findings.append(ReviewFinding(id+"-second-line","Overlap line lacks confirmed wording, owner or outer anchors.",
                                              candidate.evidence_ids,bounds))
                continue
            if candidate.secondary and any(p.owner == owner and intersects(p.interval,bounds) for p in phrases):
                findings.append(ReviewFinding(id+"-same-voice","The same voice already has a line in this interval.",
                                              candidate.evidence_ids,bounds))
                continue
            text = part_fields["wording"].value if "wording" in part_fields else segment.text[a:b]
            if "wording" in part_fields and part_fields["wording"].subdivisions:
                decision = part_fields["wording"]
                for i,part in enumerate(decision.subdivisions):
                    speakers = ownership(evidence.scan,part.interval,None,source)
                    who = owner_edit.value if owner_edit else speakers[0].voice if speakers else None
                    phrases.append(PlannedPhrase(f"{id}:edit{i}",part.text,who,part.interval,
                                                 (*candidate.evidence_ids,decision.id)))
                continue
            if not text.strip():
                continue
            support = [*candidate.evidence_ids]
            support += [p.id for p in pieces if p.id in valid and (p is pieces[0] or p is pieces[-1])]
            support += [edit.id for field, edit in part_fields.items() if field not in ("start", "end")]
            support += [edit.id for edit in (start_edit, end_edit) if edit is not None]
            if owners and owner:
                support.extend(owners[0].evidence_ids)
            phrases.append(PlannedPhrase(id,text,owner,bounds,tuple(dict.fromkeys(support))))
    for d in decisions:
        if d.field == "add":
            phrases.append(PlannedPhrase(d.id,d.value,d.voice,d.interval,(d.id,d.target_id)))
        elif d.field == "note":
            findings.append(ReviewFinding(d.id,d.value,(d.id,d.target_id),d.interval))
    return Spotted(tuple(phrases),result.candidates,tuple(findings))
