from uuid import uuid4

from .activity import read_rttm
from .domain import ModelRun
from .ports import StageError
from .rocm import RocmWorker


class SpeakerScanner:
    def __init__(self, worker: RocmWorker):
        self.worker = worker

    def preflight(self, target):
        self.worker.request("probe", target)

    def scan(self, track, target, work):
        uri = f"scan-{uuid4().hex}"
        result = self.worker.request("scan", target, audio=str(track.mix.path), uri=uri)
        try:
            versions = result["versions"]
            run = ModelRun(uri, track.mix.source.id, "pyannote.audio",
                           f"{versions['pyannote']};torch={versions['torch']};hip={versions['hip']}",
                           "diarization-3.1@84fd2591/segmentation-3.0@e66f3d3b/wespeaker@837717dd",
                           ("whole-track", "automatic-speaker-count"), target.provider, target.physical_id,
                           result["elapsed_seconds"], result["peak_allocated_bytes"])
            scan = read_rttm(result["rttm"], uri, run, track.mix.source, track.clock)
            if result["rttm"].strip() and not scan.turns:
                raise StageError("Speaker scan returned activity for another recording.")
            return scan
        except (TypeError, KeyError) as error:
            raise StageError("Missing measurements in the speaker worker response. Check worker version.") from error
