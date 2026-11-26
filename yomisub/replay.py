"""Replay a version-one evidence bundle with optional listener corrections."""

import argparse
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

from .application import ReplaySubtitles, SubtitleEditor
from .bundle import BundleError, BundleStore, validate_name
from .domain import ListenerDecision, SampleInterval, TimedText, Voice
from .layout import CuePlanner
from .ports import ReplayRequest
from .writers import AssWriter, SrtWriter


class ReplayFiles:
    def write(self,directory,stem,language,srt,ass):
        validate_name(stem,language)
        directory.mkdir(parents=True,exist_ok=True)
        paths = tuple(directory/f"{stem}.{language}.{fmt}" for fmt in ("srt","ass"))
        if any(os.path.lexists(p) for p in paths):
            raise FileExistsError("Choose an output directory without existing subtitle files.")
        with TemporaryDirectory(dir=directory) as temp:
            linked = []
            try:
                for path,data in zip(paths,(srt,ass)):
                    staged = Path(temp)/path.name
                    staged.write_bytes(data)
                for path in paths:
                    os.link(Path(temp)/path.name,path)
                    linked.append(path)
            except OSError:
                for path in linked:
                    path.unlink()
                raise
        return paths


def interval(row,clock):
    a,b = row["start"],row["end"]
    if type(a) is not int or type(b) is not int:
        raise ValueError("Listener edges must be integer recording samples.")
    bounds = SampleInterval(clock,a,b)
    if not bounds.playable:
        raise ValueError("Listener interval is outside playable time.")
    return bounds


def read_corrections(path,bundle_id,evidence,plan):
    try:
        doc = json.loads(path.read_bytes())
        if doc["bundle"]!=bundle_id or not isinstance(doc["edits"],list):
            raise ValueError("Corrections must identify this bundle and contain an edits array.")
        candidates = {c.id:c for c in (*plan.candidates,*plan.phrases)}
        valid_ids = set(candidates)|{t.id for t in evidence.scan.turns}|{evidence.scan.run.id}
        seen, used = set(), {d.id for d in evidence.decisions}
        changes = []
        for row in doc["edits"]:
            id, target, listener, field = (row[k] for k in ("id","target","listener","field"))
            if not all(isinstance(k,str) and k.strip() for k in (id,target,listener,field)):
                raise ValueError("Each edit needs a stable ID, target and named listener.")
            if id in used or id in valid_ids or target not in valid_ids:
                raise ValueError("Duplicate edit ID or unknown target.")
            if field not in ("add","note") and ((target,field) in seen or target not in candidates):
                raise ValueError("Conflicting edits or invalid phrase target.")
            seen.add((target,field))
            used.add(id)
            val = row.get("value")
            bounds,voice,parts = None,None,()
            if field in ("start","end"):
                if type(val) is not int or not 0 <= val <= evidence.clock.frames or not 0<=evidence.clock.playback_time(val)<=evidence.clock.playback_duration:
                    raise ValueError("Timing edit exceeds the recording or playback clock.")
            elif field == "owner":
                if val is not None:
                    if not isinstance(val,str) or not val.strip():
                        raise ValueError("Owner must be a listener label or null.")
                    val = Voice("listener",val)
            elif field == "suppress":
                val = None
            elif field in ("add","note","wording"):
                if not isinstance(val,str) or not val.strip():
                    raise ValueError("Listener text may not be empty.")
                if field in ("add","note"):
                    bounds = interval(row,evidence.clock)
                if field == "add" and "owner" in row:
                    if not isinstance(row["owner"],str) or not row["owner"].strip():
                        raise ValueError("Invalid listener owner.")
                    voice=Voice("listener",row["owner"])
                if "parts" in row:
                    if field!="wording":
                        raise ValueError("Timed subdivisions require a wording edit.")
                    parts=tuple(TimedText(v["text"],interval(v,evidence.clock)) for v in row["parts"])
                    if (not parts or any(not isinstance(p.text,str) or not p.text for p in parts)
                            or ''.join(p.text for p in parts)!=val or any(a.interval.end>b.interval.start for a,b in zip(parts,parts[1:]))):
                        raise ValueError("Timed subdivisions must reconstruct the replacement in order.")
            else:
                raise ValueError("Unsupported correction field.")
            changes.append(ListenerDecision(id,target,listener,field,val,bounds,voice,parts))
        for target in {d.target_id for d in changes}:
            group=[d for d in changes if d.target_id==target and d.field not in ("add","note")]
            if any(d.field=="suppress" for d in group) and len(group)>1:
                raise ValueError("Suppression conflicts with another field edit.")
            if any(d.subdivisions for d in group) and any(d.field in ("start","end") for d in group):
                raise ValueError("Outer timing edits conflict with timed subdivisions.")
            child_ids = {p.id for p in plan.phrases if p.id.startswith(target + ":part")}
            if group and any(d.target_id in child_ids and d.field not in ("add", "note") for d in changes):
                raise ValueError("Edit the whole candidate or its displayed parts in one batch.")
        return tuple(changes)
    except (ValueError,KeyError,TypeError) as error:
        raise BundleError(f"{path}: {error} Check the corrections against manifest.json.") from error


def replay(bundle,output,corrections=None):
    store=BundleStore()
    id,evidence,plan,_=store.read(bundle)
    changes=read_corrections(corrections,id,evidence,plan) if corrections else ()
    editor=SubtitleEditor(CuePlanner(),SrtWriter(),AssWriter())
    if changes:
        edited=editor.planner.plan(evidence,evidence.decisions+changes)
        used={eid for p in edited.phrases for eid in p.evidence_ids}
        if any(d.field in ("start","end","wording","add") and d.id not in used for d in changes):
            raise BundleError(f"{corrections}: An edit has no valid displayed interval. Check the target and both timing edges.")
    return ReplaySubtitles(editor,store,ReplayFiles()).replay_evidence(evidence,ReplayRequest(bundle,output,changes))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("bundle",type=Path)
    p.add_argument("output",type=Path)
    p.add_argument("--corrections",type=Path)
    args=p.parse_args()
    try:
        result=replay(args.bundle,args.output,args.corrections)
    except (OSError,ValueError) as error:
        p.exit(1,f"{error}\n")
    print(result.srt,result.ass,sep="\n")


if __name__=="__main__":
    main()
