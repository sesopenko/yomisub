# AMD speaker analysis on Debian 13

The desktop process runs Python 3.13. The speaker-analysis worker runs a separate Python 3.12 with the research ROCm 6.4.2 wheels. The Radeon must be accessible through /dev/kfd and its render node. From the project root, install the worker in its default data directory.

```sh
amd_dir="${XDG_DATA_HOME:-$HOME/.local/share}/yomisub/amd"
uv venv --python 3.12 "$amd_dir/venv"
uv pip install --no-deps --python "$amd_dir/venv/bin/python" -r runtime/amd/requirements.txt
```

The requirements pin the worker dependency closure, including the ROCm wheel URLs. This also keeps uv from substituting CUDA wheels. For a custom worker installation, set `YOMISUB_ROCM_PYTHON` to the interpreter and `YOMISUB_ROCM_WEIGHTS` to the model directory.

Accept the model conditions using your Hugging Face account, then log in with the worker environment's `huggingface-cli login`. Download the three pinned diarization files once. Model acquisition uses the credentials locally. Inference loads the files offline. [Diarization model](https://huggingface.co/pyannote/speaker-diarization-3.1) · [Segmentation model](https://huggingface.co/pyannote/segmentation-3.0)

```sh
"$amd_dir/venv/bin/python" runtime/amd/weights.py "$amd_dir/weights"
```

For an existing authorized Hugging Face cache, add `--offline --cache-dir /path/to/cache`. SepFormer is optional. Install its four pinned files by running the same acquisition command with `--separator`. [SepFormer WHAMR](https://huggingface.co/speechbrain/sepformer-whamr)

Inspect the device list. Replace the example PCI address with a returned ID to verify loading the required scanner on that physical GPU.

```sh
echo '{"version":1,"action":"devices"}' | "$amd_dir/venv/bin/python" runtime/amd/worker.py
python3 - "$amd_dir/weights" <<'PY' | "$amd_dir/venv/bin/python" runtime/amd/worker.py
import json, sys
print(json.dumps(dict(version=1, action="probe", stage="diarization", device="pci:0000:0f:00.0", weights=sys.argv[1])))
PY
```

Each request uses one JSON object on stdin and returns `version` with either `value` or a recovery code on stdout. The app shows setup instructions for a missing interpreter, unsupported protocol, unavailable weights or device mismatch. A missing required scanner stops generation. Optional separation has its own probe. Device enumeration honors inherited HIP/ROCR visibility. Each operation resolves the selected PCI identity in the worker and verifies the loaded parameters on the effective device.
