"""Capability-based placement, with provider-local discovery and binding."""

from dataclasses import dataclass, field
import os
from pathlib import Path
import re
import tomllib

from .ports import ComputeProvider, ExecutionTarget, Stage, StageError


@dataclass(frozen=True)
class Preference:
    provider: str | None = None
    device: str | None = None


@dataclass
class ComputeConfig:
    default_device: str | None = None
    stages: dict[Stage, Preference] = field(default_factory=dict)


def _table(value, path: str, allowed: set[str]) -> dict:
    if not isinstance(value, dict):
        raise StageError(f"{path} must be a TOML table")
    unknown = value.keys() - allowed
    if unknown:
        raise StageError(f"Unknown {path} key: {', '.join(sorted(unknown))}")
    return value


def _name(table: dict, key: str) -> str | None:
    if key not in table:
        return None
    value = table[key]
    if not isinstance(value, str) or not value.strip():
        raise StageError(f"{key} must be a nonempty name")
    return value


def load_config(path: Path | None = None) -> ComputeConfig:
    if path is None:
        directory = os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config"
        path = Path(directory) / "yomisub" / "compute.toml"
    try:
        content = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ComputeConfig()
    try:
        data = tomllib.loads(content)
    except tomllib.TOMLDecodeError as error:
        line = re.search(r"at line (\d+)", str(error))
        number = int(line[1]) if line else len(content.rstrip().splitlines())
        lines = content.splitlines()
        key = lines[number - 1].partition("=")[0].strip() if 0 < number <= len(lines) else ""
        raise StageError(f"Invalid {path} near {key!r}: {error}") from error
    _table(data, "compute", {"default_device", "stages"})
    stages = _table(data.get("stages", {}), "stages", set(Stage))
    config = ComputeConfig(_name(data, "default_device"))
    for stage, entry in stages.items():
        _table(entry, stage, {"provider", "device"})
        config.stages[Stage(stage)] = Preference(_name(entry, "provider"), _name(entry, "device"))
    return config


class ProviderRegistry:
    def __init__(self, config: ComputeConfig):
        self.config = config
        self._providers: dict[str, tuple[ComputeProvider, frozenset[Stage]]] = {}

    def register(self, provider: ComputeProvider, stages: frozenset[Stage]) -> None:
        if provider.name in self._providers:
            raise ValueError(f"Duplicate compute provider {provider.name}")
        self._providers[provider.name] = provider, stages

    def resolve(self, stage: Stage) -> ExecutionTarget:
        preference = self.config.stages.get(stage, Preference())
        choices = []
        for provider, supported in self._providers.values():
            if stage in supported and preference.provider in (None, provider.name):
                choices.extend((provider, device) for device in provider.devices() if stage in device.stages)
        candidates = choices
        if preference.device:
            candidates = [(p, d) for p, d in choices if d.physical_id == preference.device]
        elif self.config.default_device:
            preferred = [(p, d) for p, d in choices if d.physical_id == self.config.default_device]
            candidates = preferred or choices
        if len(candidates) != 1:
            options = ", ".join(f"{p.name}/{d.physical_id}" for p, d in choices)
            raise StageError(f"Configure stages.{stage} in compute.toml for {preference!r}. "
                             f"Compatible choices: {options or 'none visible; check provider setup'}")
        provider, device = candidates[0]
        target = provider.bind(stage, device.physical_id)
        if (target.provider, target.physical_id, target.stage) != (provider.name, device.physical_id, stage):
            raise StageError(f"{stage}: provider binding changed during selection; check visible devices")
        return target
