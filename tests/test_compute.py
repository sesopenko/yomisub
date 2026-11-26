from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from yomisub.compute import ComputeConfig, Preference, ProviderRegistry, load_config
from yomisub.ports import Device, ExecutionTarget, Stage, StageError


class Provider:
    def __init__(self, name, ids, stage):
        self.name = name
        self.ids = ids
        self.stage = stage

    def devices(self):
        return tuple(Device(id_, "Identical GPU", frozenset([self.stage])) for id_ in self.ids)

    def bind(self, stage, physical_id):
        return ExecutionTarget(self.name, physical_id, self.ids.index(physical_id), stage)


class ComputeTests(unittest.TestCase):
    def test_configured_placement_follows_physical_devices_through_reordering(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "compute.toml"
            path.write_text('default_device="A"\n[stages.diarization]\nprovider="scan"\ndevice="B"\n')
            registry = ProviderRegistry(load_config(path))
        whisper = Provider("asr", ["A", "B"], Stage.BASELINE_ASR)
        scanner = Provider("scan", ["B", "A"], Stage.DIARIZATION)
        for provider in (whisper, scanner):
            registry.register(provider, frozenset([provider.stage]))
        self.assertEqual(registry.resolve(Stage.BASELINE_ASR).physical_id, "A")
        self.assertEqual(registry.resolve(Stage.DIARIZATION).physical_id, "B")
        scanner.ids.reverse()
        self.assertEqual(registry.resolve(Stage.DIARIZATION),
                         ExecutionTarget("scan", "B", 1, Stage.DIARIZATION))

    def test_provider_extension_ambiguity_and_unavailable_selections(self):
        stage = Stage.BASELINE_ASR
        config = ComputeConfig()
        registry = ProviderRegistry(config)
        for name in ("first", "second"):
            registry.register(Provider(name, ["A"], stage), frozenset([stage]))
        with self.assertRaisesRegex(StageError, "first/A, second/A"):
            registry.resolve(stage)
        config.stages[stage] = Preference("second", "A")
        self.assertEqual(registry.resolve(stage).provider, "second")
        for preference in (Preference("missing"), Preference(device="hidden")):
            config.stages[stage] = preference
            with self.assertRaisesRegex(StageError, stage.value):
                registry.resolve(stage)
        with self.assertRaisesRegex(StageError, "diarization"):
            registry.resolve(Stage.DIARIZATION)

    def test_invalid_or_duplicate_configuration_identifies_key(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "compute.toml"
            self.assertEqual(load_config(path), ComputeConfig())
            for content, key in [('bad=1', 'bad'), ('[stages.nope]', 'nope'),
                                 ('[stages.diarization]\ngpu=0', 'gpu'),
                                 ('default_device="A"\ndefault_device="B"', 'default_device')]:
                with self.subTest(content=content):
                    path.write_text(content)
                    with self.assertRaisesRegex(StageError, key):
                        load_config(path)
