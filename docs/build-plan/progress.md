# Subtitle build progress

**Next task is [P05](tasks/P05.md).** 21 of 119 points complete. [Authoritative plan](plan.md)

| ID | Points | Status | Work |
| --- | ---: | --- | --- |
| P00 | 1 | Complete | Capture the plan and initialize progress |
| P01 | 5 | Complete | Domain values |
| P02 | 5 | Complete | Application, model and compute contracts with fakes |
| P03 | 5 | Complete | Provider registration and per-stage GPU placement |
| P04 | 5 | Complete | Baseline fixtures and accuracy scoring |
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
prior_tasks = set()
for task, path, points in index:
    assert path == f"tasks/{task}.md", (task, path)
    brief = root / path
    content = brief.read_text()
    assert content.startswith(f"# {task} — "), brief
    assert f"**Size:** {points}." in content, brief
    prerequisite = re.search(r"\*\*Prerequisites?:\*\* (.+)", content)
    assert prerequisite, brief
    dependencies = set(re.findall(r"\bP\d+\b", prerequisite.group(1)))
    assert dependencies <= prior_tasks and (task == "P00" or dependencies), brief
    prior_tasks.add(task)
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

### P00 update — Two adversarial reviews

| Review | Scope | Findings applied |
| --- | --- | --- |
| Architect | Reviewed P00–P21, the plan, ledger and research. | Defined the handoff from provisional speaker attribution to final spotting, recording-clock conversions, optional versus required model binding, GTK cutover, and recovery of an SRT-only installation. Froze the phrase IDs and independent timing references used to judge accuracy. |
| Implementer | Reviewed all 22 revised briefs in execution order against the checkout and research artifacts. | Moved acceptance checks to the task that can perform them. Specified clean-checkout inputs, model acquisition, the delayed-audio numeric example, offline corrections with changed text, publication retry order and named automatic release gates. |

Both rounds were planning reviews. P01 is the next implementation task. The live accuracy gate requires independently verified speech-edge annotations. The research control placement data measures waveform overlap.

Verification passed for all 22 task files, prerequisite order, point totals and source links. The TOML example parsed, the rational sample-clock example checked out, and the S01E10 coactivity interval matched the tracked RTTM. The lockfile check, all 18 unit tests and compilation passed. Commit subject is `P00 Resolve architect and implementer review findings`.

### P01 — Model recording clocks and subtitle evidence

Added immutable recording and source clocks, raw observations, bounded intervals, editorial overlays and layout values. `uv run --locked python -m unittest discover -s tests -p test_domain.py` passed four tests including fractional resampling and invalid observation retention. `uv lock --check`, `uv run --locked python -m unittest discover -s tests` (22 tests), and `uv run --locked python -m compileall -q yomisub.py yomisub tests` passed.

Commit subject is `P01 Model recording clocks and subtitle evidence`.

### P02 — Define generation and replay contracts

Application-owned ports and fake-driven generation/replay now share one planner and renderer. The shared binding, ASR and scanner assertions in `tests/adapter_contracts.py` also apply to P06, P07 and P09. A required scan failure stops publication and an optional failure preserves the baseline and distinct findings. `uv run --locked python -m unittest discover -s tests -p test_application.py` passed 5 tests. `uv lock --check`, `uv run --locked python -m unittest discover -s tests` (27 tests), and `uv run --locked python -m compileall -q yomisub.py yomisub tests` passed.

Commit subject is `P02 Define generation and replay contracts`.

### P03 — Resolve model stages to physical compute devices

A registered provider resolves physical IDs on each bind. A TOML override selects a provider and device by stage and ambiguous choices identify the available bindings. `uv run --locked python -m unittest discover -s tests -p test_compute.py` passed 3 tests covering reordering, extension and invalid configuration. `uv lock --check`, `uv run --locked python -m unittest discover -s tests` (30 tests), and `uv run --locked python -m compileall -q yomisub.py yomisub tests` passed. Hardware verification is scheduled in P06 and P08.

Commit subject is `P03 Resolve model stages to physical compute devices`.

### P04 — Freeze legacy subtitle recovery and independent timing scores

Ran the original 5bf2697 generator with the verified medium checkpoint on all five research scenes, three controls and a 23-second evaluation-only IngCrowd conversation excerpt. Local final SRTs and device logs are under `gitignored-inputs/evaluation/legacy/`. The 20 of 26 recovered reference IDs include four of nine manually timed utterances. Their median absolute onset and release errors were 1815 ms and 1305 ms. Legacy speaker and detector metrics are unavailable. [Frozen scores and reproduction](../../evaluation/README.md)

`uv run --locked python -m unittest discover -s tests -p test_evaluation.py` passed seven scorer tests. `uv lock --check`, `uv run --locked python -m unittest discover -s tests` (37 tests), and `uv run --locked python -m compileall -q yomisub.py yomisub tests` passed. Re-scoring the ignored final SRTs matched the committed JSON exactly.

Commit subject is `P04 Freeze legacy subtitle recovery and independent timing scores`.

## Updating this ledger

At task start, mark the row `In progress` and replace the next-task pointer at the top with a link to the active brief. After every context compression or restart, use that pointer to reread the full plan and active brief before continuing. [Starting and resuming a task](plan.md#starting-and-resuming-a-task)

For each row, record the behavior delivered, tests added, exact commands and outcomes, relevant live evidence, and the unique commit subject. Record failed checks under the open task and resolve them before continuing. On completion, mark the row complete, update the point summary and identify the next pending task in the same commit as the work.
