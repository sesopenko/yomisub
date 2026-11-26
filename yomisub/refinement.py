"""Contextual listening and ASR over detected overlap; continuous ASR stays independent."""

from dataclasses import replace

from .activity import overlap_cores
from .audio import ClockError, extract_crop
from .domain import ReviewFinding
from .timing import anchored_interval
from .ports import AudioFile, Refinement, Stage, StageError


def link_transcript(transcript, source, core):
    padding_only = []
    for seg in transcript.segments:
        interval = anchored_interval(seg.timing, source, core.interval.clock)
        if interval and (interval.end <= core.interval.start or core.interval.end <= interval.start):
            padding_only.append(seg.id)
    return replace(transcript, core_id=core.id, context_only_segment_ids=tuple(padding_only))


class OverlapRefiner:
    def __init__(self, placement, asr, stems=None):
        self.stems = stems
        self.placement = placement
        self.asr = asr

    def refine(self, request, track, scan, work, progress):
        files, transcripts, runs, findings = [], [], [], []
        for i, core in enumerate(overlap_cores(scan, track.clock)):
            key = f"mix-retry-{i}"
            window = core.interval
            padding = 2 * track.clock.sample_rate
            try:
                crop = extract_crop(track.mix, track.original.source, window.start - padding,
                                    window.end + padding, track.clock, work / (key + ".wav"), key)
                crop = AudioFile(replace(crop.source, core_id=core.id), crop.path)
                files.append(crop)
            except (OSError, ClockError) as error:
                findings.append(ReviewFinding(key + "-failed", str(error), (core.id,), window))
                continue
            try:
                progress(f"Checking overlap {i + 1} on the original mix...")
                target = self.placement.resolve(Stage.RETRY_ASR)
                self.asr.preflight("large-v3", target, progress)
                decoded = self.asr.transcribe(crop, request.stream.language, "large-v3", target, work)
                transcripts.append(link_transcript(decoded, crop.source, core))
            except (StageError, OSError, ClockError) as error:
                findings.append(ReviewFinding(key + "-failed", str(error), (core.id,), window))
            if request.analyze_stems and self.stems is not None:
                extra = self.stems.refine_core(core, crop, request.stream.language, work, progress)
                files.extend(extra.files)
                transcripts.extend(extra.transcripts)
                runs.extend(extra.runs)
                findings.extend(extra.findings)
        return Refinement(tuple(files), tuple(transcripts), tuple(runs), tuple(findings))
