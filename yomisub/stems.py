"""Excerpt-local separation and independent stem transcriptions."""

from dataclasses import replace
from uuid import uuid4

from .domain import AudioSource, ModelRun, ReviewFinding
from .ports import AudioFile, Refinement, Separation, Stage, StageError
from .refinement import link_transcript


def analysis_source(stem, frames):
    return replace(stem, id=stem.id + "-16k", parent_id=stem.id, sample_rate=16000, frames=frames,
                   leading_padding=stem.leading_padding * 2, trailing_padding=stem.trailing_padding * 2,
                   delay=stem.delay * 2)


class SepFormer:
    def __init__(self, worker):
        self.worker = worker

    def separate(self, crop, target, work):
        output = work / (crop.source.id + "-stems")
        output.mkdir()
        result = self.worker.request("separate", target, audio=str(crop.path), output=str(output))
        try:
            run = ModelRun(f"separation-{uuid4().hex}", crop.source.id, "SpeechBrain/SepFormer",
                           result["versions"]["speechbrain"], "sepformer-whamr@9950fd8055b38679d2af5bef2366b5dba600ec66",
                           ("two-speakers", "8000Hz", "resample_poly", "bounded-peak-16k"),
                           target.provider, target.physical_id, result["elapsed_seconds"], result["peak_allocated_bytes"])
            if result["analysis_frames"] != crop.source.frames or result["frames"] != (crop.source.frames + 1)//2:
                raise StageError("Separator output length does not map to the input crop.")
            stems, analysis = [], []
            for col in (1, 2):
                source = AudioSource(f"{crop.source.id}:stem{col}", crop.source.id, 8000, result["frames"],
                                     crop.source.origin, column=col, core_id=crop.source.core_id)
                path = output / f"stem-{col}.wav"
                if path.is_file():
                    stems.append(AudioFile(source, path))
                    wide = output / f"stem-{col}-16k.wav"
                    if wide.is_file():
                        analysis.append(AudioFile(analysis_source(source,result["analysis_frames"]), wide))
            return Separation(run,tuple(stems),tuple(analysis))
        except (KeyError, TypeError) as error:
            raise StageError("Separator worker returned incomplete source mapping.") from error


class StemRefiner:
    def __init__(self, placement, separator, asr):
        self.placement = placement
        self.separator = separator
        self.asr = asr

    def refine_core(self, core, crop, language, work, progress):
        key = crop.source.id
        def finding(suffix, reason):
            return ReviewFinding(key + suffix, reason, (core.id, crop.source.id), core.interval)
        if len(core.voices) != 2 or core.interval.end-core.interval.start > 12*core.interval.clock.sample_rate:
            return Refinement(findings=(finding("-stem-bound", "Stem analysis requires two voices and a core of at most 12 seconds."),))
        try:
            target = self.placement.resolve(Stage.SEPARATION)
            progress("Separating two voices for listening...")
            separated = self.separator.separate(crop,target,work)
        except (OSError, StageError) as error:
            return Refinement(findings=(finding("-separation-failed",str(error)),))
        files = (*separated.stems,*separated.analysis)
        runs = []
        findings = []
        present = {a.source.column for a in separated.analysis}
        for col in sorted({1, 2} - present):
            findings.append(finding(f"-missing-{col}",f"Stem {col} listening or transcription waveform is unavailable."))
        for audio in separated.analysis:
            try:
                target = self.placement.resolve(Stage.STEM_ASR)
                self.asr.preflight("large-v3",target,progress)
                run = self.asr.transcribe(audio,language,"large-v3",target,work)
                runs.append(link_transcript(run,audio.source,core))
            except (OSError,StageError) as error:
                findings.append(finding(f"-stem-{audio.source.column}-asr", str(error)))
        return Refinement(files,tuple(runs),(separated.run,),tuple(findings))
