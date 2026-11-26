# Subtitle build progress

**Next task: P01 — Define domain values.** The [authoritative plan](plan.md) contains the architecture, acceptance cases and test gates. The planning checkpoint accounts for 1 of 119 points. All 118 implementation and acceptance points are pending.

| ID | Points | Status | Work |
| --- | ---: | --- | --- |
| P00 | 1 | Complete | Capture the plan and initialize progress |
| P01 | 5 | Pending | Domain values |
| P02 | 5 | Pending | Application, model and compute contracts with fakes |
| P03 | 5 | Pending | Provider registration and per-stage GPU placement |
| P04 | 5 | Pending | Baseline fixtures and accuracy scoring |
| P05 | 8 | Pending | Selected-track audio and recording clock |
| P06 | 5 | Pending | AMD Vulkan device binding |
| P07 | 5 | Pending | Continuous Whisper observations |
| P08 | 5 | Pending | Isolated AMD ROCm worker and setup checks |
| P09 | 5 | Pending | Required diarization and activity measurements |
| P10 | 5 | Pending | Contextual retries on the original mix |
| P11 | 5 | Pending | Optional SepFormer listening and stem ASR |
| P12 | 5 | Pending | Japanese surface alignment and grouping |
| P13 | 8 | Pending | Candidate reconciliation and attribution |
| P14 | 8 | Pending | Phrase onset, release and timed cuts |
| P15 | 5 | Pending | Active phrases and stable speaker lanes |
| P16 | 5 | Pending | SRT and ASS rendering |
| P17 | 8 | Pending | Evidence bundle and offline replay |
| P18 | 5 | Pending | Recoverable publication |
| P19 | 5 | Pending | Production generation workflow |
| P20 | 3 | Pending | GTK workflow and user documentation |
| P21 | 8 | Pending | Paired accuracy and hardware acceptance |

## Completion record

### P00 — Capture the plan and initialize progress

- Commit subject: `P00 Record the subtitle architecture and build plan`. The implementation baseline is `5bf2697`.
- Verified the task IDs and point values match in both documents, all 22 rows are sized at 8 points or below, and all relative document links resolve. The consistency check below runs from the repository root.
- `uv lock --check` passed. `uv run --locked python -m unittest discover -s tests` passed all 18 existing tests. `uv run --locked python -m compileall -q yomisub.py yomisub tests` passed.
- The first production hardware target is AMD. Separate model stages may bind to different GPUs. The first release delivers SRT, ASS and a review bundle and requires a working speaker scan.

```sh
python3 - <<'PY'
from pathlib import Path
import re

root = Path("docs/build-plan")
plan, ledger = (root / name for name in ("plan.md", "progress.md"))
pattern = r"^\| (P\d+) \| (\d+) \|"
rows = re.findall(pattern, plan.read_text(), re.MULTILINE)
assert rows and rows == re.findall(pattern, ledger.read_text(), re.MULTILINE)
assert len({task for task, _ in rows}) == len(rows)
assert all(int(points) in {1, 3, 5, 8} for _, points in rows)
for document in (plan, ledger):
    prose = re.sub(r"^`{3}.*?^`{3}", "", document.read_text(), flags=re.MULTILINE | re.DOTALL)
    for ref in re.findall(r"\[[^\]\n]+\]\(([^)]+)\)", prose):
        assert (document.parent / ref).is_file(), (document, ref)
print(f"{len(rows)} tasks, {sum(int(points) for _, points in rows)} points")
PY
```

## Updating this ledger

For each row, record the behavior delivered, tests added, exact commands and outcomes, relevant live evidence, and the unique commit subject. Update the status, point summary and next task in the same commit as the work. Record failed checks under the open task and resolve them before continuing. After a restart or autocompaction, read `docs/build-plan/plan.md`, read this ledger, and check `git log` and the working tree before resuming.
