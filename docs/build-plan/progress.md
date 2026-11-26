# Subtitle build progress

**Next task is [P18](tasks/P18.md).** 98 of 119 points complete. [Authoritative plan](plan.md)

| ID | Points | Status | Work |
| --- | ---: | --- | --- |
| P00 | 1 | Complete | Capture the plan and initialize progress |
| P01 | 5 | Complete | Domain values |
| P02 | 5 | Complete | Application, model and compute contracts with fakes |
| P03 | 5 | Complete | Provider registration and per-stage GPU placement |
| P04 | 5 | Complete | Baseline fixtures and accuracy scoring |
| P05 | 8 | Complete | Selected-track audio and recording clock |
| P06 | 5 | Complete | AMD Vulkan device binding |
| P07 | 5 | Complete | Continuous Whisper observations |
| P08 | 5 | Complete | Isolated AMD ROCm worker and setup checks |
| P09 | 5 | Complete | Required diarization and activity measurements |
| P10 | 5 | Complete | Contextual retries on the original mix |
| P11 | 5 | Complete | Optional SepFormer listening and stem ASR |
| P12 | 5 | Complete | Japanese surface alignment and grouping |
| P13 | 8 | Complete | Candidate reconciliation and attribution |
| P14 | 8 | Complete | Phrase onset, release and timed cuts |
| P15 | 5 | Complete | Active phrases and stable speaker lanes |
| P16 | 5 | Complete | SRT and ASS rendering |
| P17 | 8 | Complete | Evidence bundle and offline replay |
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

### P05 — Prepare selected audio on the recording clock

FFmpeg decoded all five research tracks with validated frame counts. The generated `gitignored-inputs/evaluation/track-clock.mkv` has a video origin of 10 s and two tagged tones. Selecting Japanese (global index 2, ordinal 1) returned 44100 frames at 44.1 kHz with 700 positive crossings and an exact 1/4 s playback delay. The 220 Hz English track remained distinguishable. The focused `test_audio.py` suite passed 4 tests, including outward-rounded crops and early audio. `uv lock --check`, `uv run --locked python -m unittest discover -s tests` (41 tests), and `uv run --locked python -m compileall -q yomisub.py yomisub tests` passed.

Commit subject is `P05 Prepare selected audio on the recording clock`.

### P06 — Bind and verify the physical AMD Vulkan device

The shared provider contract, reordered indices, restricted visibility, ambiguous equal names, child isolation and CPU fallback tests passed in `test_vulkan.py`. Live `whisper-cli --device 0 -m <cached ggml-tiny.bin> -f <serial.wav> -l ja -osrt -of <tiny-smoke>` completed with the child restricted to physical Vulkan index 0, PCI `0000:0f:00.0`, AMD Radeon Graphics (RADV GFX1200), and `using Vulkan0 backend`. The first-use tiny download has SHA-256 `be07e048e1e599ad46341c8d2a135645097a538221678b7acdd1b1919c6e1b21`. Output and stderr are in `gitignored-inputs/evaluation/tiny-smoke.*`. `uv lock --check`, `uv run --locked python -m unittest discover -s tests` (43 tests), and `uv run --locked python -m compileall -q yomisub.py yomisub tests` passed.

Commit subject is `P06 Bind and verify the physical AMD Vulkan device`.

### P07 — Capture continuous Whisper JSON with verified checkpoints

`test_asr.py` passed 3 tests for signed and missing piece times, exact or degraded text joins, decode-local points, one continuous input, and verified cache publication. Live full JSON on the complete 24-second serial control returned four segments on AMD Vulkan at `0000:0f:00.0`, medium SHA-1 `fd9727b6e1217c2f614f9b698455c4ffd82463b4`. The installed CLI reported 1.9.5-dev. `sha1sum gitignored-inputs/models/ggml-large-v3.bin` matched the research digest `ad82bf6a9043ceed055076d0fd39f5f186ff8062`. `uv lock --check`, `uv run --locked python -m unittest discover -s tests` (46 tests), and `uv run --locked python -m compileall -q yomisub.py yomisub tests` passed.

Commit subject is `P07 Capture continuous Whisper JSON with verified checkpoints`.

### P08 — Provision and probe an isolated ROCm worker

Provisioned a fresh Python 3.12.12 environment under `gitignored-inputs/evaluation/amd/venv` with the documented `uv pip install --no-deps ... -r runtime/amd/requirements.txt`. The local cache lacked the AMD Torch wheel, so the installation fetched the pinned build. The directory contained only the three verified diarization files. The JSON probe loaded both required models on PCI `0000:0f:00.0` using Torch 2.6.0+rocm6.4.2.git76481f7c, HIP 6.4.43484-123eb5128, and pyannote.audio 3.3.2. A separate optional probe identified the missing separator. The log is `gitignored-inputs/evaluation/amd/probe.log`. Two focused worker tests, Python 3.12 worker compilation, `uv lock --check`, `uv run --locked python -m unittest discover -s tests` (48 tests), and `uv run --locked python -m compileall -q yomisub.py yomisub tests` passed.

Commit subject is `P08 Provision and probe an isolated ROCm worker`.

### P09 — Scan full recordings and measure simultaneous voice activity

Live analysis on the fresh ROCm worker yielded 15 S01E10 turns and reproduced the 26.221–26.744 s coactivity region, with three anonymous voices over the recording. Device, RTTM, elapsed inference time and peak allocation are in `gitignored-inputs/evaluation/amd/S01E10-scan.json`. The shared scanner contract and `test_activity.py` passed, including the mixed-URI research RTTM, duplicate and nested turns, changing coactivity, silence, crash and negative duration. `uv lock --check`, `uv run --locked python -m unittest discover -s tests` (51 tests), and `uv run --locked python -m compileall -q yomisub.py yomisub tests` passed.

Commit subject is `P09 Scan full recordings and measure simultaneous voice activity`.

### P10 — Retain an original-mix retry for every overlap core

Added one contextual large-v3 retry per exact active-ID core and retained its own source, core link, padding-only segment IDs and any failure finding. The continuous transcript remains a separate application input. `test_refinement.py` passed three tests covering both edges, intersecting contexts, crowded cores, no overlap, failed retries and the two documented S01E10 window readings. `uv lock --check`, `uv run --locked python -m unittest discover -s tests` (54 tests), and `uv run --locked python -m compileall -q yomisub.py yomisub tests` passed.

Commit subject is `P10 Retain an original-mix retry for every overlap core`.

### P11 — Keep optional local stems and their independent ASR evidence

The opt-in S01E10 run used full large-v3 `ad82bf6a` for the contextual mix and both stem decodes. SepFormer WHAMR `9950fd80` ran on ROCm, with Whisper on Vulkan, both PCI `0000:0f:00.0`. Both native stems held 36184 frames at 8 kHz and both analysis copies held 72368 frames at 16 kHz. All four mapped to recording sample 387536 at 16 kHz (24.221 s). Output, three run IDs and audio are in `gitignored-inputs/evaluation/stem-smoke/`. Source columns carry no speaker assignment. Three focused `test_stems.py` tests, `uv lock --check`, `uv run --locked python -m unittest discover -s tests` (57 tests), and `uv run --locked python -m compileall -q yomisub.py yomisub tests` passed.

Commit subject is `P11 Keep optional local stems and their independent ASR evidence`.

### P12 — Join Japanese morphology to exact Whisper surfaces

Pinned SudachiPy 0.7.0 and the 20261015 Core dictionary. Grouping records split mode C, versions, exact surface spans and lexical piece links. Wrap suggestions may fall inside a piece, while timed candidates require usable adjacent pieces. Whole-segment fallback keeps mismatched or non-Japanese input intact. The three focused `test_grouping.py` tests, `uv lock --check`, `uv run --locked python -m unittest discover -s tests` (60 tests), and `uv run --locked python -m compileall -q yomisub.py yomisub tests` passed.

Commit subject is `P12 Join Japanese morphology to exact Whisper surfaces`.

### P13 — Reconcile overlap readings and provisional speaker ownership

Reconciliation keeps each candidate tied to its source segment, recording occurrence, core, alternatives and supporting evidence IDs. Four focused `test_reconcile.py` tests cover merged-cluster A/B/B corrections, solo continuation into overlap, supported wording with disputed ownership, and repeated versus padding-only readings. `uv lock --check`, `uv run --locked python -m unittest discover -s tests` (64 tests), and `uv run --locked python -m compileall -q yomisub.py yomisub tests` passed.

Commit subject is `P13 Reconcile overlap readings and provisional speaker ownership`.

### P14 — Spot independent phrase edges and recheck final owners

Phrase spotting chooses each outer edge from a listener decision, a validated lexical edge, or the enclosing segment. It retains invalid raw evidence, preserves unsupported or disputed intervals for review, and checks ownership after changing boundaries. Five `test_spotting.py` tests cover cuts, phrase corrections, expansion and contraction, silence, short and long phrases, and end overrun. `uv lock --check`, `uv run --locked python -m unittest discover -s tests` (69 tests), and `uv run --locked python -m compileall -q yomisub.py yomisub tests` passed.

Commit subject is `P14 Spot independent phrase edges and recheck final owners`.

### P15 — Lay out active phrases in stable speaker lanes

The shared planner sweeps coincident events once, preserves continuing lanes, uses neutral labels for supported recording-local voices, and keeps a third phrase with a crowding finding. Two focused `test_layout.py` tests cover stable A/B entry and release, same-onset order, coincident changes, repeatability and exact combined reading demand (4 + 3 = 7 characters/s). `uv lock --check`, `uv run --locked python -m unittest discover -s tests` (71 tests), and `uv run --locked python -m compileall -q yomisub.py yomisub tests` passed.

Commit subject is `P15 Lay out active phrases in stable speaker lanes`.

### P16 — Render SRT screen states and independent ASS lanes

Two focused `test_writers.py` tests parsed UTF-8 SRT and ASS, checked literal markup, shared boundaries, half-up rounding, duration clamps and unique collapse diagnostics. FFmpeg/libass rendered a 1280×720 three-voice example: all three Japanese phrases were readable and the continuing lane was pixel-identical before and after the other voice cleared (1248 bright pixels). The reviewed frame and ASS are at `gitignored-inputs/evaluation/layout/`. `uv lock --check`, `uv run --locked python -m unittest discover -s tests` (73 tests), and `uv run --locked python -m compileall -q yomisub.py yomisub tests` passed.

Commit subject is `P16 Render SRT screen states and independent ASS lanes`.

### P17 — Save relocatable evidence and replay listener corrections

Four focused `test_bundle.py` tests passed, including byte-identical SRT and ASS from a moved ZIP in a `python -S` subprocess, a length-changing correction, corrected edge, added second voice, interval note and explicit timed subdivision. Invalid edits and damaged evidence preserve existing files. `uv lock --check`, `uv run --locked python -m unittest discover -s tests` (77 tests), and `uv run --locked python -m compileall -q yomisub.py yomisub tests` passed.

Commit subject is `P17 Save relocatable evidence and replay listener corrections`.

## Updating this ledger

At task start, mark the row `In progress` and replace the next-task pointer at the top with a link to the active brief. After every context compression or restart, use that pointer to reread the full plan and active brief before continuing. [Starting and resuming a task](plan.md#starting-and-resuming-a-task)

For each row, record the behavior delivered, tests added, exact commands and outcomes, relevant live evidence, and the unique commit subject. Record failed checks under the open task and resolve them before continuing. On completion, mark the row complete, update the point summary and identify the next pending task in the same commit as the work.
