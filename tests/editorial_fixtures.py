from fractions import Fraction

from yomisub.activity import read_rttm
from yomisub.domain import (
    AudioSource, ModelRun, RawTiming, RecordingClock, SelectedStream, TextPiece, TextSpan, TranscriptSegment,
)
from yomisub.ports import Evidence, Transcript


def run(name, source):
    return ModelRun(name,source,"fixture","v1","model",(),"fixture","device")


def segment(id, text, start, end, pieces=(), decode="base"):
    tokens = []
    cursor = 0
    for i,(surface,a,b) in enumerate(pieces):
        span = TextSpan(cursor,cursor+len(surface))
        cursor = span.end
        tokens.append(TextPiece(f"{id}-{i}",i,surface,span,RawTiming(a,b,"milliseconds")))
    return TranscriptSegment(id,decode,text,RawTiming(start,end,"milliseconds"),tuple(tokens))


def evidence(base, turns=(), extra=(), groups=(), duration=10000):
    clock = RecordingClock(1000,duration,Fraction(0),Fraction(duration,1000))
    src = AudioSource("mix","original",1000,duration)
    rttm = '\n'.join(f"SPEAKER clip 1 {a/1000:.3f} {(b-a)/1000:.3f} <NA> <NA> {voice} <NA> <NA>"
                     for a,b,voice in turns)
    scan = read_rttm(rttm,"clip",run("scan","mix"),src,clock)
    sources = (AudioSource("original",None,1000,duration),src,*(s for s,tr in extra))
    return Evidence("clip",SelectedStream(1,0,"ja","mono"),clock,sources,
                    (Transcript(run("base","mix"),tuple(base)),*(tr for s,tr in extra)),
                    scan,(),tuple(groups),())


def retry(name, core, text, start, end, pieces, column=None, context_only=False):
    src=AudioSource(name,"mix",1000,10000,column=column,core_id=core)
    seg=segment(name+"-s",text,start,end,pieces,decode=name)
    return src,Transcript(run(name,name),(seg,),core,(seg.id,) if context_only else ())
