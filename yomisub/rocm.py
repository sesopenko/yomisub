"""Application-side ROCm worker client. Only protocol data crosses interpreters."""

import json
import os
from pathlib import Path
import subprocess

from .ports import Device, ExecutionTarget, Stage, StageError


STAGES = frozenset((Stage.DIARIZATION, Stage.SEPARATION))
SETUP = "See runtime/amd/README.md."
RECOVERY = {
    "interpreter": "Install the separate Python 3.12 worker or set YOMISUB_ROCM_PYTHON.",
    "protocol": "Install matching Yomisub worker and application versions.",
    "weights": "Run the documented weights.py setup for this stage with approved model access.",
    "device": "Check ROCm device permissions, visibility and the selected PCI address.",
    "runtime": "Install the pinned ROCm worker dependencies and verify the model probe.",
}


def failure(code):
    return StageError(RECOVERY.get(code, RECOVERY["runtime"]) + " " + SETUP)


class RocmWorker:
    def __init__(self, python=None, weights=None):
        data = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "yomisub/amd"
        self.python = python or os.environ.get("YOMISUB_ROCM_PYTHON", data / "venv/bin/python")
        self.weights = Path(weights or os.environ.get("YOMISUB_ROCM_WEIGHTS", data / "weights"))
        self.script = Path(__file__).resolve().parents[1] / "runtime/amd/worker.py"

    def request(self, action, target=None, **params):
        msg = {"version": 1, "action": action, "weights": str(self.weights), **params}
        if target:
            if target.provider != AmdRocm.name or target.stage not in STAGES:
                raise failure("device")
            msg.update(stage=target.stage.value, device=target.physical_id)
        try:
            # The offline child needs driver and localisation settings. Give no registry credentials to ML code.
            keys = {"PATH", "HOME", "TMPDIR", "LANG", "LD_LIBRARY_PATH", "XDG_CACHE_HOME",
                    "ROCR_VISIBLE_DEVICES", "HIP_VISIBLE_DEVICES", "CUDA_VISIBLE_DEVICES", "GPU_DEVICE_ORDINAL"}
            env = {key: os.environ[key] for key in keys if key in os.environ}
            run = subprocess.run([str(self.python), "-E", "-s", str(self.script)], env=env, input=json.dumps(msg),
                                 capture_output=True, text=True, errors="replace")
        except OSError:
            raise failure("interpreter") from None
        if run.returncode:
            raise failure("runtime")
        try:
            response = json.loads(run.stdout)
            if response["version"] != 1:
                raise failure("protocol")
            if "error" in response:
                raise failure(response["error"])
            value = response["value"]
            if target and (value["device"], value["stage"]) != (target.physical_id, target.stage.value):
                raise failure("device")
            return value
        except (TypeError, AttributeError, KeyError, ValueError):
            raise failure("protocol") from None


class AmdRocm:
    name = "amd-rocm"

    def __init__(self, worker: RocmWorker):
        self.worker = worker

    def devices(self):
        return tuple(Device(d["id"], d["name"], STAGES) for d in self.worker.request("devices")["devices"])

    def bind(self, stage, physical_id):
        devices = [d for d in self.worker.request("devices")["devices"] if d["id"] == physical_id]
        if len(devices) != 1 or stage not in STAGES:
            raise failure("device")
        return ExecutionTarget(self.name, physical_id, devices[0]["index"], stage)
