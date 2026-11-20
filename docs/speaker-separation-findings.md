# Choosing a speech-separation model for Yomisub

**Use full-context Whisper on the original soundtrack for the first transcript. Run a speaker scan alongside it. Offer SepFormer on a disputed overlap when hearing each voice separately could help.** Of the methods tested, SepFormer gave the clearest improvement a listener could hear. None reliably produced two complete, correctly attributed subtitle lines. An editor needs access to the mix even after a voice sounds isolated. [How the cue planner should use this evidence](whisper-input-findings.md)

The deciding case was the short S01E10 interruption. Sean could hear one character clearly on a SepFormer track, but only the **original mix** yielded the other character’s phrase about pressure. Whisper placed those phrases one after the other. The speaker scan and listening established that they overlapped. Each input answered a different part of the subtitle question. [Guide to presenting actual overlap](japanese-subtitling-craft-for-yomisub.md#53-the-same-words-with-actual-overlap)

## Which methods belong in the workflow?

| Method | Decision for Yomisub | Decisive local result |
| --- | --- | --- |
| **pyannote speaker-diarization-3.1** detects activity and recurring voices. | Keep it as the source of anonymous voice turns and overlap flags. An ID is local to the recording and run. | In S01E10 it located 523 ms of dual activity. Copying the mix wherever either ID was active gave both tracks **8,370 identical samples** during those 523 ms. A timing mask cannot separate what the characters said. [Diarizer](https://huggingface.co/pyannote/speaker-diarization-3.1) |
| **SpeechBrain SepFormer WHAMR** estimates two voices from an 8 kHz mono mix. | First choice for *listening* to a difficult overlap. Keep both estimated tracks as optional ASR inputs. Re-establish speaker ownership for each excerpt. | It isolated audible voices in both E10 examples. It also lost a phrase the mix retained, degraded verified fight dialogue and produced spurious speech on song excerpts. [Tested checkpoint](https://huggingface.co/speechbrain/sepformer-whamr/tree/9950fd8055b38679d2af5bef2366b5dba600ec66) |
| **pyannote PixIT** combines speaker clustering with **ToTaToNet**, the local separator tested inside that pipeline. | Keep as a benchmark. Its output counts and timings are insufficient for automatic speaker tracks. | In S01E10 only one output had sound during the interruption. Sean heard both voices change level together in it. On the many-speaker clip three turn IDs had only one reconstructed waveform. Supplying a count created more files without reliably separating the speech. [PixIT](https://huggingface.co/pyannote/speech-separation-ami-1.0) · [ToTaToNet](https://huggingface.co/pyannote/separation-ami-1.0) |
| **Scicom voice-isolator** extracts a target from a 16 kHz mix using a solo reference. | Keep the enrollment approach experimental. A transcript on the target’s output is insufficient evidence for crediting that person. | Changing references in S01E10 changed the voice balance and reduced music, but the competing voice still interfered with understanding. In a control containing only B, the A-enrolled output retained B within 0.79 dB of the input. [Tested 555M GPU release](https://huggingface.co/Scicom-intl/voice-isolator/tree/20eee9195213dde59d957578b06782058a76b524) |

## S01E10 interruption at 25–28 s

**Keep both candidate phrases, their competing readings, and the fact that they overlap. Leave the exact subtitle edges open.** In the 24–29 s original-mix crop, full `large-v3` decoded `まって、まって、まって` and `あつりょくに くっしない` (“won’t give in to pressure”). The base diarizer detected both voices at 26.221–26.744 s. On a half-speed, pitch-preserved replay, Sean heard “atsryokuni kushine” from the other voice during the repeated `まって`. This supports the pressure phrase and a possible colloquial `くっしねえ` ending. It does not settle the last vowel or either speaker’s exact onset.

Sean described the 8 kHz mix as grainier, with music and both speakers still at similar levels. On SepFormer source 2 he heard one character clearly. On source 1 he heard one character but could not make out the words. The source 2 transcript kept `まって` and the later question. Source 1 produced a stock sign-off on the five-second crop. Neither source recovered the pressure phrase, even when the separator was rerun on just the final eight seconds. A clearer listening track and a more complete transcript can come from different inputs.

The preceding word provides a useful check on context. Sean heard something like `ゆうがい` on the original. Large-v3 gave `有害` on the mix and on the full isolated source, but `じゅうらい` on the isolated crop. The full isolated decode also repeated the clause. Keep the tentative listener reading separate from the proposed spelling.

## Where isolated speech helped and where it failed

| Material and reference | What the comparison established |
| --- | --- |
| **Calm dialogue, S01E01.** Sean independently heard the king, square, group and statues in the first line and “koushite tadazake” in the later line. | SepFormer source 1 with large-v3 recovered both lines, including the free-drink wording. They belong to different characters. The short aside near 39–40 s also resembled Sean’s “namaguso bosu,” but the spelling varied with context. A successful track can carry several successive speakers. |
| **Constructed simultaneous onset.** Those same two soundtrack excerpts started together at 0.500 s and their waveforms overlapped to 3.875 s. | Large-v3 recovered each line on its solo input. After separation one transcript combined A’s square with B’s drinking and lost the listener-confirmed “free.” Neither track recovered a complete separately attributable line. Against the bandwidth-matched solo references, even the better one-to-one assignment reduced SI-SDR by 1.83 dB for A and 2.78 dB for B. The references include background sound. |
| **Fight, S01E03.** Sean identified A saying `こうします`, then B saying `そう` and `たえられる`. | The original mix recovered **3/3** phrases both in full context and in the 43.4–50.3 s crop. Across both full isolated tracks only **1/3** survived. The two cropped tracks recovered **0/3**. Sean found cropped source 2 incomprehensible. Even the mixed 0–10 s effects-only crop invented a chapter announcement. Keep uncorroborated speech out of the displayed dialogue. |
| **Theme song, S01E02.** Sean distinguished the 19–29 s instrumental break from the background chorus after 78 s. The sung line after the break has a published reference. | Both separated break crops invented `はい`. Both isolated lead-vocal crops returned “thank you for watching.” On the mix, the line was intact except for one particle. Neither input supplied verified words for the closing chorus. Speech separation is a poor default for lyric transcription on this material. [Published lyric](https://www.uta-net.com/song/344130/) |
| **Crowded dialogue, separate S01E10 many-speaker excerpt.** Sean heard a single voice on each replay and the fast speaker alone on source 1. | Separation helped distinguish the voices. Large-v3 gave `たんじょう` (“birth”) on both the full isolated monologue and its crop. Medium gave “afterimage” and “heating” respectively, even with wider beam search on the crop. The normal and slowed mixes favored “birth,” but Sean still heard an ambiguous “tanju/tanzu.” On the other cropped voice, medium recovered the listener-confirmed `つかいます`. Large-v3 substituted `かいまく` and recovered the correct phrase with full context. Model agreement, context and listening answer different questions. |

## What the Python interfaces must preserve

- **Keep the mix, voice turns, source audio and text independently addressable on the media clock.** Store the model revision, source column, sample rate, source offset and any padding or delay alongside each waveform. Each ASR result belongs to its input and run. An editor can then use a word heard on the mix even when it disappears from both separated transcripts.
- **Allow a voice turn without a waveform or transcript.** PixIT’s 0.32 s context allowance widened its estimated overlap on the crowded E10 clip from 5.560 s to 14.651 s. Keep the original activity grid and padded intervals distinct. Link a waveform only to an actual output column. [PixIT source reconstruction](https://github.com/pyannote/pyannote-audio/blob/3.3.2/pyannote/audio/pipelines/speech_separation.py)
- **For an enrolled voice, retain the reference clip and its listening status.** The Scicom test selected sole-active diarizer intervals, trimmed 80 ms from each edge, enrolled 1–3 s and ran a full pass per voice. One “solo” reference contained laughter. Four enrollments in the crowded E10 passage yielded signals correlated at 0.99–1.00. Keep an uncertain owner open and allow replacing the reference for just that voice.

**What would change this recommendation?** Test a candidate on the known two-speaker mixture and on the natural S01E10 interruption. For each, show which words are recovered for each speaker, whether either transcript borrows the other’s words, and whether both phrases can enter and clear at their own times. Count a missing or unassigned line explicitly. Until a method passes those checks, its outputs belong in listening review.

## What fits on the Radeon?

All tested neural separation pipelines ran on the **16 GB RX 9060 XT** with ROCm. Whisper used Vulkan. The timings support interactive review of excerpts. Only Scicom had a continuous 24-minute duration test, on repeated audio with one enrolled voice.

| Stage | Measurement | Implication for an episode |
| --- | --- | --- |
| Original-mix Whisper large-v3 | 2.50 s for a 10 s excerpt and 5.13 s for 33 s, including loading. Sampled peak Whisper-process VRAM was **3.94 GiB** across twelve matched runs. Total board use peaked at 6.13 GiB. | Fits this GPU for the tested transcriptions. |
| SepFormer | 5.57 s for the two natural E10 excerpts totaling 63 s. A single 89 s song used **12.82 GiB** and took 21.5 s. | Use bounded excerpts. Whole-episode memory and speaker continuity across windows remain untested. |
| PixIT | 115 s of separation for 258.9 s across five natural clips, with 2.19 GiB peak PyTorch allocation. Mix and source ASR with medium added 57.6 s. | About 16 minutes per 24-minute episode or 3.2 hours for twelve **if that clip and source mix scales linearly**. |
| Scicom | A 24-minute repeated input took 141.55 s to extract one enrolled voice, with 2.41 GiB peak PyTorch allocation. The 160-sample stream delay was removed and the output preserved the input length. | Four enrolled voices across twelve episodes would take about 1 h 53 min for extraction alone at this rate. A separate short-clip extrapolation including scan, extraction and medium ASR was 3.5 hours per season. |

PyTorch allocation and driver-reported process VRAM are different measurements. The timings exclude human review. They establish hardware feasibility separately from whether a particular line was recovered.

## Reproducing the tests

The research environment used Python 3.12, ROCm 6.4.2, PyTorch 2.6.0 and pyannote.audio 3.3.2 on Debian 13. PixIT used configuration `9486b106` and ToTaToNet weights `4d38e95c`. Scicom used revision `20eee919` and SepFormer `9950fd80`. The non-turbo large-v3 checkpoint matched SHA-1 `ad82bf6a9043ceed055076d0fd39f5f186ff8062` and reported 32 text decoder layers. Use Japanese transcription with five beams and best-of five for the matched large-v3 results. [Pinned environment](../experiments/speaker-models-rocm-requirements.txt) · [Vulkan build](../README.md#build-the-vulkan-transcription-engine)

From the repository root with the weights already cached, these probes each take a fresh output path. The gated PixIT release uses the Hugging Face credential when first downloaded. [Environment template](../.env.example) · [PixIT probe](../experiments/benchmark_pixit_rocm.py) · [Scicom probe](../experiments/benchmark_scicom_rocm.py) · [SepFormer probe](../experiments/benchmark_sepformer_rocm.py)

~~~bash
d=gitignored-inputs/speaker-separation-2026-11-19
src=gitignored-inputs/whisper-feasibility-2026-11-19
export HF_HOME="$PWD/$d/cache/huggingface" PYANNOTE_CACHE="$PWD/$d/cache/pyannote"
export HF_HUB_OFFLINE=1 TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1 MIOPEN_FIND_MODE=FAST
"$d/venv-rocm/bin/python" experiments/benchmark_pixit_rocm.py "$src/together.wav" "$d/replay-pixit" --speakers 2
"$d/venv-rocm/bin/python" experiments/benchmark_scicom_rocm.py "$d/scicom-upstream" "$src/10.wav" "$d/scicom/10/ref-SPEAKER_02.wav" "$d/replay-scicom-02.wav"
"$d/venv-rocm/bin/python" experiments/benchmark_sepformer_rocm.py "$d/sepformer/model" "$d/replay-sepformer" \
    "$src/together.wav" "$src/10.wav" "$src/10-multi.wav"
~~~

The table locates the underlying results in the ignored research directory `$d`.

| Evidence | Local path |
| --- | --- |
| Activity-mask sample comparisons, PixIT turns and count-hint runs | `activity-baseline.json`, `control-scores-gpu.json`, `pixit-rocm/`, `rocm-results.json` |
| Scicom enrollments, per-voice audio, scores, streaming check and timings | `scicom/`, `scicom-scores.json`, `scicom-parity.log`, `scicom-asr-duration.log` |
| Matched SepFormer inputs, 8 kHz control, medium JSON and individual listening clips | `sepformer/run/`, `sepformer/asr/`, `sepformer/asr-windows/`, `sepformer/review/`, `sepformer/asr-half-speed/` |
| Large-v3 JSON, timing and VRAM by input | `sepformer/asr-large-v3/benchmark.json` and the adjacent CLI logs and JSON |
| S01E10 short interruption, 24–29 s after two different separation windows | `sepformer/interruption-10-local/`. The nine-second half-speed replay is `sepformer/review/S01E10-interruption-24.5-29-half-speed.mkv` |
| Other episodes and known-overlap controls | `sepformer/additional-episodes/` contains the raw estimates, 39 Whisper logs, JSON and listening windows |
