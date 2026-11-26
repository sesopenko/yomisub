"""Versioned, typed JSON and audio members for relocatable offline review."""

from dataclasses import fields, is_dataclass
from fractions import Fraction
from functools import cache
import json
from pathlib import Path
import re
from types import UnionType
from typing import Literal, get_args, get_origin, get_type_hints
from uuid import uuid4
from zipfile import BadZipFile, ZIP_STORED, ZipFile

from .activity import overlap_cores
from .domain import ReviewFinding
from .ports import CuePlan, Evidence


class BundleError(ValueError):
    pass


def encode(value):
    if isinstance(value,Fraction):
        return {"n":value.numerator,"d":value.denominator}
    if is_dataclass(value):
        return {f.name:encode(getattr(value,f.name)) for f in fields(value)}
    if isinstance(value,tuple):
        return [encode(v) for v in value]
    return value


@cache
def field_types(cls):
    return get_type_hints(cls)


def decode(kind, value):
    origin, args = get_origin(kind), get_args(kind)
    if kind is Fraction:
        if type(value) is int:
            return Fraction(value)
        if not isinstance(value,dict) or set(value)!={"n","d"}:
            raise ValueError("Invalid rational sample or time.")
        return Fraction(value["n"],value["d"])
    if origin is UnionType:
        for member in args:
            try:
                return decode(member,value)
            except (ValueError,TypeError):
                pass
        raise ValueError("Unexpected value type.")
    if origin is Literal:
        if value not in args:
            raise ValueError("Unsupported field value.")
        return value
    if origin is tuple:
        if not isinstance(value,list) or (args[-1] is not Ellipsis and len(args)!=len(value)):
            raise ValueError("Invalid sequence.")
        return tuple(decode(args[0] if args[-1] is Ellipsis else args[i],v) for i,v in enumerate(value))
    if is_dataclass(kind):
        types = field_types(kind)
        if not isinstance(value,dict) or not value.keys()<=types.keys():
            raise ValueError(f"Invalid {kind.__name__} fields.")
        return kind(**{k:decode(types[k],v) for k,v in value.items()})
    if type(value) is not kind and not (kind is float and type(value) is int):
        raise ValueError(f"Expected {kind.__name__}.")
    return value


def validate_name(stem,language):
    if not stem or stem in (".","..") or Path(stem).name!=stem or "\\" in stem or not re.fullmatch(r"[a-z]{2,3}",language):
        raise ValueError("Invalid output stem or language.")


def unique(items, key=lambda x:x.id):
    values = [key(item) for item in items]
    if len(set(values)) != len(values):
        raise ValueError("Duplicate evidence IDs.")
    return set(values)


def validate(e,plan,findings):
    validate_name(e.stem,e.stream.language)
    sources = unique(e.sources)
    if not {"original","mix"} <= sources:
        raise ValueError("Missing original or analysis waveform.")
    runs = [t.run for t in e.transcripts]+[e.scan.run,*e.other_runs]
    run_ids = unique(runs)
    if any(r.source_id not in sources for r in runs):
        raise ValueError("Model run references an unknown source.")
    known = set()
    for s in e.sources:
        if s.parent_id is not None and s.parent_id not in known:
            raise ValueError("Invalid waveform ancestry.")
        known.add(s.id)
    segs = [s for tr in e.transcripts for s in tr.segments]
    seg_ids = unique(segs)
    piece_ids = unique(p for s in segs for p in s.pieces)
    turns = unique(e.scan.turns)
    core_ids = {c.id for c in overlap_cores(e.scan,e.clock)}
    if any(s.core_id and s.core_id not in core_ids for s in e.sources):
        raise ValueError("Unknown overlap core.")
    for tr in e.transcripts:
        if any(s.run_id!=tr.run.id for s in tr.segments) or not set(tr.context_only_segment_ids)<= {s.id for s in tr.segments}:
            raise ValueError("Broken transcript or context reference.")
        if tr.core_id is not None and tr.core_id not in core_ids:
            raise ValueError("Broken transcript core reference.")
    if any(t.voice.run_id!=e.scan.run.id or (t.interval and t.interval.clock!=e.clock) for t in e.scan.turns):
        raise ValueError("Voice turn references a different scan or clock.")
    for g in e.groups:
        if g.segment_id not in seg_ids or any(not set(ids)<=piece_ids for ids in g.piece_ids):
            raise ValueError("Unknown grouping evidence.")
    phrases = unique(plan.phrases)
    candidates = unique(plan.candidates)
    decisions = unique(e.decisions)
    ids = known|run_ids|seg_ids|piece_ids|turns|phrases|candidates|decisions|core_ids
    for i,state in enumerate(plan.states):
        if state.interval.clock!=e.clock or any(l.phrase_id not in phrases for l in state.lanes):
            raise ValueError("Screen state references a missing phrase or clock.")
        ids.add(f"state-{i}")
    for c in plan.candidates:
        if (c.source_id not in sources or c.segment_id not in seg_ids or not set(c.alternative_ids)<=seg_ids
                or not set(c.core_ids)<=core_ids):
            raise ValueError("Broken candidate reference.")
    for obj in (*plan.phrases,*plan.candidates,*findings):
        if not set(obj.evidence_ids)<=ids or (obj.interval and obj.interval.clock!=e.clock):
            raise ValueError(f"Broken evidence reference on {obj.id}.")


class BundleStore:
    def save(self,destination,evidence,files,plan,open_findings):
        validate(evidence,plan,open_findings)
        if {f.source for f in files}!=set(evidence.sources) or len(files)!=len(evidence.sources):
            raise BundleError("Missing listening or analysis file for an evidence source.")
        members = {f.source.id:f"audio/{i:04}.wav" for i,f in enumerate(files)}
        manifest = {"schema":1,"planner":evidence.planner_version,"id":str(uuid4()),"audio":members,
                    "evidence":encode(evidence),"plan":encode(plan),"open_findings":encode(open_findings)}
        with ZipFile(destination,"x",compression=ZIP_STORED,allowZip64=True) as archive:
            archive.writestr("manifest.json",json.dumps(manifest,ensure_ascii=False,allow_nan=False).encode())
            for f in files:
                archive.write(f.path,members[f.source.id])

    def read(self,path):
        try:
            with ZipFile(path) as archive:
                doc=json.loads(archive.read("manifest.json"))
                if doc["schema"]!=1 or doc["planner"] not in (1,2):
                    raise ValueError("Unsupported bundle schema or planner version.")
                evidence=decode(Evidence,doc["evidence"])
                if evidence.planner_version != doc["planner"]:
                    raise ValueError("Inconsistent planner version.")
                plan=decode(CuePlan,doc["plan"])
                findings=decode(tuple[ReviewFinding,...],doc["open_findings"])
                validate(evidence,plan,findings)
                audio=doc["audio"]
                names=archive.namelist()
                if (set(audio)!={s.id for s in evidence.sources}
                        or any(not re.fullmatch(r"audio/[0-9]+\.wav",n) for n in audio.values())
                        or len(set(audio.values()))!=len(audio)
                        or sorted(names)!=sorted(["manifest.json",*audio.values()]) or archive.testzip()):
                    raise ValueError("Missing, damaged or unexpected audio member.")
                return doc["id"],evidence,plan,findings
        except (OSError,BadZipFile,ValueError,KeyError,TypeError,ArithmeticError,EOFError,RuntimeError) as error:
            raise BundleError(f"{path}: {error} Restore an intact, supported evidence bundle.") from error

    def load(self,path):
        return self.read(path)[1]
