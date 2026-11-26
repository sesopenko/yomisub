"""Contextual listening and ASR over detected overlap; continuous ASR stays independent."""

from dataclasses import replace
from fractions import Fraction

from .activity import overlap_cores
from .audio import ClockError, extract_crop
from .domain import ReviewFinding, SampleInterval
from .ports import AudioFile, Refinement, Stage, StageError


def anchored_interval(timing, source, clock):
    if timing.start is None or timing.end is None:
        return None
    scale = {"milliseconds": Fraction(source.sample_rate, 1000),
             "seconds": source.sample_rate, "samples": 1}[timing.unit]
    left, right = timing.start * scale, timing.end * scale
    if not source.leading_padding <= left < right <= source.frames - source.trailing_padding:
        return None
    a, b = (source.recording_sample(x, clock) for x in (left, right))
    return SampleInterval(clock, a, b) if 0 <= a < b <= clock.frames else None


def link_transcript(transcript, source, core):
    padding_only = []
    for seg in transcript.segments:
        interval = anchored_interval(seg.timing, source, core.interval.clock)
        if interval and (interval.end <= core.interval.start or core.interval.end <= interval.start):
            padding_only.append(seg.id)
    return replace(transcript, core_id=core.id, context_only_segment_ids=tuple(padding_only))


class OverlapRefiner:
    def __init__(self, placement, asr):
        self.placement = placement
        self.asr = asr

    def refine(self, request, track, scan, work, progress):
        files, transcripts, findings = [], [], []
        for i, core in enumerate(overlap_cores(scan, track.clock)):
            key = f"mix-retry-{i}"
            window = core.interval
            padding = 2 * track.clock.sample_rate
            try:
                crop = extract_crop(track.mix, track.original.source, window.start - padding,
                                    window.end + padding, track.clock, work / (key + ".wav"), key)
                crop = AudioFile(replace(crop.source, core_id=core.id), crop.path)
                files.append(crop)
                progress(f"Checking overlap {i + 1} on the original mix...")
                target = self.placement.resolve(Stage.RETRY_ASR)
                self.asr.preflight("large-v3", target, progress)
                decoded = self.asr.transcribe(crop, request.stream.language, "large-v3", target, work)
                transcripts.append(link_transcript(decoded, crop.source, core))
            except (StageError, OSError, ClockError) as error:
                findings.append(ReviewFinding(key + "-failed", str(error), (core.id,), window))
        return Refinement(tuple(files), tuple(transcripts), findings=tuple(findings))
