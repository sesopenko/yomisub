import unittest
from unittest.mock import patch
from subprocess import CompletedProcess

from adapter_contracts import check_binding
from yomisub.ports import Stage, StageError
from yomisub.vulkan import AmdVulkan


def gpu(index, bus, name="Radeon"):
    return f"""GPU{index}:
 vendorID = 0x1002
 deviceName = {name}
 deviceType = PHYSICAL_DEVICE_TYPE_DISCRETE_GPU
 driverName = radv
 pciDomain = 0
 pciBus = {bus}
 pciDevice = 0
 pciFunction = 0
"""


class VulkanTests(unittest.TestCase):
    def test_contract_and_reenumeration_at_launch_with_child_only_selection(self):
        listing = [gpu(0, 3) + gpu(1, 4, "Other")]
        env = {"GGML_VK_VISIBLE_DEVICES": "0,1"}
        provider = AmdVulkan(lambda: listing[0], env)
        check_binding(self, provider, Stage.BASELINE_ASR, "pci:0000:03:00.0")
        target = provider.bind(Stage.RETRY_ASR, "pci:0000:03:00.0")
        listing[0] = gpu(1, 3) + gpu(0, 4, "Other")
        log = ("ggml_vulkan: Found 1 Vulkan devices:\nggml_vulkan: 0 = Radeon (radv) | fp16: 1\n"
               "whisper_backend_init_gpu: using Vulkan0 backend\n")
        with patch("yomisub.vulkan.subprocess.run", return_value=CompletedProcess([],0,"",log)) as call:
            provider.invoke("whisper-cli", [], target)
            self.assertEqual(call.call_args.kwargs["env"]["GGML_VK_VISIBLE_DEVICES"], "1")
        self.assertEqual(env, {"GGML_VK_VISIBLE_DEVICES": "0,1"})

    def test_hidden_and_ambiguous_and_wrong_backend(self):
        listing = gpu(1, 3) + gpu(0, 4)
        env = {}
        provider = AmdVulkan(lambda: listing, env)
        with self.assertRaisesRegex(StageError, "Ambiguous"):
            provider.bind(Stage.BASELINE_ASR, "pci:0000:03:00.0")
        env["GGML_VK_VISIBLE_DEVICES"] = "1"
        with self.assertRaises(StageError):
            provider.bind(Stage.BASELINE_ASR, "pci:0000:04:00.0")
        target = provider.bind(Stage.BASELINE_ASR, "pci:0000:03:00.0")
        with patch("yomisub.vulkan.subprocess.run", return_value=CompletedProcess([],0,"","using CPU backend")):
            with self.assertRaisesRegex(StageError, "Cannot verify"):
                provider.invoke("whisper-cli", [], target)
