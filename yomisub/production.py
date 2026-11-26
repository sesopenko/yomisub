"""Composition root for the generation application and hardware-specific adapters."""

from dataclasses import dataclass

from .application import GenerateSubtitles, SubtitleEditor
from .asr import WhisperJSON
from .audio import FFmpegAudio
from .bundle import BundleStore
from .compute import ProviderRegistry, load_config
from .grouping import PhraseGrouping
from .layout import CuePlanner
from .ports import ComputeProvider, Scanner, Separator, Stage, Transcriber
from .publication import FilePublisher
from .refinement import OverlapRefiner
from .rocm import AmdRocm, RocmWorker
from .scanner import SpeakerScanner
from .stems import SepFormer, StemRefiner
from .vulkan import ASR_STAGES, AmdVulkan
from .writers import AssWriter, SrtWriter


@dataclass(frozen=True)
class ModelBackend:
    provider: ComputeProvider
    asr: Transcriber | None = None
    scanner: Scanner | None = None
    separator: Separator | None = None


class Transcribers(dict):
    def preflight(self, model, target, progress):
        return self[target.provider].preflight(model, target, progress)

    def transcribe(self, audio, language, model, target, work):
        return self[target.provider].transcribe(audio, language, model, target, work)


class Scanners(dict):
    def preflight(self, target):
        return self[target.provider].preflight(target)

    def scan(self, track, target, work):
        return self[target.provider].scan(track, target, work)


class Separators(dict):
    def separate(self, crop, target, work):
        return self[target.provider].separate(crop, target, work)


def amd_backends():
    worker = RocmWorker()
    vulkan = AmdVulkan()
    return (ModelBackend(vulkan, asr=WhisperJSON(vulkan)),
            ModelBackend(AmdRocm(worker), scanner=SpeakerScanner(worker), separator=SepFormer(worker)))


def build_generator(*, backends=None, config=None, audio=None):
    registry = ProviderRegistry(config if config is not None else load_config())
    asr, scanners, separators = Transcribers(), Scanners(), Separators()
    for backend in amd_backends() if backends is None else backends:
        stages = set()
        for adapter, table, capabilities in (
            (backend.asr, asr, ASR_STAGES),
            (backend.scanner, scanners, (Stage.DIARIZATION,)),
            (backend.separator, separators, (Stage.SEPARATION,)),
        ):
            if adapter is not None:
                stages.update(capabilities)
                table[backend.provider.name] = adapter
        registry.register(backend.provider, frozenset(stages))
    refiner = OverlapRefiner(registry, asr, StemRefiner(registry, separators, asr))
    return GenerateSubtitles(registry, audio or FFmpegAudio(), asr, scanners, refiner, PhraseGrouping(),
                             SubtitleEditor(CuePlanner(), SrtWriter(), AssWriter()), BundleStore(), FilePublisher())
