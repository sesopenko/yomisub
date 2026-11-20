# From Whisper output to Japanese learner subtitles

**Build the first version from a transcript of the original soundtrack and an independent timeline of who is speaking.** Use full-context, multilingual Whisper on the mix for candidate Japanese wording. Use pyannote diarization for recording-local voice IDs and possible overlaps. Give each subtitle phrase its own text, speaker, start and end. Two phrases must be able to occupy the same instant. Whisper’s ordered segments are useful input, but publishing them directly can turn an interruption into a reply. [Editorial brief and worked overlap example](japanese-subtitling-craft-for-yomisub.md#53-the-same-words-with-actual-overlap)

**The first version can** preserve the Japanese, propose linguistically sensible cuts, flag unsupported timing or ownership, and render independently timed phrases in stable positions. **Recovering both simultaneous lines with verified boundaries still requires review.** On this Radeon, full `large-v3` on the mix is the best-supported starting point from the listening tests. Keep the checkpoint selectable. The small sample establishes useful regression cases, not an episode-wide accuracy ranking. [Model comparisons and GPU measurements](speaker-separation-findings.md)

## What S01E10 requires the data model to preserve

At about 25–28 s in `S01E10.mp4`, Sean heard one voice repeat `まって` while another spoke over it. The three inputs capture different parts of that moment.

| Source | What it established | What Yomisub should retain |
| --- | --- | --- |
| Whisper large-v3 on the original 24–29 s mix | It put `まって、まって、まって` at 26–27 s and `あつりょくに くっしない` at 27–28 s, one after the other. | Two candidate texts and their original ASR times. Publishing those times would lose the interruption. |
| Independent pyannote scan | Two recording-local IDs were active together at 26.221–26.744 s. The shorter voice turn lay inside the longer one. | A reviewable overlap interval. Its edges locate detected voice activity. The syllable at each edge remains unknown. |
| Original stereo replay at half speed | Sean heard “atsryokuni kushine” from the other voice. This supports the pressure phrase and suggests the colloquial ending `くっしねえ`. Both separated tracks missed the pressure phrase in ASR. | Link the listener’s phonetic reading to this utterance. Keep the competing ending and the unresolved phrase boundaries. [Listening and separation evidence](speaker-separation-findings.md#s01e10-interruption-at-2528-s) |

Once both phrase intervals are supported, show the first phrase at its onset, add the second in its own position when it enters, and clear each when it ends. A known-time render test produced **A alone → A+B → B alone → clear**. The continuing line stayed in the same position in FFmpeg/libass. Plain SRT can switch between the active texts and end the last cue to clear the screen. Positioning depends on the player. If only one line is recoverable, keep the second voice interval available for review. A third intelligible voice should likewise survive an eventual layout conflict. [Guide to interruptions and crowded scenes](japanese-subtitling-craft-for-yomisub.md#54-interruptions-carry-information)

## Decisions for the Python implementation

For an ordinary phrase with usable times and a single supported voice, propose a cue and keep its evidence. If the words are usable but two owners are plausible, leave ownership open. If a second voice is audible but has no recoverable words, keep that interval for review. These are distinct outcomes an editor can correct independently.

| Build in this order | Decision | Evidence behind it |
| --- | --- | --- |
| 1. Preserve the recording clock in `media.py` and `generation.py`. | Retain the audio stream, channel layout, media start, sample rate and sample count. Map each crop or derived waveform back to the original samples. Preserve the stereo original for replay. | A 6.328 s crop yielded a segment ending at 7.960 s. An export needs bounds checks even for plausible text. |
| 2. Replace the raw SRT handoff with structured observations from `whisper.py` and a proposed `speakers.py`. | Store raw segment text, text-piece offsets and times, run settings, and raw voice turns. Keep overlap events even if they have no words. For a candidate phrase, measure covered time per voice, simultaneous time and uncovered time on half-open intervals. Retain competing owners and listener corrections. | On S01E03 a listener identified the three turns as A/B/B. The diarizer assigned the same ID to all three. On S01E01 a repeated ID at 25–30 s and around 40 s *did* agree with the listener. A longest-intersection rule cannot distinguish those cases. |
| 3. Reuse Sudachi in a proposed `japanese.py`, then choose phrase times in `spotting.py`. | Map exact Unicode surface spans back to Whisper pieces. Protect particles with their phrases and negatives or contractions with their predicates. Propose a timed cut only where the audio supports an edge. Otherwise keep the wider phrase provisional. | Sudachi splits `できない` into `でき / ない` and `食べちゃった` into several pieces. In S01E03 only 22 of 39 internal Sudachi boundaries had usable adjacent ASR timing anchors. A readable line break alone supplies no timestamp. |
| 4. Lay out the active phrases in `layout.py`, then serialize in `subtitles.py`. | Sweep phrase starts and ends. Give concurrent voices stable positions and neutral labels where needed. Flag the combined reading demand of both lines while keeping each phrase with its speech. Preserve atomic publication to `<stem>.<language>.srt`. | The current writer adds 0.5 s and caps duration at 6 s. This can leave the first voice on screen after it stops or cut it off while it continues. Move timing into the cue planner. [Current writer](../yomisub/subtitles.py) |

Keep the earlier app’s tokenization work. Its previous join indexes a list by surface length and takes the first record’s speaker. A Whisper piece can span multiple characters or include a leading space. Join by character offsets, check that the original string reconstructs exactly, and allow a surface to have missing time or ambiguous ownership. These runs tested native whisper.cpp timings. The older app’s WhisperX alignment remains unevaluated here. [Earlier tokenizer](https://github.com/sesopenko/yomisub/blob/8ab562e92647b7c370dd51f6b28fddba5c0999da/subtitles/tokenization.py) · [Earlier diarization workflow](https://github.com/sesopenko/yomisub/blob/8ab562e92647b7c370dd51f6b28fddba5c0999da/yomisub.py#L346)

## Acceptance cases for the build

| Case | What a passing result demonstrates |
| --- | --- |
| S01E10 interruption and the constructed same-onset mix | Score overlap detection, text recovered per voice, ownership, and onset/end independently. On the known 0.500–3.875 s waveform overlap, pyannote marked 0.537–3.878 s while medium recovered only one line. On a staged interruption it put the second speaker’s text 1.960 s after that speaker’s waveform entered. Preserve those discrepancies for review. |
| S01E03 fight | Retain the listener’s A/B/B assignment for `こうします`, `そう`, `たえられる`. Reject inverted or out-of-range piece times. The first sentence had a plausible onset near 15.5 s, yet one piece ran from 15,480 ms back to 2,970 ms. A DTW point for `そう` also fell outside its detected turn. |
| S01E01 dialogue and laughter | Preserve the confirmed recurring voice, the brief aside around 39–40 s, and uncertainty over its spelling. Laughter can attract a voice ID. A music label crossing a voice interval supplies no spoken words to assign. |
| S01E02 theme song | Preserve the listener-confirmed instrumental break at about 19–29 s. After 78 s the lead stops and a chorus remains audible. Identical gaps in a transcript therefore call for two different editorial decisions. |
| S01E10 many-speaker clip and three-voice layout | Sean heard several interruptions. The base scan returned only 136 ms of coactivity across the clip. The tested segmentation model can represent at most two active voices per frame. Retain externally supported overlap and a third phrase even when the detector misses them or two lines are already occupied. Flag crowding for editorial review. |
| Export and replay | On known boundaries test A alone, both, B alone, then neither. Include a late negation, a short response, a nonzero media origin and a phrase crossing the end of a clip. Reject timing outside the available media. Replaying the same evidence and editorial choices should produce the same cues. |

Camera cuts, character names, visual obstructions, narrative importance and learner comprehension require other evidence. The audio-only planner can preserve unknowns and use fixed positions. [Scope of audio-only decisions](japanese-subtitling-craft-for-yomisub.md#11-applying-the-craft-with-audio-and-text-alone)

## Whisper input and output reference

The tested whisper.cpp build encodes 16 kHz audio in nominal 30 s windows. For medium, it computes 80-band log-Mel features using a 25 ms analysis window and a 10 ms hop. The decoder predicts Japanese text pieces and timestamp tokens in a single sequence. Segment boundaries are reported on a nominal 20 ms grid. A reported boundary can still be seconds away from the audible onset. Full JSON adds estimated piece intervals, including interpolation and energy-based adjustments. [Whisper architecture](https://github.com/openai/whisper#approach) · [Pinned timing implementation](https://github.com/ggml-org/whisper.cpp/blob/231638a0717b7822784297e5980965ffcec05810/src/whisper.cpp#L8790)

| Option or field | How to use it |
| --- | --- |
| `-m`, `-l ja`, `-f`, `-of` | Select the multilingual model, Japanese transcription, source WAV and unique output stem. `-tr` requests translation. Record the model hash, build, options, stream and backend. |
| `-oj`, `-ojf` | Both write JSON. Ordinary JSON supplies segment text and offsets in milliseconds. Full JSON enables piece timing and adds `tokens[]`, token IDs, lexical probability `p`, optional offsets and `t_dtw`. Filter control tokens by vocabulary. The writer can combine decoder bytes to complete a UTF-8 character. Treat `p` as evidence about the text choice only. |
| `-osrt`, `-ovtt`, `-ocsv`, `-otxt` | Alternative serializations. All 64 default segments matched on the fields shared across the writers. Switching export formats adds no speaker or acoustic evidence. |
| `-dtw medium -nfa -ojf` | Match the DTW preset to the checkpoint and verify `dtw = 1` in stderr. A nonnegative `t_dtw` is a point in 10 ms ticks. The value `-1` means unavailable. The five alternate decodes yielded 68 segments and sometimes different words. Associate points with their own run. |
| `-ml`, `-sow`, `-wt` | Maximum length can enable token timing and wrapping. Space-prefixed tokens give `-sow` few useful boundaries in Japanese. `-wt` sets a timestamp-probability threshold. Use unwrapped text for the Sudachi join. |
| `-bs`, `-bo`, `-tp`, `-tpi`, `-nf`, `-et`, `-lpt`, `-nth` | Beam width, candidate count, sampling, fallback and decoder thresholds can change or suppress text. The tested defaults included beam/best-of 5, temperature 0, increment 0.2 and no-speech threshold 0.6. A wider search changed segment boundaries even when a disputed word stayed the same. |
| `-di`, `-tdrz`, `--vad` | Stereo labeling compares channel energies per segment. TinyDiarize requires compatible weights and can mark a next turn. VAD gates likely speech. For recurring anonymous speakers and simultaneous turns use a separate diarization pass. [Tested diarizer](https://huggingface.co/pyannote/speaker-diarization-3.1) |
| `-ot`, `-d`, `-t`, `-p`, `-ng` | Offset and duration are milliseconds. Threads, processors and backend are run settings. The baseline below used CPU. The later large-v3 listening comparisons used Vulkan. [CLI and JSON writer](https://github.com/ggml-org/whisper.cpp/blob/231638a0717b7822784297e5980965ffcec05810/examples/cli/cli.cpp) |

### Timing coverage and reproduction

These counts are from the original full-context medium runs. A usable internal cut coincides with a whole ASR-piece edge whose adjacent intervals are positive, ordered and within segment and media bounds. This is an upper bound on cuts with timing evidence under this rule. An anchor can pass validation and still miss the spoken boundary.

| Measurement | S01E01 | S01E02 | S01E03 | S01E10 | S01E10 multi |
| --- | ---: | ---: | ---: | ---: | ---: |
| ASR segments / voice turns / voice IDs | 9 / 10 / 4 | 16 / 24 / 5 | 10 / 12 / 2 | 15 / 15 / 3 | 14 / 12 / 4 |
| Unusable piece intervals / text pieces | 4 / 110 | 18 / 214 | 14 / 58 | 15 / 109 | 3 / 142 |
| Internal cuts with usable anchors / candidates | 57 / 74 | 103 / 148 | 22 / 39 | 50 / 69 | 83 / 90 |

On 19 November 2026, FFmpeg 7.1.5 decoded the Japanese soundtrack of each excerpt to 16 kHz mono PCM16. The five clips had zero media start. The baseline used whisper.cpp `1.9.5-dev` (adjacent source `231638a0`), multilingual medium and pyannote `speaker-diarization-3.1` at `84fd2591`. Run the recognizer and diarizer independently on the same samples. Read RTTM onset **and duration** in seconds and carry the exact sample origin when converting cropped results back to media time. [Recorded voice turns](whisper-example-speaker-turns.rttm)

~~~bash
ffmpeg -nostdin -v error -i "$clip" -map 0:a:0 -ac 1 -ar 16000 -c:a pcm_s16le "$stem.wav"
whisper-cli -ng -t 4 -m "$model" -l ja -f "$stem.wav" -ojf -osrt -ovtt -ocsv -otxt -of "$stem-full"
whisper-cli -ng -t 4 -m "$model" -l ja -f "$stem.wav" -nfa -dtw medium -ojf -of "$stem-dtw"
~~~

The ignored directory `gitignored-inputs/whisper-feasibility-2026-11-19/` holds `manifest.json`, `inputs.sha256`, per-clip `*-joined.json`, the source recordings used in the controls and the analysis scripts. GPU results and their reproduction commands are in the [speaker-separation report](speaker-separation-findings.md#reproducing-the-tests).
