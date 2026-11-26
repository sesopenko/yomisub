"""One versioned JSON request per process. Imported ML libraries run only here."""

import contextlib
import ctypes
from importlib.metadata import version
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from time import monotonic

from weights import SCAN, SEPARATOR, verified


class WorkerError(Exception):
    pass


def devices(torch):
    hip = ctypes.CDLL(str(Path(torch.__file__).parent / "lib" / "libamdhip64.so"))
    result = []
    for i in range(torch.cuda.device_count()):
        bus = ctypes.create_string_buffer(32)
        if hip.hipDeviceGetPCIBusId(bus, len(bus), i) != 0:
            raise WorkerError("device")
        identity = bus.value.decode("ascii").lower()
        result.append({"id": "pci:" + identity, "index": i, "name": torch.cuda.get_device_name(i)})
    return result


def load_model(operation, root, device):
    files = SCAN if operation == "diarization" else SEPARATOR
    try:
        if not all(verified(root / name, spec[-1]) for name, spec in files.items()):
            raise WorkerError("weights")
    except OSError:
        raise WorkerError("weights") from None
    if operation == "diarization":
        import yaml
        from pyannote.audio.pipelines import SpeakerDiarization

        config = yaml.safe_load((root / "config.yaml").read_text())
        params = dict(config["pipeline"]["params"], segmentation=str(root / "segmentation.bin"),
                      embedding=str(root / "embedding.bin"))
        model = SpeakerDiarization(**params)
        model.instantiate(config["params"])
        model.to(device)
        modules = (model._segmentation.model, model._embedding.model_)
    else:
        from speechbrain.inference.separation import SepformerSeparation

        with TemporaryDirectory() as temp:
            model = SepformerSeparation.from_hparams(source=str(root / "separator"), savedir=temp,
                                                     run_opts={"device": str(device)})
        modules = (model.mods,)
    if any(p.device != device for mod in modules for p in mod.parameters()):
        raise WorkerError("device")
    return model


def execute(request):
    if request.get("version") != 1:
        raise WorkerError("protocol")
    if sys.version_info[:2] != (3, 12):
        raise WorkerError("runtime")
    import torch

    if not torch.version.hip or not str(torch.__version__).startswith("2.6.0+rocm6.4.2"):
        raise WorkerError("runtime")
    if not torch.cuda.is_available():
        raise WorkerError("device")
    inventory = devices(torch)
    versions = {"torch": str(torch.__version__), "hip": torch.version.hip, "pyannote": version("pyannote.audio"),
                "speechbrain": version("speechbrain")}
    if versions["pyannote"] != "3.3.2" or versions["speechbrain"] != "1.0.3":
        raise WorkerError("runtime")
    if request["action"] == "devices":
        return {"devices": inventory, "versions": versions}
    if request["stage"] not in ("diarization", "separation") or request["action"] not in ("probe", "scan", "separate"):
        raise WorkerError("protocol")
    chosen = [d for d in inventory if d["id"] == request["device"]]
    if len(chosen) != 1:
        raise WorkerError("device")
    torch.cuda.set_device(chosen[0]["index"])
    torch.set_num_threads(4)
    device = torch.device("cuda", torch.cuda.current_device())
    effective = devices(torch)[device.index]["id"]
    if effective != request["device"]:
        raise WorkerError("device")
    model = load_model(request["stage"], Path(request["weights"]).resolve(), device)
    result = {"device": effective, "versions": versions, "stage": request["stage"]}
    if request["action"] == "scan":
        if request["stage"] != "diarization":
            raise WorkerError("protocol")
        import soundfile as sf

        signal, rate = sf.read(request["audio"], dtype="float32")
        if signal.ndim != 1 or rate != 16000:
            raise WorkerError("audio")
        torch.cuda.reset_peak_memory_stats(device)
        started = monotonic()
        turns = model({"uri": request["uri"], "waveform": torch.from_numpy(signal[None]), "sample_rate": rate})
        torch.cuda.synchronize(device)
        result.update(rttm=turns.to_rttm(), elapsed_seconds=monotonic() - started,
                      peak_allocated_bytes=torch.cuda.max_memory_allocated(device))
    elif request["action"] == "separate":
        if request["stage"] != "separation":
            raise WorkerError("protocol")
        import numpy as np
        import soundfile as sf
        from scipy.signal import resample_poly

        signal, rate = sf.read(request["audio"], dtype="float32")
        if signal.ndim != 1 or rate != 16000 or not 0 < len(signal) <= 16 * rate:
            raise WorkerError("audio")
        if model.hparams.sample_rate != 8000 or model.hparams.num_spks != 2:
            raise WorkerError("weights")
        narrow = resample_poly(signal, 1, 2)
        torch.cuda.reset_peak_memory_stats(device)
        started = monotonic()
        with torch.inference_mode():
            est = model.separate_batch(torch.from_numpy(narrow[None]).to(device))
        torch.cuda.synchronize(device)
        if est.device != device or est.shape != (1, len(narrow), 2):
            raise WorkerError("runtime")
        result.update(frames=len(narrow), analysis_frames=len(signal), elapsed_seconds=monotonic() - started,
                      peak_allocated_bytes=torch.cuda.max_memory_allocated(device))
        for column, stem in enumerate(est[0].cpu().numpy().T, 1):
            if not np.isfinite(stem).all():
                raise WorkerError("runtime")
            root = Path(request["output"])
            sf.write(root / f"stem-{column}.wav", stem, 8000, subtype="FLOAT")
            wide = resample_poly(stem, 2, 1)[:len(signal)]
            wide /= max(1, np.max(np.abs(wide)))
            sf.write(root / f"stem-{column}-16k.wav", wide, 16000, subtype="PCM_16")
    return result


def main():
    os.environ.update(HF_HUB_OFFLINE="1", TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD="1", MIOPEN_FIND_MODE="FAST")
    try:
        request = json.load(sys.stdin)
        with contextlib.redirect_stdout(sys.stderr):
            payload = {"value": execute(request)}
    except WorkerError as error:
        payload = {"error": error.args[0]}
    except Exception:
        payload = {"error": "runtime"}
    print(json.dumps({"version": 1, **payload}))


if __name__ == "__main__":
    main()
