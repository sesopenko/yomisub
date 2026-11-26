# Subtitle rebuild acceptance

The final automatic medium run retained all 20 phrase IDs recovered by the legacy system across nine recordings. The frozen set has 26 IDs. On the four independently timed utterances recovered by both systems, median absolute onset error went from 1815 to 1640 ms and release error from 1305 to 320 ms. Timing on the remaining phrases has no independent paired reference. [Per-ID results and hardware measurements](../../evaluation/rebuild-scores.json) · [Frozen references and matching rules](../../evaluation/README.md)

## Automatic results

Each row scores published SRT text against the frozen recording-local IDs. Owner counts refer to recovered phrases with a reference owner. The detector columns use the constructed waveform events. A dash indicates there is no exact event reference for that recording. Each ASS event and SRT state was parsed and checked against the final evidence bundle. Legacy speaker and detector metrics are unavailable.

| Recording | Legacy / rebuilt / reference phrases | Correct / wrong / unresolved owners | Overlap hits / misses / false positives | Generation wall time |
| --- | ---: | ---: | ---: | ---: |
| S01E01 | 2 / 2 / 2 | 2 / 0 / 0 | — | 45.0 s |
| S01E03 | 3 / 3 / 3 | 0 / 0 / 3 | — | 46.7 s |
| S01E10 | 2 / 2 / 2 | 1 / 0 / 1 | — | 44.5 s |
| S01E10-multi-speakers | 0 / 0 / 0 | 0 / 0 / 0 | — | 47.1 s |
| S01E02 | 0 / 0 / 0 | 0 / 0 / 0 | — | 51.3 s |
| serial | 4 / 4 / 4 | 3 / 0 / 1 | 0 / 0 / 0 | 41.0 s |
| mix | 4 / 4 / 4 | 3 / 1 / 0 | 1 / 0 / 0 | 43.4 s |
| together | 1 / 1 / 2 | 1 / 0 / 0 | 1 / 0 / 0 | 40.1 s |
| ingcrowd01-first23 | 4 / 4 / 9 | 1 / 0 / 3 | — | 43.8 s |

### Independent phrase timing

Signed errors are displayed edge minus listener edge, in milliseconds. The four matched ELAN IDs were frozen at P04. The other five annotations stay visible as misses in the score file. [Legacy per-ID results](../../evaluation/legacy-scores.json)

| Annotation | Legacy onset / release | Rebuilt onset / release |
| --- | ---: | ---: |
| a1 | -3470 / +1560 | -3410 / -90 |
| a3 | -7980 / -3360 | -3180 / +640 |
| a41 | -160 / +1050 | -100 / +550 |
| a4 | -100 / +870 | -12 / +15 |

## Listening and correction checks

- **Ordinary dialogue.** The king/square and free-drink lines received distinct, correct recording-local owners. The 39–40 s aside retained the earlier 25–30 s voice. Its ASR spelling is flagged for review. The statue homophone remains an example of uncertain wording.
- **Fight.** The scan clustered the checked exchange together. The automatic SRT retained all three phrases and left their owners unresolved. Offline replay applied the recorded listener’s A/B/B to the same bundle and verified all three assigned lines in SRT and ASS. [Corrected replay results](../../evaluation/review-scores.json)
- **Constructed controls.** Same-onset and staggered coactivity measured 0.537–3.878 s and 14.273–16.332 s. The alternating control had no coactivity. The same-onset mix still missed the king/square phrase. The staggered mix still had one mismatched voice under the fixed recording-wide correspondence. An explicit staggered display fixture verified A alone, A+B, B alone, then clear in both exports with stable lanes. The fixture timings are excluded from speech timing metrics.
- **Natural interruption.** The detector located 26.221–26.744 s. The continuous reading kept the repeated wait and the two pressure endings. Their exact syllable edges and the disputed vowel remain open. The detected event and timed alternatives are in the bundle. A recovered word in this score can still be displayed too early.
- **Crowded dialogue.** The scan reported 19.657–19.927 s, 24.230–24.382 s. The listener reported several interruptions without exact reference edges, so a numerical miss count would be speculative. A three-voice replay fixture on the recording kept all three supplied lines, assigned distinct positions and added a crowding finding. Its injected words and edges are layout evidence only.
- **Music.** The final SRT and ASS kept the verified 19–29 s instrumental break clear. The chorus after 78 s remained without displayed lyrics and its untranscribed interval was available for listening. An unsupported foreign-language sign-off remains in the raw evidence. A separate corrected replay added the listener’s verified instrumental and unresolved chorus notes. [Research listening observations](../whisper-input-findings.md#acceptance-cases-for-the-build)

## Hardware and reproduction

The GTK run used a 14 s, language-tagged multitrack video, stream 2, Japanese audio ordinal 1, and tiny. The missing-runtime dialog identified the installation step and a retry with the installed worker generated all three sibling files. Offline replay under Python with site packages disabled reproduced both subtitle files byte-for-byte. Whisper inference took 0.43 s, and the speaker scan took 3.03 s with 0.76 GiB peak PyTorch allocation. [GTK screenshot](../subtitle-generation.png)

The actual device was the 16 GB Radeon RX 9060 XT at `pci:0000:0f:00.0`. Whisper used Vulkan and the pinned Python 3.12 pyannote worker used ROCm. The machine exposed one physical GPU and the software Vulkan renderer. Split-device placement passed through the same generation factory using controlled providers. Physical dual-GPU operation and NVIDIA inference remain unverified. No local LLM ran.

All quality runs used continuous multilingual medium, the required scan, and contextual large-v3 retries where overlap was detected. Optional stems were off for this comparison. P11 recorded the separate real SepFormer and two-stem ASR smoke. Wall times include preflight and publication. Individual scanner times cover model inference and its peak allocated bytes. Whisper times cover the subprocess, including loading, and its GPU memory was unmeasured here. [Stage-level timings, devices, hashes and settings](../../evaluation/rebuild-scores.json) · [P11 hardware evidence](progress.md#p11--keep-optional-local-stems-and-their-independent-asr-evidence)

Automatic outputs are under `gitignored-inputs/evaluation/release/`, corrected files and overlays under `gitignored-inputs/evaluation/review-release/`, and the GTK smoke under `gitignored-inputs/evaluation/gtk/`. Raw media and bundles remain local. Reproduce the comparison with the generators, scorer and replay checks in the evaluation guide. [Commands and data provenance](../../evaluation/README.md)
