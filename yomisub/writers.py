"""Serialize the common cue plan at each format's native time precision."""

from collections import defaultdict
from fractions import Fraction
from html import escape
from math import floor

from .domain import ReviewFinding
from .ports import Rendered


def ticks(bounds, scale, cache):
    clock = bounds.clock
    for sample in (bounds.start,bounds.end):
        if sample not in cache:
            nearest = floor(clock.playback_time(sample) * scale + Fraction(1,2))
            cache[sample] = max(0,min(nearest,floor(clock.playback_duration*scale)))
    return cache[bounds.start],cache[bounds.end]


def timestamp(value, scale):
    sec,frac = divmod(value,scale)
    minutes,s = divmod(sec,60)
    h,m = divmod(minutes,60)
    if scale==1000:
        return f"{h:02}:{m:02}:{s:02},{frac:03}"
    return f"{h}:{m:02}:{s:02}.{frac:02}"


def caption(phrase,lane):
    label = f"【{lane.label}】" if lane.label else ""
    return label + phrase.text.strip()


class SrtWriter:
    def render(self,plan):
        phrases = {p.id:p for p in plan.phrases}
        blocks = []
        cache = {}
        lost = defaultdict(list)
        for i,state in enumerate(plan.states):
            if not state.lanes:
                continue
            start,end = ticks(state.interval,1000,cache)
            if end<=start:
                for lane in state.lanes:
                    lost[lane.phrase_id].append(f"state-{i}")
                continue
            lines = [escape(caption(phrases[l.phrase_id],l),quote=False) for l in state.lanes]
            blocks.append(f"{len(blocks)+1}\n{timestamp(start,1000)} --> {timestamp(end,1000)}\n"
                          + "\n".join(lines) + "\n\n")
        findings = tuple(ReviewFinding(f"srt-precision-{id}","SRT precision collapsed a screen state.",
                                       (id,*states),phrases[id].interval) for id,states in lost.items())
        return Rendered(''.join(blocks).encode(),findings)


ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1280
PlayResY: 720
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Voice,Noto Sans CJK JP,{size},&H00FFFFFF,&H00FFFFFF,&H00101010,&H80000000,0,0,0,0,100,100,0,0,1,2,0,2,30,30,20,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def ass_literal(text):
    # libass interprets backslash-N/n/h specially. A nonprinting word joiner
    # keeps a literal backslash visible without changing the next glyph.
    return text.replace("\\","\\\u2060").replace("{","\\{").replace("}","\\}").replace("\r\n","\n").replace("\r","\n").replace("\n","\\N")


class AssWriter:
    def render(self,plan):
        lanes = {lane.phrase_id:lane for state in plan.states for lane in state.lanes}
        count = max((l.number+1 for l in lanes.values()),default=1)
        spacing = min(56, max(1,660//count))
        blocks = [ASS_HEADER.format(size=min(34,max(1,spacing*2//3)))]
        findings = []
        cache = {}
        for p in plan.phrases:
            start,end = ticks(p.interval,100,cache)
            if end<=start:
                findings.append(ReviewFinding("ass-precision-"+p.id,"ASS precision collapsed this phrase.",
                                              (p.id,),p.interval))
                continue
            lane = lanes[p.id]
            y = 680 - spacing*lane.number
            blocks.append(f"Dialogue: 0,{timestamp(start,100)},{timestamp(end,100)},Voice,,0,0,0,,"
                          + "{\\pos(640," + str(y) + ")}" + ass_literal(caption(p,lane)) + "\n")
        return Rendered(''.join(blocks).encode(),tuple(findings))
