"""AMD Vulkan discovery and process-local binding for whisper.cpp."""

from collections.abc import Callable
from dataclasses import dataclass
import os
import re
import subprocess
from uuid import UUID

from .ports import Device, ExecutionTarget, Stage, StageError

ASR_STAGES = frozenset((Stage.BASELINE_ASR, Stage.RETRY_ASR, Stage.STEM_ASR))


@dataclass(frozen=True)
class VulkanDevice:
    index: int
    identity: str
    name: str
    driver: str


def enumerate_vulkan() -> str:
    try:
        return subprocess.run(["vulkaninfo"], text=True, capture_output=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError) as error:
        raise StageError("Install vulkan-tools and verify the AMD device with vulkaninfo.") from error


def visible_devices(report, mask):
    allowed = None
    if mask is not None:
        try:
            allowed = {int(item) for item in mask.replace(",", " ").split()}
        except ValueError as error:
            raise StageError("Check the indices in GGML_VK_VISIBLE_DEVICES.") from error
    devices = []
    sections = re.split(r"(?m)^GPU(\d+):\s*$", report)[1:]
    indices = set()
    for raw_index, section in zip(sections[::2], sections[1::2]):
        index = int(raw_index)
        indices.add(index)
        fields = dict(re.findall(r"(?m)^\s*(\w+)\s*=\s*([^\n]+?)\s*$", section))
        if allowed is not None and index not in allowed:
            continue
        if fields.get("vendorID") != "0x1002" or fields.get("deviceType") not in {
            "PHYSICAL_DEVICE_TYPE_DISCRETE_GPU", "PHYSICAL_DEVICE_TYPE_INTEGRATED_GPU"
        }:
            continue
        parts = ("pciDomain", "pciBus", "pciDevice", "pciFunction")
        if all(p in fields for p in parts):
            domain, bus, dev, function = (int(fields[p], 0) for p in parts)
            identity = f"pci:{domain:04x}:{bus:02x}:{dev:02x}.{function}"
        else:
            try:
                uuid = UUID(fields.get("deviceUUID", ""))
            except ValueError as error:
                raise StageError("Vulkan device lacks a stable PCI address or UUID.") from error
            if not uuid.int:
                raise StageError("Vulkan device reports an empty physical UUID.")
            identity = f"uuid:{uuid}"
        devices.append(VulkanDevice(index, identity, fields["deviceName"], fields.get("driverName", "")))
    if allowed is not None and not allowed <= indices:
        raise StageError("GGML_VK_VISIBLE_DEVICES contains an unavailable device index.")
    return devices


class AmdVulkan:
    name = "amd-vulkan"

    def __init__(self, enumerate_devices: Callable[[], str] = enumerate_vulkan, environ=None):
        self.enumerate_devices = enumerate_devices
        self.environ = os.environ if environ is None else environ

    def _visible(self):
        return visible_devices(self.enumerate_devices(), self.environ.get("GGML_VK_VISIBLE_DEVICES"))

    def devices(self):
        return tuple(Device(d.identity, d.name, ASR_STAGES) for d in self._visible())

    def _resolve(self, stage, physical_id):
        devices = self._visible()
        matches = [d for d in devices if d.identity == physical_id]
        if stage not in ASR_STAGES or len(matches) != 1:
            raise StageError(f"Check {self.name} device {physical_id} and visibility for {stage}.")
        chosen = matches[0]
        if sum((d.name, d.driver) == (chosen.name, chosen.driver) for d in devices) > 1:
            raise StageError("Ambiguous equal-name Vulkan devices. Restrict GGML_VK_VISIBLE_DEVICES.")
        return chosen

    def bind(self, stage, physical_id):
        chosen = self._resolve(stage, physical_id)
        return ExecutionTarget(self.name, physical_id, chosen.index, stage)

    def invoke(self, executable, args, target):
        if target.provider != self.name:
            raise StageError(f"{target.provider} is incompatible with the AMD Vulkan runner.")
        chosen = self._resolve(target.stage, target.physical_id)
        env = {**self.environ, "GGML_VK_VISIBLE_DEVICES": str(chosen.index), "WHISPER_ARG_DEVICE": "0"}
        try:
            run = subprocess.run([str(executable), "--device", "0", *args], env=env,
                                 text=True, capture_output=True, errors="replace")
        except OSError as error:
            raise StageError("Install the Vulkan-enabled whisper-cli from README.md.") from error
        if run.returncode:
            raise StageError(f"whisper-cli exited {run.returncode}: {run.stderr[-700:]}")
        verify_backend(run.stderr, chosen)
        return run


def verify_backend(stderr, selected):
    line = f"ggml_vulkan: 0 = {selected.name} ({selected.driver}) |"
    if (line not in stderr or "ggml_vulkan: Found 1 Vulkan devices:" not in stderr
            or not re.search(r"(?m)^whisper_backend_init_gpu: using Vulkan0 backend\s*$", stderr)):
        raise StageError(f"Cannot verify Whisper on {selected.identity}. Check the Vulkan build and visibility.")


def check_cli(executable, flags):
    try:
        result = subprocess.run([str(executable), "--help"], capture_output=True, text=True, check=True)
    except (OSError, subprocess.CalledProcessError) as error:
        raise StageError("Install a working Vulkan-enabled whisper-cli and add it to PATH.") from error
    report = result.stdout + result.stderr
    missing = [flag for flag in flags if flag not in report]
    if missing:
        raise StageError(f"Rebuild whisper-cli. Missing required options: {', '.join(missing)}.")
