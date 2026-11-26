"""Reconcile original-mix readings with recording-local alternatives and voice evidence."""

from dataclasses import dataclass, replace
import unicodedata

from .activity import coverage, overlap_cores
from .domain import Attribution, AudioSource, PhraseCandidate, ReviewFinding, SampleInterval, TranscriptSegment
from .timing import anchored_interval


def wording(text):
    return "".join(c for c in unicodedata.normalize("NFKC", text) if c.isalnum()).casefold()


def intersects(left, right):
    return left is not None and right is not None and left.start < right.end and right.start < left.end


def ownership(scan, interval, segment, source, allowed_pieces=None):
    if interval is None:
        return ()
    stats = coverage(scan, interval)
    if len(stats.per_voice) == 1 and not stats.uncovered:
        voice = next(iter(stats.per_voice))
        ids = tuple(t.id for t in scan.turns if t.voice == voice and intersects(interval, t.interval))
        return (Attribution(voice,ids),)
    if not stats.simultaneous or segment is None:
        return ()
    support = {}
    enclosing = anchored_interval(segment.timing,source,interval.clock)
    for piece in segment.pieces:
        if piece.span is None or not wording(piece.surface) or (allowed_pieces is not None and piece.id not in allowed_pieces):
            continue
        part = anchored_interval(piece.timing,source,interval.clock)
        if (part is None or enclosing is None or not interval.start <= part.start < part.end <= interval.end
                or not enclosing.start <= part.start < part.end <= enclosing.end):
            continue
        solo = coverage(scan,part)
        if len(solo.per_voice) == 1 and not solo.uncovered:
            voice = next(iter(solo.per_voice))
            support.setdefault(voice, []).append(piece.id)
    if len(support) == 1:
        voice, ids = next(iter(support.items()))
        return (Attribution(voice,tuple(ids)),)
    return ()


@dataclass(frozen=True)
class Observation:
    segment: TranscriptSegment
    source: AudioSource
    interval: SampleInterval | None
    core_id: str | None
    context_only: bool


@dataclass(frozen=True)
class Reconciled:
    candidates: tuple[PhraseCandidate, ...]
    findings: tuple[ReviewFinding, ...]


def as_candidate(obs, scan, *, secondary=False, supported=True):
    seg = obs.segment
    return PhraseCandidate(seg.id, seg.text, (seg.id,), obs.interval,
                           ownership(scan,obs.interval,seg,obs.source), obs.source.id, seg.id,
                           secondary=secondary, wording_supported=supported,
                           core_ids=(obs.core_id,) if obs.core_id else ())


def overlay(candidate, decisions):
    for edit in decisions:
        if edit.target_id != candidate.id:
            continue
        ids = candidate.evidence_ids + (edit.id,)
        if edit.field == "wording":
            candidate = replace(candidate,text=edit.value,wording_supported=True,evidence_ids=ids)
        elif edit.field == "owner":
            candidate = replace(candidate,owners=(Attribution(edit.value,(edit.id,)),),evidence_ids=ids)
    return candidate


def reconcile(evidence, decisions=()):
    sources = {s.id:s for s in evidence.sources}
    base, mixes, stems = [], [], []
    cores = {c.id:c for c in overlap_cores(evidence.scan,evidence.clock)}
    findings = []
    for i, tr in enumerate(evidence.transcripts):
        source = sources[tr.run.source_id]
        for seg in tr.segments:
            if seg.run_id != tr.run.id:
                findings.append(ReviewFinding(seg.id+"-decode","Segment references a different decode.",(seg.id,)))
                continue
            interval = anchored_interval(seg.timing,source,evidence.clock)
            obs = Observation(seg,source,interval,tr.core_id,seg.id in tr.context_only_segment_ids)
            if i == 0:
                base.append(as_candidate(obs,evidence.scan))
            elif source.column is None:
                mixes.append(obs)
            else:
                stems.append(obs)
    secondary = []
    for obs in (*mixes,*stems):
        # The occurrence test precedes text comparison. Padding stays in the bundle.
        core = cores.get(obs.core_id)
        if not core or obs.context_only or not intersects(obs.interval,core.interval):
            continue
        matched_primary = []
        for i, primary in enumerate(base):
            if not intersects(obs.interval,primary.interval):
                continue
            if wording(primary.text) == wording(obs.segment.text):
                shared = min(primary.interval.end,obs.interval.end) - max(primary.interval.start,obs.interval.start)
                matched_primary.append((shared,i))
            else:
                base[i] = replace(primary,alternative_ids=primary.alternative_ids+(obs.segment.id,))
        if matched_primary:
            matched_primary.sort(reverse=True)
            if len(matched_primary) == 1 or matched_primary[0][0] > matched_primary[1][0]:
                index = matched_primary[0][1]
                primary = base[index]
                base[index] = replace(primary,evidence_ids=primary.evidence_ids+(obs.segment.id,))
            else:
                findings.append(ReviewFinding(obs.segment.id+"-occurrence","Retry could refer to multiple repetitions.",
                                              (obs.segment.id,),obs.interval))
            continue
        if obs.source.column is not None:
            continue
        corroboration = [s for s in stems if s.core_id == obs.core_id and not s.context_only
                         and intersects(s.interval,obs.interval) and intersects(s.interval,core.interval)
                         and wording(s.segment.text) == wording(obs.segment.text) and wording(obs.segment.text)]
        candidate = as_candidate(obs,evidence.scan,secondary=True,supported=bool(corroboration))
        ids = candidate.evidence_ids + tuple(s.segment.id for s in corroboration)
        same = next((i for i,c in enumerate(secondary) if intersects(c.interval,candidate.interval)
                     and wording(c.text) == wording(candidate.text)), None)
        if same is None:
            secondary.append(replace(candidate,evidence_ids=ids))
        else:
            prev = secondary[same]
            secondary[same] = replace(prev,evidence_ids=tuple(dict.fromkeys(prev.evidence_ids+ids)),
                                      core_ids=tuple(dict.fromkeys(prev.core_ids+candidate.core_ids)),
                                      wording_supported=prev.wording_supported or candidate.wording_supported)
    candidates = tuple(overlay(c,decisions) for c in (*base,*secondary))
    for c in candidates:
        edited = any(d.target_id == c.id and d.field == "wording" for d in decisions)
        if c.alternative_ids and not edited:
            findings.append(ReviewFinding(c.id+"-readings","Competing overlap readings; continuous wording retained.",
                                          (c.id,*c.alternative_ids),c.interval))
        if c.secondary and not (c.owners and c.wording_supported):
            findings.append(ReviewFinding(c.id+"-disputed","Second line needs wording and ownership evidence.",
                                          c.evidence_ids,c.interval))
    for turn in evidence.scan.turns:
        if turn.interval and not any(intersects(c.interval,turn.interval) and c.wording_supported
                                     and c.text.strip() not in {"[音楽]", "[拍手]", "♪"} for c in candidates):
            findings.append(ReviewFinding(turn.id+"-wordless","Voice activity has no supported wording.",
                                          (turn.id,),turn.interval))
    for core in cores.values():
        supplied = {at.voice for c in candidates if c.wording_supported and intersects(c.interval,core.interval)
                    for at in c.owners if at.voice}
        if set(core.voices) - supplied:
            findings.append(ReviewFinding(core.id+"-unresolved","Overlapping voice has no independently assigned words.",
                                          (core.id,),core.interval))
    return Reconciled(candidates,tuple(findings))
