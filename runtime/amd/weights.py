"""Acquire and verify the exact files used by the isolated ROCm worker."""

import argparse
import hashlib
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory

SCAN = {
    "config.yaml": ("pyannote/speaker-diarization-3.1", "84fd25912480287da0247647c3d2b4853cb3ee5d",
                    "config.yaml", "04ad9cd59a93c3a7c754200ecc9e1c4ba87bf1657ef8a4debf7555e711daeeda"),
    "segmentation.bin": ("pyannote/segmentation-3.0", "e66f3d3b9eb0873085418a7b813d3b369bf160bb",
                         "pytorch_model.bin", "da85c29829d4002daedd676e012936488234d9255e65e86dfab9bec6b1729298"),
    "embedding.bin": ("pyannote/wespeaker-voxceleb-resnet34-LM", "837717ddb9ff5507820346191109dc79c958d614",
                      "pytorch_model.bin", "366edf44f4c80889a3eb7a9d7bdf02c4aede3127f7dd15e274dcdb826b143c56"),
}
SEPARATOR = {
    "separator/" + name: ("speechbrain/sepformer-whamr", "9950fd8055b38679d2af5bef2366b5dba600ec66", name, sha)
    for name, sha in {
        "decoder.ckpt": "059532c89f67474e98c737e3790d607b60dcdd420767e9259165a2e7370bdd97",
        "encoder.ckpt": "68e6706cd485dd62a7f29ce596e79fb604dfdd352849a546650baa41fe8c34b7",
        "hyperparams.yaml": "ff040161fc168d07e6a13a7a98592b90d39eab311bf55ace91372d9e2575b400",
        "masknet.ckpt": "897fc2de3cde8992891a2ee7164cd49877459e65d4867327c3c6b80da94aad01",
    }.items()
}


def verified(path, expected):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest() == expected


if __name__ == "__main__":
    from huggingface_hub import hf_hub_download

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--cache-dir", type=Path)
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--separator", action="store_true")
    args = parser.parse_args()
    for name, (repo, revision, filename, sha) in (SEPARATOR if args.separator else SCAN).items():
        path = Path(hf_hub_download(repo, filename, revision=revision, cache_dir=args.cache_dir,
                                    local_files_only=args.offline))
        if not verified(path, sha):
            raise SystemExit(f"Checkpoint mismatch for {repo} at {revision}.")
        output = args.directory / name
        output.parent.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(dir=output.parent) as directory:
            staged = Path(directory) / output.name
            shutil.copyfile(path, staged)
            staged.replace(output)
