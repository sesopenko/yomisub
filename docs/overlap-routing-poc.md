# Does routing overlaps to Whisper large-v3 improve the subtitles?

**The router found all three test overlaps on the RX 9060 XT. None yielded two usable, separately attributed subtitle lines.** The tested strategy sent the original audio between overlaps to medium, separated each detected overlap, and sent each resulting track to large-v3. On S01E10 the cut split a phrase that medium recognized on the continuous mix. The sample comprised one natural interruption and two constructed events using the same utterances.

## What happened in the subtitles?

| Recording | What the scan found | What a learner would see or hear |
| --- | --- | --- |
| S01E10, natural interruption around 25–28 s | Two voices at **26.221–26.744 s**, inside the interval identified by ear. The exact syllable boundaries are unknown. | Large-v3 on the two isolated cores produced **はい** and **お待ちしております**. The listener heard repeated **まって** and approximately **あつりょくに くっしねえ**. Medium after the cut recovered only **つりくにくっしね** of the latter. Continuous medium recovered both phrases, placed the repeated **まって** too early, and repeated the pressure line. Full-clip large-v3 garbled the exchange. |
| Two known voices starting together | **0.537–3.879 s** detected against **0.500–3.875 s** constructed. | The 0.537 s preceding block, with only 17 ms of detected solo voice, even produced a spurious thank-you subtitle. In the overlap, one stem yielded gibberish. The other retained **広場** and **僕たち** but confused the statue wording. Neither supplied the free-drink phrase during the overlap. Full-mix large-v3 recovered recognizable parts of both lines in sequence. |
| Same voices, staggered interruption | **14.274–16.332 s** detected against **14.000–16.375 s** constructed. | One stem yielded **ブリビでクレンサーだ**. The other turned statues into **地元** (“hometown”). Large-v3 on the full mix recovered both complete phrases, but placed the second at 15.96 s, nearly two seconds after its known onset. |
| Alternating control, same recordings | Zero overlapping intervals. | Medium kept the king/statues and free-drink lines separate. It wrote the homophone **蝶像** for **彫像**. |
| S01E01, ordinary dialogue | Zero detected overlaps. | Medium kept the words the listener heard about the king, square and free drinks, with the same statue spelling error. The lines had different voice IDs. The later short aside shared an ID with the earlier 25–30 s voice, consistent with listening. |
| S01E03, fight | Zero detected overlaps. | Medium recovered **こうします／そう／たえられる**, all three listener-confirmed phrases. The scan assigned one ID to all three. The listener had identified the speakers as **A/B/B**. |

**Did additional context rescue S01E10?** Each separated core came from a waveform estimated with up to two seconds of real audio on either side. In a second decode, large-v3 also heard that surrounding audio. Source 1 recovered **だれかいるのか** from nearby dialogue. Source 2 produced a stock “thank you for watching” line. The original mix over the identical 24.221–28.744 s window gave the repeated **まって** and **だれかいるのか**. Neither padded stem recovered the pressure phrase. An earlier large-v3 run on the original 24–29 s window did recover it. A change of crop can change the words. [Earlier listening evidence](speaker-separation-findings.md#s01e10-interruption-at-2528-s)

**Did the separator distinguish the speakers?** To check independently, compare each estimated waveform to the two original utterances used to make the controls. In the same-onset overlap, source 2 correlated more with the king/statues recording (0.61 versus 0.42 for free drinks). Source 1 favored free drinks (0.62 versus 0.24). The staggered case had the same preference. These are absolute waveform correlations over the intersection of the detected and known overlap, with the references resampled to the same 8 kHz clock. They reflect background sound too. A favored voice was measurable even when its subtitle was wrong.

**Could the router identify those voices on its own?** It left ownership open on all three overlaps. The experiment compared each core's WeSpeaker embedding to the longest sole-active excerpt per participating ID, up to four seconds, requiring at least one second on both sides of each comparison. S01E10's core was only 0.523 s. In both controls one cluster lacked a qualifying solo reference. In the staggered control the same king/statues recording had one cluster on its solo appearance and a different one during the interruption. Known clean references were used only to evaluate the outputs. An editor seeing “source 2” cannot infer the same actor in the next excerpt.

## Cost on the Radeon

Six recordings contained **193.93 s** of audio. Only **5.92 s** triggered separation. Three overlap windows generated **11.85 source-seconds** for large-v3. These are single-run wall times with already-cached weights. Whisper ran on Vulkan and both speaker models ran on ROCm.

| Work measured across the six files | Seconds |
| --- | ---: |
| Decode, scan, prepare waveforms and check ownership | 21.87 |
| ↳ Speaker scan alone, already included above | 19.58 |
| Routed Whisper batches, medium and large-v3 combined | 21.36 |
| **Routed total** | **43.23** |
| Continuous medium ASR alone | 14.53 |
| Continuous large-v3 ASR alone | 20.80 |

The routed ASR by itself took about as long as continuous large-v3. Each active model loaded once per recording and decoded all its assigned clips in one batch invocation. The total excludes Python startup, 1.57 s of shared speaker-model initialization, separate comparison decodes and preview rendering. A planner that also needs voice metadata must budget for the scan on either path. Season throughput needs a full-episode run.

## Recommended strategy for the next build

1. Run medium on the continuous mix and retain the independent speaker scan. Use the scan to flag candidate interruptions and to propose recording-local identities.
2. For each flagged interruption, try large-v3 on a contextual **original mix** and optionally on both separated sources. Keep the original times, texts and waveform for each. A word from the mix remains available if separation loses it.
3. Accept a second displayed line only when its wording, owner and interval have support. Preserve the second voice interval when its words remain unresolved. The S01E10 draft demonstrates the distinction visually. Its two subtitle rows appear together, but both contain the wrong words. [Guide on interruptions](japanese-subtitling-craft-for-yomisub.md#54-interruptions-carry-information)

The experiment measured the continuous transcript and the alternative decodes separately. Automatic selection among competing phrases, speaker verification across excerpts, and the end-to-end cost of this recommended strategy remain unverified. Use the staggered control to check both speaker assignments and the transition from one visible line to two and back to one. The second source recording enters at 14.000 s and the first ends at 16.375 s. Those are known waveform boundaries. Use the solo recordings to check where the spoken phrases begin and end within them. The natural S01E10 listening check can establish whether both phrases survived, while their exact onset and end still need review.

## Reproduce the experiment

The first command decodes the selected audio track to mono 16 kHz and scans the whole recording. Contiguous regions with at most one active ID stay together, including silence between turns, so medium receives continuous audio. Entirely inactive regions are skipped. Exact two-ID overlaps go to two-source SepFormer WHAMR at 8 kHz. The probe flags three or more IDs or cores over 12 s for review. The second command runs Japanese transcription with beam size and best-of both set to five. It compares the cores, the padded stems, the identical padded mix and both full-mix baselines. Model revisions and environment dependencies are in the separation report. [Preparation script](../experiments/route_voice_activity.py) · [ASR and subtitle script](../experiments/transcribe_voice_routes.py) · [Model environment](speaker-separation-findings.md#reproducing-the-tests)

```bash
models=gitignored-inputs/speaker-separation-2026-11-19
controls=gitignored-inputs/whisper-feasibility-2026-11-19
run=gitignored-inputs/overlap-routing-repeat
"$models/venv-rocm/bin/python" experiments/route_voice_activity.py \
  "$models/sepformer/model" "$run" gitignored-inputs/examples/S01E10.mp4 \
  "$controls"/{together,mix,serial}.wav gitignored-inputs/examples/{S01E01,S01E03}.mp4
python3 experiments/transcribe_voice_routes.py \
  ~/src/github.com/ggml-org/whisper.cpp/build/bin/whisper-cli \
  ~/.cache/yomisub/models/ggml-medium.bin gitignored-inputs/models/ggml-large-v3.bin \
  "$run"/{S01E10,together,mix,serial,S01E01,S01E03}
```

The original artifacts are under `gitignored-inputs/overlap-routing-poc/`. Each recording has `routes.json` (sample clock, scan, source-to-mix mapping and voice evidence), `results.json` (raw and bounded times, text and costs), per-run Whisper JSON/logs and `routed.ass`. The ASS is a machine draft with independent rows for the two local sources. Only the strict route is displayed. For an embedding match the two stems must prefer different IDs, each with cosine similarity ≥0.35 and a lead of ≥0.10. These experimental thresholds were never reached for both speakers and remain uncalibrated. Diagnostic decodes and listener corrections never enter it. The individual S01E10 preview `S01E10/interruption-draft.mp4` plays source time 23–29.5 s with the original stereo soundtrack.
