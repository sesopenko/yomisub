import re
from pathlib import Path


def extract_show_name(file_path: str) -> str:
    path = Path(file_path).resolve()

    # Walk up each parent directory and apply regex
    for part in path.parents:
        match = re.match(r"(.*\(\d+\))", part.name)
        if match:
            return match.group(1)

    raise ValueError("Show name not found in path using the expected pattern.")