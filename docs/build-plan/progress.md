# Subtitle build progress

**Next task is P01 — Define domain values.** The planning checkpoint accounts for 1 of 119 points. All 118 implementation and acceptance points are pending. [Authoritative plan](plan.md) · [P01 task brief](tasks/P01.md)

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
- Verified that the task IDs and point values match in both documents, all 22 rows are sized at 8 points or below, and the original relative document links resolve.
- `uv lock --check` passed. `uv run --locked python -m unittest discover -s tests` passed all 18 existing tests. `uv run --locked python -m compileall -q yomisub.py yomisub tests` passed.
- The first production hardware target is AMD. Separate model stages may bind to different GPUs. The first release delivers SRT, ASS and a review bundle and requires a working speaker scan.

### P00 update — Detail each task and cite its sources

- Added and indexed 22 briefs under `docs/build-plan/tasks/`. Each records its prerequisite, work, acceptance checks and source links. The briefs distinguish research results from proposed behavior and mark the tests that still need to establish accuracy.
- The consistency check below passed for all 22 tasks and 119 points, including local research links and section anchors. Run it from the repository root.
- `uv lock --check` passed. `uv run --locked python -m unittest discover -s tests` passed all 18 tests. `uv run --locked python -m compileall -q yomisub.py yomisub tests` passed.
- Commit subject is `P00 Detail subtitle rebuild tasks and research references`.

```sh
python3 - <<'PY'
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

root = Path("docs/build-plan")
plan, ledger = (root / name for name in ("plan.md", "progress.md"))
index = re.findall(
    r"^\| \[(P\d+)\]\((tasks/[^)]+)\) \| (\d+) \|",
    plan.read_text(), re.MULTILINE,
)
rows = [(task, points) for task, _, points in index]
assert rows and rows == re.findall(r"^\| (P\d+) \| (\d+) \|", ledger.read_text(), re.MULTILINE)
assert len({task for task, _ in rows}) == len(rows)
assert all(int(points) in {1, 3, 5, 8} for _, points in rows)
briefs = []
for task, path, points in index:
    assert path == f"tasks/{task}.md", (task, path)
    brief = root / path
    content = brief.read_text()
    assert content.startswith(f"# {task} — "), brief
    assert f"**Size:** {points}." in content, brief
    assert all(f"\n## {section}\n" in content for section in ("Work", "Acceptance", "Sources")), brief
    briefs.append(brief)
assert set(briefs) == set((root / "tasks").glob("*.md"))

def markdown_prose(path):
    return re.sub(r"^(`{3}|~{3}).*?^\1[^\n]*", "", path.read_text(), flags=re.MULTILINE | re.DOTALL)

for document in (plan, ledger, *briefs):
    prose = markdown_prose(document)
    for ref in re.findall(r"\[[^\]\n]+\]\(([^)]+)\)", prose):
        link = urlsplit(ref)
        if link.scheme or link.netloc:
            continue
        target = document.parent / unquote(link.path) if link.path else document
        assert target.is_file(), (document, ref)
        if link.fragment:
            headings = re.findall(r"^#{1,6} (.+)$", markdown_prose(target), re.MULTILINE)
            anchors = {re.sub(r"[^\w -]", "", title.lower()).replace(" ", "-") for title in headings}
            assert unquote(link.fragment) in anchors, (document, ref)
print(f"{len(rows)} tasks, {sum(int(points) for _, points in rows)} points")
PY
```

## Updating this ledger

At task start, mark the row `In progress` and replace the next-task pointer at the top with a link to the active brief. After every context compression or restart, use that pointer to reread the full plan and active brief before continuing. [Starting and resuming a task](plan.md#starting-and-resuming-a-task)

For each row, record the behavior delivered, tests added, exact commands and outcomes, relevant live evidence, and the unique commit subject. Record failed checks under the open task and resolve them before continuing. On completion, mark the row complete, update the point summary and identify the next pending task in the same commit as the work.
