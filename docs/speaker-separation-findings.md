# Can Yomisub recover both voices in an interruption?

**GPU processing works. Automatic ownership of overlapping words remains unresolved.** Both pyannote PixIT and Scicom's enrolled GPU model ran on this workstation's 16 GB Radeon RX 9060 XT. Whisper medium decoded their outputs through Vulkan. In the natural S01E10 interruption, the listener heard both characters in the one active PixIT waveform. In a controlled mixture, Scicom tended to retain words from the same voice under two different enrollments. Yomisub can offer these waveforms for audition and competing transcripts. The tests give insufficient evidence to publish overlapping subtitles from source IDs alone. [Subtitling guide, §5](japanese-subtitling-craft-for-yomisub.md#5-multiple-speakers-and-their-visual-presentation) · [Whisper and diarization findings](whisper-input-findings.md)

The project owner deliberately chose S01E10 because this show frequently combines simultaneous voices, busy music and fast action. Treat its 25–28 s exchange and the many-speaker clip as acceptance cases for the intended material. The measurements describe these excerpts and do not estimate the prevalence of separation failures across Japanese television.

## PixIT on the Radeon

The GPU benchmark used the release settings and automatic speaker count. Each clip had a zero media start. We preserved the native output, exported one 16 kHz WAV per actual source column at the input length, then ran whisper.cpp medium on each exported WAV. The table reports the number of IDs in the returned turns separately from the number of available waveforms.

| Input | Audio | PixIT time | IDs / WAVs | Result that matters for subtitles |
| --- | ---: | ---: | ---: | --- |
| Known same-onset mixture | 9.0 s | 5.5 s | 2 / 1 | The only WAV mixed fragments from both voices in its transcript. Its zero-lag SI-SDR against reference B fell 5.06 dB relative to the mix. |
| S01E10 interruption | 30.0 s | 12.5 s | 2 / 2 | Only source 01 contained audio at 24–29 s. In a matched five-second replay the listener heard both characters increase in loudness, then both become quieter. Source 00 was digitally silent throughout. |
| S01E10-multi-speakers | 33.0 s | 14.9 s | 3 / 1 | Two extra turn IDs had no corresponding waveform. The original activity grid marked 5.560 s of simultaneous activity. Adding context widened the returned overlap to 14.651 s. |
| S01E01 dialogue and laughter | 44.0 s | 19.9 s | 4 / 4 | Returned ID 03 recurred at 25–30 and around 40 s, consistent with the listener's same-character judgment. Only the last 0.240 s of 39–40 s was in its returned interval, entirely from added context. |
| S01E03 fight | 63.0 s | 26.8 s | 1 / 1 | The single source could not distinguish the confirmed A/B/B exchange at 44–49 s. Whisper also emitted dialogue at 0–9 s on a digitally silent part of the stem. The listener placed the first spoken line near 15 s. |
| S01E02 theme song | 89.0 s | 41.0 s | 2 / 2 | In the listener-confirmed instrumental window at 19–29 s, PixIT reported 2.312 s of activity before adding context. In the closing chorus from 78 s it reported only 0.040 s before context. |

**What a count hint changed.** Giving PixIT the known count of two on the control produced two WAVs. Over the true overlap, the best one-to-one waveform assignment had SI-SDR changes of −5.70 dB for A and −2.47 dB for B. Whisper recovered B's `ただ酒` on track 00. A's matching track 01 produced `(お前はフリーク)`, missing `王様` and `広場`. On S01E10 the older diarizer's count of three produced three WAVs, but two were silent at 24–29 s. On the crowded clip, supplying four produced four WAVs and one transcript with words about the probability calculation. Other outputs included generic farewells. Four physical files alone cannot establish the ownership or completeness of the babbled line.

**Why label counts and timing can mislead.** In pyannote.audio 3.3.2, the diarization grid can acquire additional columns when the predicted number of active speakers exceeds the number of clustered sources. Source reconstruction uses the actual clusters. Preserve turn-only IDs explicitly, and index audio by validated source columns. With leakage removal enabled, the pipeline modifies its activity grid before exporting RTTM. We captured the original grid at the `discrete_diarization` hook. The configured 0.32 s ASR collar can bridge short gaps and create display overlap. Retain the two kinds of timing separately. [Source reconstruction](https://github.com/pyannote/pyannote-audio/blob/3.3.2/pyannote/audio/pipelines/speech_separation.py) · [Activity-grid padding](https://github.com/pyannote/pyannote-audio/blob/3.3.2/pyannote/audio/pipelines/utils/diarization.py)

**Turnaround.** Across the five natural excerpts, PixIT took 115.0 s for 258.9 s of audio. The corresponding CPU runs on S01E10 and S01E10-multi took 66.9 and 81.7 s, respectively, versus 12.5 and 14.9 s on GPU. Peak PyTorch allocation was 2.19 GiB on these clips. Vulkan Whisper took another 16.9 s for the five mixtures and 40.7 s for their ten WAVs, including CLI startup per file. At this clip mix and source count, that is about **16 minutes per 24-minute episode or 3.2 hours per twelve episodes** for separation plus mix and source ASR. This extrapolates short clips. Full-episode cast size, host RAM during whole-file reconstruction, model loading and export I/O can change the season result.

Both PixIT neural modules were checked on the HIP device before inference. Python used AMD's PyTorch and torchaudio 2.6.0 wheels for ROCm 6.4.2 on Debian 13. The physical card reported `gfx1200`. A first nine-second GPU trial with default kernel lookup took 59.2 s. The reported timings use a loaded pipeline and `MIOPEN_FIND_MODE=FAST` after that initial trial. Its model load and transfer took a further 4.16 s. The fastest setting on a new machine would need measurement. Each Whisper benchmark log confirmed `using Vulkan0 backend`. [AMD wheels](https://rocm.docs.amd.com/projects/radeon-ryzen/en/docs-6.4.2/docs/install/native_linux/install-pytorch.html) · [AMD MIOpen lookup modes](https://rocm.docs.amd.com/projects/MIOpen/en/docs-6.4.2/how-to/find-and-immediate.html) · [PyTorch HIP device semantics](https://docs.pytorch.org/docs/main/notes/hip.html)

## Timestamp masks as a CPU baseline

On 19 November 2026, an offline run of the cached `pyannote/speaker-diarization-3.1` processed the Japanese 16 kHz mono soundtracks. For the two S01E10 examples and the control below, we also made one full-length WAV per detected voice by copying the original PCM samples while its label was active and writing zeros elsewhere. These activity masks measure what can be recovered from timestamps alone. [Diarization model card](https://huggingface.co/pyannote/speaker-diarization-3.1)

| Recording | What establishes overlap | What the activity-mask WAVs contain |
| --- | --- | --- |
| Two S01E01 excerpts mixed at the same onset | A and B start at 0.500 s. A ends at 3.875 s and B at 6.828 s. Reconstructing the mixture from the solo excerpts agreed within one PCM16 quantization unit. Both excerpts include their soundtrack backgrounds. | Two IDs. Their WAVs share 53,460 identical samples (3.341 s) while both are active. |
| S01E10 | The listener identified dual speech around 25–28 s. | IDs 00 and 02 share 8,370 identical samples (0.523 s), at approximately 26.221–26.744 s. There is no source-specific acoustic information in those copied samples. |
| S01E10-multi-speakers | The listener heard several interruptions and a voice babbling for roughly ten seconds. The exact words and the times of each interruption remain open. | Four IDs. Only 2,160 samples (0.135 s) are assigned to two voices across the entire clip. The 9.059–18.863 s run under one ID is a candidate listening window. Its duration alone cannot identify the babbler. |

The sample counts use turn boundaries rounded directly to the nearest sample. The earlier report used endpoints rounded to milliseconds, accounting for the 1 ms difference on the many-speaker clip. Elapsed time with two active IDs measures the detector's output. An estimate of recall would require a listener to mark the individual overlaps.

Over the known 0.500–3.875 s overlap, scale-invariant signal-to-distortion ratio (SI-SDR) against solo A was −0.36 dB for the mix and −0.36 dB for either mask. Against B it was +0.27 dB for the mix and +0.24/+0.25 dB for the two masks. All four changes were under 0.03 dB in magnitude. The solo references include background sound, so this measures fidelity to the two source excerpts rather than to studio-clean voices.

**What Whisper decoded from those masks.** In the control, medium decoded the longer mask as the line about フリーレン and ただ酒. The shorter mask produced `おまえが広場に僕たちの調子を使ってくれそうな…`. It recovered `広場` and `僕たち`, both absent from the whole-mix decode, but lost the solo reference's `王様`. Changing the surrounding audio changed which mixture component Whisper followed. The sample-by-sample comparison shows why even a recognizable phrase on a labeled track is insufficient proof of its owner.

On S01E10, the mask for ID 00 contains digital silence until 22.745 s. Whisper emitted eight segments ending before that first retained sound, including repeated dialogue. ID 02's only decoded segment was at 0–5 s, also entirely silent on its mask. Neither transcript supplies a defensible pair of lines for the 25–28 s interruption. The recognizer used the same multilingual medium checkpoint on all four full-length mask WAVs, in Japanese on CPU with three threads and full JSON output. All six fresh diarization scans, including S01E01–03, reproduced the previous recording-local turns to the millisecond.

**PixIT setup.** After both access requests were granted, the pipeline configuration (`9486b106`) and separation checkpoint (`4d38e95c`) downloaded successfully. The released configuration uses an ECAPA speaker embedding, a five-second analysis window with a half-second step, and a 0.32 s context allowance around speech. All inference used local audio. [Pipeline](https://huggingface.co/pyannote/speech-separation-ami-1.0) · [Checkpoint](https://huggingface.co/pyannote/separation-ami-1.0)

## Models worth retaining

| Model | Input → output | Role in the experiment |
| --- | --- | --- |
| pyannote PixIT, `pyannote/speech-separation-ami-1.0` | A mono 16 kHz recording → a diarization annotation and an array of estimated source samples. The published example maps each column to an entry in `diarization.labels()`. CPU is supported. | First choice to test a whole recording with unknown speaker count. The model was trained on distant-microphone AMI meetings. Recovery of Japanese acting, laughter, songs and speech under effects requires local evidence. [Pipeline and WAV export](https://huggingface.co/pyannote/speech-separation-ami-1.0) |
| pyannote ToTaToNet, `pyannote/separation-ami-1.0` | A five-second mono window → activity estimates and up to three local source waveforms. | PixIT's underlying checkpoint. The full pipeline associates local outputs across windows. A raw column number can change speakers between windows. [Checkpoint and limitations](https://huggingface.co/pyannote/separation-ami-1.0) · [Pipeline implementation](https://github.com/pyannote/pyannote-audio/blob/3.3.2/pyannote/audio/pipelines/speech_separation.py) |
| Scicom, `Scicom-intl/voice-isolator` | An enrollment clip and a mono 16 kHz mixture → one target-speaker waveform. | The 555M-parameter GPU release ran locally through ROCm. The smaller CPU and ONNX packagings are additional options without a verified Radeon benchmark here. [Tested GPU release](https://huggingface.co/Scicom-intl/voice-isolator) · [CPU release](https://huggingface.co/Scicom-intl/voice-isolator-cpu) · [ONNX packaging](https://huggingface.co/TigreGotico/audiosronnx-voiceisolator) |
| SpeechBrain, `speechbrain/sepformer-whamr` | An 8 kHz mono mixture → two estimated speech waveforms. Trained on English speech with noise and reverberation. | Documented PyTorch GPU path. Radeon execution, Japanese dialogue quality and cross-scene ownership remain untested here. [SepFormer model card](https://huggingface.co/speechbrain/sepformer-whamr) |

## Scicom with a fixed reference voice

We tested the proposed sequence end to end. First, `pyannote/speaker-diarization-3.1` ran on the Radeon with both its segmentation and WeSpeaker embedding models on HIP. For each local ID we looked for continuous samples with exactly one predicted active speaker, trimmed 80 ms from each edge, and took up to three seconds. The minimum accepted duration for this experiment was one second. These are candidate solo turns from the original soundtrack. A single predicted ID can still contain music, laughter or missed speech.

The reference was encoded once per voice. We then streamed the **entire original recording** through `Scicom-intl/voice-isolator` with that embedding fixed, including intervals the scanner had assigned to someone else. Each run used the 555M release at revision `20eee919`, FP32, one-second chunks and PyTorch GPU attention. We flushed the final chunk and removed the model's 160-sample stream delay. The output has exactly the input's sample count at 16 kHz. Native float WAVs were preserved. Whisper and the listening comparisons used PCM16 copies with one shared export gain across a recording's outputs. [Scicom GPU release](https://huggingface.co/Scicom-intl/voice-isolator/tree/20eee9195213dde59d957578b06782058a76b524) · [Reference loader and inference](https://huggingface.co/Scicom-intl/voice-isolator/blob/20eee9195213dde59d957578b06782058a76b524/vi/infer.py)

We also ran the publisher's whole-file `run_offline` implementation on the original nine-second control with each reference. For both voices its output and the clock-corrected stream had zero-lag correlation above 0.999999, with relative error energy below −121 dB. Streaming and timestamp compensation reproduced the reference computation on this control.

### Did the enrollment change which voice survived?

We used two controls from S01E01. The first gives the extractor an unusually favorable reference: the entire original solo excerpt for each voice, including the exact words later mixed together. The second takes only the first 1.5 s of each solo for enrollment, then mixes the *remaining* samples. Those reference samples never occur in the held-out mixture. Both mixes start A and B together at 0.500 s, at equal gain. SI-SDR improvement measures the output against the designated target at zero lag over the known waveform overlap. Labels were fixed by enrollment before scoring.

| Test | A-enrolled output | B-enrolled output |
| --- | --- | --- |
| Full solo references, 3.375 s of waveform overlap | SI-SDR changed by −1.43 dB. Whisper emitted repeated あ. | +0.21 dB. Whisper also emitted repeated あ. |
| Disjoint references, 1.875 s of waveform overlap | −1.34 dB. The transcript combined A-like words about 僕たち with B's ending. | +0.34 dB. The transcript had nearly the same combined wording. |
| Only A's held-out speech present | A remained, with energy 1.33 dB below the input. | The absent B's track attenuated A by 34.73 dB. |
| Only B's held-out speech present | The absent A's track retained B within 0.79 dB of the input. | B remained within 0.83 dB of the input. |

The absent-speaker check matters for cue generation. Enrollment B successfully rejected A alone. Enrollment A passed B alone at nearly the level of B's own extraction. A transcript on A's track could therefore credit A with a line spoken entirely by B.

### What happened in the real scenes

| Clip | Scan / extraction time | Enrolled voices | Observation |
| --- | ---: | ---: | --- |
| S01E10 | 7.0 / 8.6 s | 3 of 3 | Both likely participants had references outside 24–29 s. At the diarizer's marked 26.221–26.744 s overlap, outputs 00 and 02 had waveform correlation 0.96 and energies 4.99 and 4.60 dB below the mix. Several recognitions remained ambiguous. |
| S01E10-multi-speakers | 3.5 / 13.0 s | 4 of 4 | From 9–19 s, all four tracks retained the explanation about chance or the universe in their Whisper output. Pairwise waveform correlations rounded to 0.99–1.00, and the four energy changes were −1.32 to −1.25 dB. Different enrollment IDs yielded nearly the same signal in that passage. |
| S01E01 | 5.4 / 16.9 s | 4 of 4 | The recurring character's reference was 27.092–30.092 s. Another ID's reference at 7.789–9.637 s lies in the listener-marked laughter. The scanner's exclusivity criterion alone admits non-dialogue references. |
| S01E03 | 6.9 / 6.0 s | 1 of 2 | Only one ID had a long enough solo candidate outside the held-out 44–49 s exchange. The other ID remains unresolved. |
| S01E02 | 10.1 / 25.8 s | 3 of 3 | These are three predicted voice clusters in a song. Their extracted WAVs and ASR are available for review. Lead and chorus identity would require listening evidence. |

**S01E10 listening check.** The two candidate references were 22.825–23.920 s for ID 00 and 20.648–22.412 s for ID 02. The listener heard the original 24–29 s scene, each reference, and the identical scene extracted with that reference. Both extracts removed much of the background music. In each extract the other character still came through strongly enough to interfere with understanding the intended voice. Switching enrollment reversed the roles. This is audible conditioning, with insufficient isolation to accept either line automatically. The review did not independently certify the purity of both enrollment clips.

On S01E01, the track enrolled from the confirmed recurring character produced the candidate `生草ホース。` at 39.08–40.60 s, close in sound to the listener's “namaguso bosu.” The same track also transcribed the preceding character's line about free alcohol. Preserve the short phrase as a candidate for listening and orthographic review. On the many-speaker example ID 01 used a sole-active reference at 20.100–21.840 s, outside the measured 9–19 s passage. IDs are local to each recording and provider.

Across the five natural clips, the initial scan took 32.8 s and extraction took 70.2 s for 15 enrolled voices in total. Peak PyTorch allocation during extraction was about 2.41 GiB. These extraction times include enrollment, GPU transfer of chunks, writing float audio and synchronization. Each additional enrolled voice adds another full-recording pass. Whisper took 69.5 s for the 15 tracks and 16.9 s for the original mixtures. The measured stages sum to 189.4 s per 258.9 s of material. At this cast mix, a linear season estimate is about **17.6 minutes per 24-minute episode, or 3.5 hours for twelve**, before human review. This estimate excludes model loading and preprocessing and does not measure a natural full season.

**Measured at episode length.** For a continuous 24-minute timing run, we repeated the original many-speaker soundtrack to exactly 23,040,000 samples and extracted one enrolled voice with one persistent stream state. Scicom wrote exactly 23,040,000 output samples in **141.55 s (2 min 22 s)**, about 10.2× real time. The measured PyTorch peak was 2.41 GiB. At that rate, extracting one voice across twelve episodes costs about 28.3 minutes. Four separately enrolled voices would cost about 1 h 53 min for extraction alone. This duration test establishes throughput and clock preservation. The five natural excerpts and the listening checks establish what was actually isolated.

## Consequence for the Python architecture

Keep the original mixture, voice-activity intervals, estimated source audio and ASR hypotheses independently addressable on the media timeline. For each waveform store the producing model and revision, recording-local voice ID, original time offset, sample rate, and any trimming, padding or measured delay. Preserve the mixed-audio transcript alongside per-source hypotheses. An editor can replay a disputed phrase in the mix and in each candidate source without losing the other speaker's onset.

The cue planner can render two verified phrases with separate starts and ends. Where the evidence establishes two voices but yields only one phrase, retain the unresolved voice interval for review. A third intelligible voice should survive in the timeline even when the display needs an editorial choice. [Guide on interruptions and crowded scenes](japanese-subtitling-craft-for-yomisub.md#5-multiple-speakers-and-their-visual-presentation)

For an enrolled extractor, keep the reference's source recording, sample range, local ID and listening status alongside the output. Make it possible to replace a mistaken reference and rerun only that voice. A reference that cannot be found or includes a second voice is a reason to leave ownership open. If two extracted outputs reproduce the same speech during an interruption, keep the original mixture and the unresolved second line available for review. The throughput and listening evidence support optional extraction for audition. Selecting a GPU-capable provider is a separate decision from approving its words for display.

## Repeat the GPU benchmarks

Both portable probes require a visible ROCm device. The PixIT probe verifies GPU placement of the separator and the speaker embedder. The Scicom probe verifies model parameters on the device, uses a fixed enrollment, and preserves the original sample count. The test environment is separate from the Python 3.13 GTK application. The pinned packages reproduce the tested Linux x86-64, Python 3.12 environment. [Research environment](../experiments/speaker-models-rocm-requirements.txt) · [PixIT probe](../experiments/benchmark_pixit_rocm.py) · [Scicom probe](../experiments/benchmark_scicom_rocm.py)

From the repository root on the research workstation, the following commands use the installed environment and downloaded release. Choose fresh output paths for each invocation.

```bash
d=gitignored-inputs/speaker-separation-2026-11-19
src=gitignored-inputs/whisper-feasibility-2026-11-19
export HF_HOME="$PWD/$d/cache/huggingface" PYANNOTE_CACHE="$PWD/$d/cache/pyannote"
export HF_HUB_OFFLINE=1 TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1 MIOPEN_FIND_MODE=FAST
"$d/venv-rocm/bin/python" experiments/benchmark_pixit_rocm.py "$src/together.wav" "$d/replay-pixit" --speakers 2
"$d/venv-rocm/bin/python" experiments/benchmark_scicom_rocm.py "$d/scicom-upstream" "$src/10.wav" "$d/scicom/10/ref-SPEAKER_02.wav" "$d/replay-scicom-02.wav"
```

For a fresh installation, create a Python 3.12 research venv with uv and install the pinned requirements into it. Download the two accepted PixIT repositories and dependencies before switching to offline mode. The Scicom probe loads the publisher's local directory containing `vi/`, `config.json` and `model.safetensors` from the revision recorded above. Use the repository's Vulkan whisper-cli build with `-l ja -t 3 -ojf` on 16 kHz PCM16 exports and confirm the Radeon device and backend in its log. [Vulkan build instructions](../README.md#build-the-vulkan-transcription-engine)

Local experiment audio, activity intervals, logs and Whisper JSON are under `gitignored-inputs/speaker-separation-2026-11-19/`. The original 16 kHz inputs, solo references, whole-mix transcripts and source hashes are under `gitignored-inputs/whisper-feasibility-2026-11-19/`.

The PixIT download reads `HUGGING_FACE_TOKEN` from the repository's ignored `.env`. The public Scicom download needed no credential. The example recordings, references, extracted audio and VLC comparison videos stayed local. [Environment template](../.env.example)
