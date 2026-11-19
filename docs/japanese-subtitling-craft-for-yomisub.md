# Japanese Subtitling for Language Learners

## Purpose and editorial brief

This is a foundation in the theory and craft of presenting Japanese speech as Japanese subtitles, written for yomisub’s author and development agents. The intended viewer is a learner who wants to follow Japanese shows with help from the written language. English explanations accompany the Japanese examples; the examples do not assume advanced Japanese knowledge.

**The governing priority for yomisub is to keep the displayed Japanese closely tied to the speech currently being heard, even when fast speech makes the subtitles too fast for the learner to finish reading.** Preserve the spoken wording and the relationship between speakers. Improve readability through good grouping and presentation within those constraints. Do not create a backlog of delayed subtitles or silently rewrite dialogue to satisfy a reading-speed target.

This priority reflects the project owner’s stated preference. It is a deliberate editorial brief, not a claim that every subtitle service should make the same tradeoff. The project’s published purpose is already to support language learning through subtitles for foreign television and film. [1](https://github.com/sesopenko/yomisub/blob/main/README.md)

The scope is prerecorded shows and similar audiovisual material. It covers what to preserve, when to display it, how to divide it, how to distinguish speakers, and how to judge quality. The core stays theoretical, without subtitle formats, CLI instructions, or implementation architecture. Section 14 separately answers the requested question about small local language models. Live subtitling is a different production situation: the editor cannot necessarily know or correct the next utterance in advance.

The practical recommendations and worked examples below are an editorial synthesis for this brief. Named professional limits are identified as house rules; research findings retain their audience and study limitations. Research checked on 18 November 2026.

**Reading map:** Sections 3–5 cover timing and multiple speakers; Sections 6–10 cover Japanese language, presentation, and accuracy; Section 11 explains what audio-only evidence can support; Section 12 summarizes research limits; Section 13 is a brief for development agents; Section 14 covers local models; Section 15 collects the sources. Netflix’s *Japanese Timed Text Style Guide* is source 5, with translated subtitles and Japanese SDH kept distinct throughout.

## 1 What a subtitle actually does

A transcript answers “What was said?” A finished subtitle also answers “Which part belongs now?”, “Who said it?”, “How does it fit the scene?”, and “What can the viewer take in before it disappears?” A correct transcript can therefore produce poor subtitles without containing a single misspelled word.

The automatic scope considered here has the audio and transcript, without visual inspection or knowledge of the plot. It can therefore work with audible words, voice distinctions, pauses, and overlap when those are reliably established. Advice about visible faces, screen text, camera cuts, or narrative importance describes the broader craft; applying it requires human review or trustworthy external information. The software should not guess those facts from the transcript.

Terminology varies by country. **Intralingual subtitles** use the same language as the audio; **interlingual subtitles** translate into a different language. **Captions**, particularly accessibility captions, commonly include meaningful non-speech audio as well as dialogue. W3C describes these distinctions while acknowledging regional differences in naming. [2](https://www.w3.org/WAI/media/av/captions/)

| Product | Main purpose | Consequence for editorial choices |
| --- | --- | --- |
| Japanese translation subtitles | Convey dialogue spoken in another language | Wording can be substantially rephrased during translation. |
| Japanese same-language dialogue subtitles | Make Japanese speech available as written Japanese | Correspondence with the audible words becomes directly observable. |
| Japanese accessibility captions or SDH | Provide access to relevant audio for deaf and hard-of-hearing viewers | Speaker identity, significant sounds, music, and delivery can be essential. |
| Japanese learner subtitles for yomisub | Help a learner connect Japanese speech, written Japanese, and the scene | Audible wording and close synchronization deserve particular protection. |

SDH means **subtitles for the deaf and hard of hearing**. It is an audience designation, not a synonym for “more detailed learner subtitles.” Accessibility captions must convey relevant audio information, including speaker identity and meaningful sounds. A learner who hears the soundtrack may need a different amount of supplementary labeling. Some learners also need accessibility captions; the groups can overlap. [3](https://www.w3.org/WAI/WCAG22/Understanding/captions-prerecorded.html)

For yomisub, distinguish four possible benefits:

1. Understanding what happens in the scene.
2. Recognizing which Japanese words were spoken.
3. Learning or remembering language from the scene.
4. Understanding similar speech later without subtitles.

These are separate outcomes. A subtitle may help the first two without proving the last two. Reading an accurate sentence is also different from understanding its vocabulary or grammar. Additional exposure time can help someone finish reading; it cannot by itself explain a word they have never learned.

## 2 Good subtitles balance several kinds of fidelity

For this project, evaluate quality along six dimensions. Treat them as questions about the viewing experience, not interchangeable numerical scores.

| Dimension | The question to ask |
| --- | --- |
| Verbal accuracy | Does the text represent the words actually spoken, including negation, names, and numbers? |
| Meaning and voice | Does it preserve uncertainty, politeness, emotion, relationships, and the speaker’s distinctive wording? |
| Temporal accuracy | Can the learner connect the displayed phrase to the speech they are hearing now? |
| Attribution | Can the viewer tell which person or audio source each line belongs to? |
| Reading clarity | Are the written forms, grouping, line breaks, and presentation easy to decode? |
| Scene integrity | In human or externally informed review, can the viewer still follow visual events, discoveries, jokes, and reactions? |

Professional captioning guidance treats accuracy, consistency, clarity, readability, and preservation of meaning as related aspects of quality. DCMP also cautions against substituting simpler synonyms just because an expression may be unfamiliar. [8](https://dcmp.org/learn/captioningkey/599DCMP)

The additional emphasis for yomisub is **audio–text correspondence**. Suppose a subtitle conveys the right general idea but uses different Japanese from the soundtrack. The learner may search for words that were never spoken. Suppose it preserves every word but appears one exchange late. The learner may attach those words to the wrong person. Both are serious failures for this use case.

Conversely, a fast subtitle that faithfully accompanies a fast line is not automatically defective. It can accurately expose a difficult moment. Accepting that difficulty does not excuse unreadable typography, arbitrary fragmentation, missing text, or poor attribution.

### A compact vocabulary for the craft

| Term | Meaning in this document |
| --- | --- |
| Cue or subtitle event | One timed presentation of subtitle text. It need not equal one sentence. |
| Spotting or cueing | Deciding where subtitle events begin and end. |
| Segmentation | Dividing speech into cues, and dividing a cue into lines. These are different decisions. |
| In-time and out-time | The moments a cue appears and disappears. |
| Exposure or duration | How long the text is visible. |
| Reading or presentation speed | How much displayed text must be processed per unit of time. |
| Condensation | Shortening wording while trying to preserve selected meaning. |
| Speaker attribution | Making clear whose speech a subtitle represents. |
| Backchannel or aizuchi | A listener’s short response, such as an acknowledgment, during someone else’s turn. |
| Ruby or furigana | Small reading annotations associated with characters, commonly kana readings for kanji. |

## 3 Timing is part of meaning

Timing determines which sounds, faces, and actions the reader associates with a phrase. It also determines when information becomes available. A well-timed subtitle can help make a rapid utterance recognizable. A misplaced one can change the apparent conversation.

Ofcom’s accessibility guidance favors close synchronization and near-verbatim speech. It also warns against revealing important information before it is spoken, particularly answers and punchlines. These principles support yomisub’s preference, although Ofcom allows more editing for readability than this project may want. [4](https://www.ofcom.org.uk/siteassets/resources/documents/tv-radio-and-on-demand/broadcast-codes/other-codes/ofcoms-guidelines-on-providing-tv-on-demand-access-services.pdf?v=357066)

### 3.1 Distinguish timing defects from difficult reading

| What the viewer experiences | What is wrong or difficult | Editorial interpretation |
| --- | --- | --- |
| Text arrives after the matching phrase has already ended | Late onset | The learner is comparing current sound with earlier words. |
| A completed phrase from an earlier speaker remains into a subsequent, non-overlapping turn and looks current | Stale text or misleading attribution | Additional exposure has damaged correspondence. |
| Subtitles become progressively further behind during a rapid exchange | Accumulating delay | Reading-time adjustments have created a queue rather than synchronized subtitles. |
| The answer appears before the question or dramatic pause is finished | Premature reveal | The subtitle has changed the experience of the scene. |
| Text begins and ends with the right speech, but there is too much to finish | High reading demand | This can be an acceptable consequence of fast speech under yomisub’s brief. |
| Words flash individually despite forming one short phrase | Excessive fragmentation | Synchronization has been pursued at the expense of useful grouping. |
| Every line is displaced by roughly the same amount | Consistent offset | Different from a local segmentation error or accumulating drift. |

This distinction matters for evaluation. A high character rate is not proof of bad timing. A low character rate is not proof of good timing. More time is helpful only when the text still belongs to the audible event; its relationship to the picture needs separate evidence.

### 3.2 Synchronize meaningful phrases

Close synchronization does not require each character to appear at the instant of its corresponding sound. A short phrase can appear as a stable unit near its onset. This necessarily makes some upcoming words visible slightly before they are spoken. The editorial task is to keep that anticipation small and appropriate.

Long sentences create the opposite problem. Displaying the entire sentence on its first syllable may reveal too much; waiting until its final syllable makes the text late. Divide it into meaningful spoken units so the display follows the sentence as it unfolds.

The boundaries should respond to both language and performance. A breath does not automatically end a thought. A grammatical sentence can contain a long dramatic pause. A speaker can begin a new thought without taking a breath. None of these boundaries is a reliable substitute for understanding the utterance.

Text can suggest a grammatical boundary, but only audio evidence can establish when that part was spoken. A proposed text split does not, by itself, supply a reliable time for the split.

### 3.3 Keep onset and ending decisions separate

At the start, ask whether the text belongs to speech that has actually begun, and whether showing the whole cue would disclose a later response or reveal. At the end, ask whether the phrase is complete and whether something new would make the remaining text misleading.

A small tail into genuine silence can be reasonable when attribution stays clear. It should not be an automatic extension attached to every cue. Netflix’s timing guidance, for example, uses an approximately half-second extension where circumstances permit; that is a particular editorial policy, not a universal requirement. Its broader guidance also permits dialogue to continue across a shot change when the speech itself continues. [7](https://partnerhelp.netflixstudios.com/hc/en-us/articles/360051554394-Timed-Text-Style-Guide-Subtitle-Timing-Guidelines)

For yomisub, prefer clearing the text with the end of its phrase. Do not import a routine reading-time extension from another service’s house style. Small boundary adjustments can be judged by whether they still feel synchronized, but an unfinished read is not a reason to retain obsolete text. Equally, do not erase an ongoing speaker merely because a second person starts talking: that is overlap, and both may still be current.

### 3.4 Shot changes and scene changes are different

A **shot change** switches the camera view. A **scene change** may move the story to a different place, time, or event. A person can speak continuously while the camera cuts to the listener. Their subtitle still belongs to that speech.

When a human editor or trustworthy external annotation identifies a cut, coordinate with it where doing so preserves the audio relationship. Do not force every cut to become a new subtitle. An old line hanging into an unrelated scene deserves particular attention because the new image can make it appear to refer to the wrong event.

These are picture-dependent checks. The current audio-only process cannot establish whether text covers a face, misses a visual joke, or crosses a scene transition badly. Keep its timing grounded in the speech; do not infer camera cuts or scene changes merely from silence or a change of topic. Visual review can be a separate quality step without being a prerequisite for the present automatic workflow.

## 4 How long should a subtitle stay visible

There are two different questions:

- **How much exposure would make this text comfortable for this viewer?**
- **How much exposure is available while it remains connected to this speech?**

For yomisub, the available speech interval constrains exposure. Desired reading comfort remains useful information about difficulty.

### 4.1 Use character rate as a description

For a cue, the basic calculation is:

**Characters per second = counted displayed characters ÷ visible seconds.**

The reverse calculation, **characters ÷ chosen rate**, estimates the exposure needed to meet that chosen rate. It does not tell you whether that much exposure is available, whether the words are familiar, or whether moving the boundaries would be editorially acceptable.

An invented example makes the conflict concrete:

| Same text | Display duration | Calculated demand |
| --- | --- | --- |
| 18 counted characters | 3 seconds | 6 characters per second |
| 18 counted characters | 6 seconds | 3 characters per second |

If the actual utterance occupies three seconds and the next speaker begins immediately, the six-second version lowers the calculated rate while making the timing worse. Under yomisub’s brief, keep the relationship to the three-second utterance. The two rates here are arithmetic examples, not recommended learner settings.

### 4.2 Professional numbers are scoped conventions

| Published reference | Stated convention | What it does not establish |
| --- | --- | --- |
| Netflix Japanese translated subtitles, Section I | Up to 4 characters per second; 13 full-width characters per horizontal line | A universal limit for reading Japanese or learning Japanese |
| Netflix Japanese SDH, Section II | Up to 7 characters per second; 16 full-width characters per horizontal line | A comfortable rate for an N4/N5 learner |
| Netflix general requirements | Event duration from five-sixths of a second, approximately 0.833 seconds, to 7 seconds | Enough time to comprehend arbitrary text within that range |
| Netflix Japanese translated subtitles, Section I | A language-specific minimum of 0.5 seconds | An appropriate duration for every short Japanese cue |

For its line-length limits, Netflix counts full-width characters, spaces, and punctuation as one unit and half-width equivalents as half a unit. Do not assume every character-rate measure uses that same definition. The Japanese minimum above applies specifically to Section I. [5](https://partnerhelp.netflixstudios.com/hc/en-us/articles/215767517-Japanese-Timed-Text-Style-Guide) [6](https://partnerhelp.netflixstudios.com/hc/en-us/articles/215758617-Timed-Text-Style-Guide-General-Requirements)

English word-per-minute limits are not directly interchangeable with Japanese character rates. DCMP’s educational guidance uses words per minute and counts speaker identification and sound descriptions as part of the load. Its school-level categories are not Japanese proficiency levels. [9](https://dcmp.org/learn/captioningkey/601)

Do not reduce reading difficulty to a character total. Familiar phrases, unusual names, dense kanji, unfamiliar contractions, changes of speaker, and competing visual action can make equally long cues very different tasks. Any counting convention must also distinguish what a layout limit measures from what the viewer actually has to process.

### 4.3 Different situations need different judgment

| Situation | General craft concern | Application to yomisub |
| --- | --- | --- |
| A familiar short response | Avoid a distracting flash, but keep the turn clear | Give it a coherent presentation within the actual exchange. |
| Slow speech with a long pause | Avoid revealing the delayed ending | Respect the audible pause; keep later words from appearing too early. |
| Dense rapid speech | Full reading may be impossible at original pace | Preserve the words and synchronization; do not build delay. |
| Unfamiliar name or technical expression | Decoding may take longer than length suggests | Verify spelling and use a consistent orthography policy; avoid artificial retiming. |
| Two people speaking together | Both lines compete for the same attention | Judge their combined load and preserve their separate timing. |
| A critical action or on-screen message | The subtitle competes with the picture | Requires human review or external visual information; the audio-only process uses fixed placement. |
| A genuine quiet interval after speech | Some professional profiles use additional exposure | Prefer clearing with the phrase; silence alone does not require an extension. |
| Paused or repeated study | Available reading time changes | Additional study time can be provided by the viewing situation, without changing the original speech relationship. |

The sources reviewed do not establish a universal N4/N5 subtitle speed. Here, a threshold identifies demanding cues; it does not prescribe their timing.

## 5 Multiple speakers and their visual presentation

The best starting point is to separate three questions:

1. Who produced each utterance?
2. Did their utterances alternate, overlap, or interrupt one another?
3. What visual arrangement makes that relationship clear without requiring the viewer to learn a complicated notation?

Speaker identification and timing are independent. A correct name attached to a late line is still misleading. Conversely, perfectly synchronized text can remain confusing if the viewer cannot tell whose words it contains.

### 5.1 A practical default for yomisub

Use one speaker at a time for ordinary alternating turns. For two overlapping, intelligible voices, use two clearly distinguished lines when the text fits, with one speaker per line. Netflix’s Japanese SDH guide also uses one speaker per line in dual-speaker cues; the exact punctuation is its house style. [5](https://partnerhelp.netflixstudios.com/hc/en-us/articles/215767517-Japanese-Timed-Text-Style-Guide)

Use stable, fixed screen positions for this audio-only workflow. Where names have not been verified, distinguish voices with neutral labels grounded in the audio. Mentioning someone’s name in dialogue does not establish the identity of the person speaking.

For yomisub, add these editorial commitments:

- Make each speaker’s text available when that speaker begins the relevant phrase.
- Keep the association between a person and their displayed line stable during the overlap.
- Keep each speaker’s current phrase visible during its speech interval, including overlap; advance their text as their speech continues.
- Avoid displaying a later reply early merely to assemble a convenient two-line block.
- Avoid postponing an interruption until after the interrupted person has finished.
- Count both lines, including labels, as one combined visual demand. Two voices do not give the viewer two independent reading capacities.

This is a useful default, not a universal command to squeeze every conversation into two lines. A single speaker may legitimately need two lines. If another enters then, the available presentation space becomes a real editorial constraint.

### 5.2 Ordinary alternating dialogue

Assume Aki and Yui have already been introduced. They are arranging a meeting.

**First turn, while Aki speaks:**

```text
（アキ）駅で待ってる。
```

Gloss: “I’ll be waiting at the station.” The future meaning and “I” come from this context; the same Japanese can mean “I’m waiting at the station” in another scene.

**Next turn, when Yui responds:**

```text
（ユイ）どの駅？
```

Gloss: “Which station?”

If the turns do not overlap, separate presentations make their order clear. Showing both from Aki’s first word makes Yui’s question available before Yui asks it. Labels do not repair that premature reveal.

The labels in these illustrations are deliberately explicit so the relationship is easy to see. They are not a requirement to repeat every name in every ordinary cue.

### 5.3 The same words with actual overlap

Now suppose Yui begins the question before Aki finishes. At the overlapping moment, the display can be:

```text
（アキ）駅で待ってる。
（ユイ）どの駅？
```

The display should develop with the exchange. The following times are invented solely to illustrate that relationship:

| Moment | Audible event | Appropriate visible state |
| --- | --- | --- |
| 0.0 seconds | Aki starts the phrase | Aki’s line appears. |
| 0.9 seconds | Yui starts while Aki continues | Yui’s line appears separately; Aki’s remains. |
| 1.4 seconds | Aki finishes; Yui continues | Aki’s line can clear; Yui’s remains associated with Yui. |
| 1.8 seconds | Yui finishes | Yui’s line clears with the end of the exchange. |

Avoid making the remaining line jump unnecessarily when the other disappears. Stable placement is an editorial preference here because it preserves the viewer’s point of reference; it is not a claim that every professional caption system behaves this way.

The first phrase is presented as a phrase, not revealed character by character. That small amount of within-phrase anticipation is different from showing a second person’s entire answer before their turn begins.

### 5.4 Interruptions carry information

An interruption can express disagreement, urgency, impatience, familiarity, or cooperation. Its temporal relationship is part of the interaction.

```text
（アキ）明日は…
（ユイ）無理！
```

Gloss: Aki begins “Tomorrow…”; Yui cuts in with “No way!” or “I can’t!” The correct English interpretation of the short reply depends on context.

If Yui interrupts, do not present the exchange as though Aki calmly completed a turn and then received a response. Preserve the interrupted fragment instead of supplying a sentence the speaker never finished. A visual mark can suggest incompleteness, but actual onset timing establishes the interruption.

A dash, ellipsis, or other continuation mark needs a consistent editorial meaning. If the same mark sometimes means an audible pause, sometimes missing words, and sometimes a change of speaker, the learner must solve an unnecessary puzzle.

### 5.5 Labels, color, and placement

| Method | Useful contribution | Limitation to account for |
| --- | --- | --- |
| A verified name, role, or neutral voice label | Explicit attribution independent of camera position | Adds text; an unverified name or role can mislead or spoil a reveal. |
| One speaker per line during overlap | Separates concurrent utterances at a glance | Longer turns may not fit one line. |
| Consistent color | Can reinforce speaker distinctions without repeated long labels | Should not be the only way to distinguish people; many colors become hard to remember. |
| Position related to the speaker | Can make the association intuitive in a stable scene | Requires picture information; unsuitable as an automatic audio-only rule. |
| A change of cue | Makes alternating turns clear | Cannot by itself explain simultaneous voices. |

For yomisub, favor explicit attribution where the audio indicates distinct speakers, supported by stable positions. Neutral labels such as **話者１** (“Speaker 1”) and **話者２** (“Speaker 2”) avoid unsupported identities. Keep an assignment only where the audio supports continuity of the voice; uncertain assignments should remain uncertain.

Treat color as supplementary. W3C’s general accessibility principle is to provide another visible means of conveying information communicated by color. Choose text and backing that remain clear on varied backgrounds rather than relying on a color looking clear in a particular shot. [22](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html)

Stable, labeled positions can remain attached to the same speakers during an exchange even if the camera reverses. Following people around the picture, or moving captions away from a face or sign, needs visual information and belongs to a separate review process. Fixed placement cannot guarantee that it avoids all pictured content, but it provides a consistent convention without inventing that information.

DCMP advises identifying speakers using information available to the audience and withholding names until they have been introduced. Japanese professional guidance likewise warns that script-based labels can spoil revelations and that inconsistent labeling can create confusion. [10](https://dcmp.org/learn/603-captioning-key---speaker-identification) [12](https://www.okosuke.jp/seisaku)

This suggests a simple rule: **use the least elaborate label that resolves a real ambiguity without inventing knowledge**. Descriptions such as “phone voice” or “shopkeeper” need supporting evidence too. Use a neutral voice label when that evidence is absent. Professional decisions to omit a label because the speaker is visibly obvious require picture information; the audio-only process cannot make that judgment. The named examples above assume verified identities for illustration.

### 5.6 Backchannels are not all disposable

Japanese listeners often produce short responses during another person’s speech. Consider **うん**, which can mean “yeah” or “uh-huh.” Depending on context, it can acknowledge hearing rather than promise agreement. It is different from **うーん**, which can convey thinking, hesitation, or doubt.

For yomisub, preserve a backchannel when it is an identifiable part of the exchange, particularly when it changes the interpretation or is something the learner can hear and match. Do not automatically turn every small vocal event into a separate flashing cue. A brief overlap can be represented within a stable arrangement.

If a production chooses to omit incidental listener sounds, that is an editorial completeness policy. It should not silently emerge from a rule that deletes every short utterance or every secondary speaker.

### 5.7 Three or more voices

There is no lossless way to place three substantial simultaneous utterances into two short, easily read lines. The conflict is real even when recognition is perfect.

| Situation | Suitable editorial reasoning |
| --- | --- |
| Several people say the same words together | A collective attribution may convey the event without duplicating identical text. |
| A clear exchange sits over indistinct crowd chatter | Preserve the intelligible exchange; describe the audible crowd if the chosen caption profile includes such sounds. |
| Two sustained voices overlap with a brief intelligible third reaction | Preserve the reaction and its timing; review the denser arrangement as an exception. |
| Three independent, intelligible streams overlap | A fuller labeled presentation adds clutter; selective transcription loses content. Make that tradeoff explicit. |
| The overlapping speech is genuinely unrecoverable | Indicate the uncertainty or overlapping voices when relevant; do not invent words. |

For this project, a two-line preference should not become an automatic excuse to drop intelligible speech. Neither should a generic “voices overlap” label replace words that are clearly recoverable merely because they are inconvenient to display. Audio prominence does not establish narrative importance: there is no universal plot-priority rule that can be applied from audio alone. If a crowded exchange requires selection, disclose that limitation rather than claiming the omitted voices were unimportant. Its timing must still represent simultaneity honestly.

## 6 Dividing Japanese into useful units

Subtitle segmentation operates at two levels. A **line break** changes the layout while both parts remain visible. A **cue boundary** can make the earlier part disappear. A division that is tolerable within one visible block can be much harder across two separate moments.

### 6.1 Preserve relationships within the language

Useful candidates for boundaries include complete short utterances, clauses, topic phrases, and meaningful pauses. Prefer boundaries that let the reader retain a coherent piece of meaning. Japanese does not normally put spaces between words, so a simple count of characters cannot tell you where such a boundary belongs.

General Japanese typography permits many character-based line breaks, with restrictions on punctuation and certain character sequences. Those rules establish typographic possibilities, not the best place to divide a fleeting subtitle. W3C’s Japanese layout guidance describes these restrictions; an editor must additionally consider the phrase and its timing. [13](https://www.w3.org/TR/jlreq/?lang=en)

When possible, keep together:

- A short noun phrase and its associated particle.
- A name, fixed expression, or tightly connected compound.
- A number and the unit or counter that gives it meaning.
- A verb and its negation, tense, or modal ending.
- A grammatical construction the learner needs to recognize as a unit.

These are preferences to apply with judgment, not a demand that every long construction remain on one line. Avoid a grammatically beautiful block so long that it exposes an entire future speech turn.

### 6.2 Meaning can outweigh visual symmetry

Consider:

```text
明日の会議には
出られないかもしれません。
```

Gloss: “I might not be able to attend tomorrow’s meeting.” The first line supplies the topic; the second keeps inability and uncertainty together. The lines need not have identical lengths.

A poor division would split **かもしれません**—the expression contributing “might”—into fragments merely to balance line widths. Japanese professional guidance explicitly favors clarity of meaning over perfectly balanced line lengths. [12](https://www.okosuke.jp/seisaku)

Another example is **それはできない。**, “I can’t do that.” Breaking it as **それはでき / ない。** separates the verb stem from its negative ending. The first fragment is not a complete affirmative sentence; the problem is that the reader must reconstruct a tightly connected predicate across the break.

### 6.3 Respect what has actually been revealed

Japanese utterances can leave decisive information until an ending: a negative, a question, a condition, or an expression of uncertainty. This creates two competing risks. Splitting a construction too early can make its interpretation awkward; displaying the whole ending well in advance can spoil its delivery.

Use the audible performance as evidence. If a phrase is spoken continuously, keeping its construction together is usually helpful. If the speaker pauses before a reversal, preserve the pause without assuming why it occurs. Do not show the delayed conclusion immediately merely to complete the written sentence.

### 6.4 Avoid both tiny fragments and oversized blocks

A stream of one-word cues repeatedly asks the viewer to find new text. A giant block asks the viewer to locate the current phrase within too much text. For yomisub, aim for stable, coherent pieces of the ongoing speech.

Research on English subtitle segmentation found that poor syntactic grouping could increase reported processing effort without reducing comprehension-test scores. That supports reviewing comfort as well as eventual comprehension; it does not establish a Japanese line-break formula. [19](https://pmc.ncbi.nlm.nih.gov/articles/PMC7901653/)

Good segmentation is therefore a form of editorial help that can preserve the original words and timing. It is especially valuable here because the project deliberately does not solve difficulty through compulsory slowing or paraphrase.

## 7 Preserving the Japanese that was spoken

Speech has false starts, contractions, unfinished thoughts, repeated words, and context-dependent responses. The editor must decide which of these are part of what the viewer needs to follow. “Clean up the transcript” is too vague a policy: it can mean correcting an error, removing an empty hesitation, changing a character’s register, or rewriting the entire sentence.

### 7.1 Distinguish correction from rewriting

| Editorial action | Example of its purpose | Fit with yomisub’s brief |
| --- | --- | --- |
| Correct transcription | Restore an audible negative that was misheard | Essential accuracy work |
| Choose conventional spelling | Write the spoken word with an appropriate kanji or kana form | Necessary, provided the spelling is verified |
| Lightly edit disfluency | Omit a hesitation that contributes nothing relevant | A contextual judgment, not an automatic deletion rule |
| Condense | Remove repetition or parts of a sentence to lower text load | May damage correspondence; not justified by speed alone here |
| Paraphrase into easier Japanese | Replace an unfamiliar expression with a simpler construction | A different teaching purpose; should not masquerade as the spoken wording |

Conventional transcription is not a phonetic record of every sound. For example, the topic particle pronounced *wa* is normally written **は**. Using that spelling does not change the utterance. Replacing a contracted expression with a more formal sentence does.

### 7.2 Contractions are learning material

```text
もう食べちゃった。
```

Gloss: “I already ate it,” in a suitable context. **ちゃった** is the contracted form of **てしまった** here. The longer **もう食べてしまった。** is useful as an explanation, but it is not the same sequence of spoken sounds. Depending on context, the construction can express completion, unintended action, or regret; regret is not compulsory.

Likewise, **何してるの？** means “What are you doing?” in an ordinary context. Replacing it with **何をしているのですか？** expands the wording and changes the register. A learner trying to follow the first utterance should not have to reconcile it with the second.

The Japan Foundation explicitly treats colloquial contractions and honorific expressions as useful learning targets in video-based teaching. Preserving such forms in learner subtitles follows from that purpose; it is not a claim that one spelling policy has been experimentally proved best. [14](https://www.jpf.go.jp/j/project/japanese/teach/tsushin/hint/201301.html)

### 7.3 Preserve corrections and uncertainty

```text
明日、いや、あさっての３時ね。
```

Gloss: “Tomorrow—no, the day after tomorrow, at three, okay?” The speaker corrects the date. A condensed **あさっての３時ね。** preserves the final appointment but removes the self-correction the learner heard. It may also remove something about the character’s state of mind.

If the correction follows a meaningful pause, its timing matters as well. Do not show the final date at the beginning merely because it is the eventually correct information.

Similarly, **行けたら行く。** means “I’ll go if I can.” Reducing it to **行く。**, “I’ll go,” removes the condition. The original can be sincere or noncommittal depending on context; a subtitle should not resolve that ambiguity into a definite promise or refusal without evidence.

Small elements can matter greatly. A negative ending, question ending, hedge, or sentence-final particle may occupy little space while doing much of the interpersonal work. Do not rank importance by character count.

### 7.4 Fast speech under this brief

When a speaker is very fast, first establish that the wording is accurate and divided into useful units. Remove duplication caused by transcription errors. Improve line breaks. Make attribution clear. Keep the text connected to its actual speech interval.

If the resulting subtitles are still too fast to finish, that is an accepted tradeoff for yomisub. Do not compensate by letting later cues accumulate behind the audio, merging unrelated turns, or replacing the sentence with a smoother summary. A viewer may choose to pause, replay, or change viewing pace, but those choices do not excuse incorrect original timing.

An ordinary professional subtitler working under a different brief may choose condensation. When that happens, preserve crucial propositions and relations: who did what, to whom, whether it happened, and with what certainty or condition. Preserve characterization and emotional intent as well. A shortened text that reverses one of those relations has failed, even if it meets every length limit.

## 8 Japanese writing choices and reading assistance

Spoken language does not uniquely determine its written form. Subtitling includes choices about kanji, kana, names, punctuation, and annotations. Those choices affect recognition as well as appearance.

### 8.1 Mixed script, kana, and furigana solve different problems

| Presentation | What it can help with | Tradeoff |
| --- | --- | --- |
| Ordinary kanji and kana | Shows conventional written forms and distinctions between words | Unfamiliar kanji can block recognition. |
| Kana-focused wording | Makes the pronunciation available to someone who knows kana | Can be longer and can remove distinctions supplied by kanji. |
| Kanji with furigana | Associates a written form with a reading | Adds material to inspect; knowing the reading does not guarantee knowing the meaning. |
| Romanization | Makes a pronunciation accessible before kana is secure | Changes the written learning task and is outside the main Japanese-script brief. |

The Japan Foundation’s *Activate Your Japanese!* material offers both kanji-based and hiragana/katakana Japanese captions. This is useful evidence that orthography can be an audience choice, rather than a reason to declare one version universally superior. [15](https://www.hikidasu.jpf.go.jp/jp/about/)

For yomisub, a defensible starting point is faithful Japanese in consistent conventional spelling, with reading assistance treated as a separate editorial choice. The viewer’s N4/N5 description informs that choice but does not specify every word or kanji they know.

### 8.2 Furigana supplies a reading

Take **明日**. Depending on the utterance, its reading might be **あした** or **あす**. If reading annotations are supplied, they should correspond to the actual speech, not merely to a valid dictionary reading. Names and place names require particular care.

Furigana can help a viewer connect a familiar spoken word to an unfamiliar written form. It cannot by itself explain an unknown word, an idiom, or the grammatical relationship between clauses. Nor should its visual cost be assumed to be either always harmful or always negligible.

A 2024 lexical-decision study found different effects of furigana for Japanese learners with and without kanji backgrounds. That is evidence that literacy background matters. It was not a subtitle-viewing experiment and does not establish an ideal density of furigana or an extra number of display seconds. [18](https://bunkyo.repo.nii.ac.jp/records/2000111)

Useful editorial questions are: Does the viewer need help with this word’s reading? Is the annotation accurate for the performance? Is the word’s meaning still unknown afterward? Does the annotation compete with other essential text? Answers can vary across viewers and scenes.

### 8.3 Verify written distinctions

For instance, **橋** means “bridge” and **箸** means “chopsticks”; both can be represented by the kana **はし**. Context helps determine which written word is intended. A plausible kanji substitution can produce clean-looking but incorrect Japanese.

Use contextual evidence to establish names and terminology, and keep them consistent throughout the work. Do not manufacture a character’s official name spelling from pronunciation alone. Also preserve purposeful differences: a nickname and a formal name may both be correct, and the choice between them can express a relationship.

Dialect and character speech deserve similar respect. A nonstandard expression is not necessarily a recognition mistake. Regularizing everyone into formal textbook Japanese would erase part of what the learner is watching and hearing.

### 8.4 Choose a punctuation policy for its purpose

Japanese subtitle services do not all use ordinary prose punctuation in the same way. Some replace familiar stops and commas with spacing. Do not assume that a convention inherited from translated cinema subtitles is automatically the best teaching choice.

For this document’s examples, ordinary punctuation makes the English explanation and Japanese sentence easier to compare. Yomisub’s eventual policy should be consistent and should clarify questions, interruptions, and continuation without clutter. Punctuation should reflect the utterance; adding a question mark to an uncertain recognition result does not make the uncertainty honest.

Apply Japanese line-start and line-end conventions as well. Avoid leaving an opening bracket stranded at the end of a line or closing punctuation detached at the next line’s start. Then apply the additional semantic grouping described earlier. [13](https://www.w3.org/TR/jlreq/?lang=en)

## 9 Sounds and information beyond dialogue

A useful subtitle may need to identify a knocking sound, distinguish a television voice from a conversation, or indicate who is laughing. Some of these distinctions are audible; others need visual or contextual evidence. A sound description should stay within what is actually established.

Accessibility captions should convey meaningful non-speech information. For yomisub’s hearing learner audience, decide how much of that information needs written support. Some sounds are already obvious; some are difficult to identify or easy to confuse with speech. Avoid turning the display into a running description of every noise.

### 9.1 Describe the relevant event

```text
（ドアをたたく音）
```

Gloss: “Knocking at the door.” This is an editorial description, not dialogue someone spoke. Its presentation should make that difference clear, and it should appear when the sound occurs.

PEPNet-Japan’s educational accessibility guidance recommends considering what produced the sound rather than simply spelling an imitative noise. A learner may recognize the event more readily from a clear description than from an unfamiliar onomatopoeic form. [23](https://www.pepnet-j.org/contents/archives/1923)

An onomatopoeic expression can still be appropriate when its particular sound or linguistic character matters. The choice is about what information the viewer needs, not a prohibition on Japanese sound symbolism.

### 9.2 Do not turn interpretation into an asserted fact

“Laughing” describes an audible event. “Laughing because she secretly knows the answer” explains a motive. The latter adds a conclusion that may not be established. Similarly, “sarcastically” can be useful when delivery is crucial and well supported, but should not be a convenient substitute for understanding the scene.

Preserve uncertainty and narrative point of view. An unidentified off-screen sound should not name a hidden cause before the work reveals it. Speaker descriptions and sound descriptions can spoil a story just as early dialogue can.

### 9.3 Music and lyrics require an explicit scope

Distinguish background instrumental music, intelligible lyrics, and characters singing. Dialogue and lyrics can occur at the same time and compete for space. Decide whether the task is to follow the main conversation, study the song, or provide full accessibility information.

Meaningful changes in music may merit a description, especially in an accessibility version. Lyrics that explain the story are different from a barely audible background song. Do not present guessed lyrics as verified text, and do not let incidental lyrics displace a current dialogue line simply because they were easier to recognize.

### 9.4 Existing on-screen Japanese is another source of text

Signs, messages, title cards, and television graphics can be important to the scene. They can also compete with subtitles. Avoid covering an important message or a speaker’s face. DCMP’s text guidance treats placement, logical line division, and access to significant visual information as parts of caption presentation. [11](https://dcmp.org/learn/597-captioning-key---text)

Japanese television often includes editorial on-screen text. Treat any such text as evidence of what the programme displays, not automatic proof of the exact words spoken: it may emphasize, summarize, or comment on the dialogue. A learner may otherwise mistake a graphic’s rewording for a transcript.

These visual concerns require human inspection or separately supplied information. They remain relevant craft knowledge even though yomisub’s audio-only process cannot identify or avoid every collision with existing screen text.

## 10 Accuracy and uncertainty before presentation

Speech recognition supplies a candidate transcription. It does not decide whether a line is narratively important, which person spoke it, whether a spelling is appropriate, or how a learner will connect it to the scene. W3C cautions that automatic captions require accuracy review and gives missing negation as an example of an error that can reverse meaning. [2](https://www.w3.org/WAI/media/av/captions/)

The relevant distinction is between **what the recording supports** and **what the editor infers**. Context can resolve a word or name, but plausibility alone is not evidence that it was spoken.

| Uncertainty | Appropriate editorial response |
| --- | --- |
| The word is audible but its spelling is unclear | Verify the written form using reliable context. |
| One short portion is masked | Preserve the recoverable material and localize the uncertainty. |
| The identity of an audible speaker is uncertain | Avoid a confident name; use an honest attribution if needed. |
| A character deliberately speaks indistinctly | Preserve the intended lack of clarity where it matters. |
| The recording contains no recoverable words | Do not manufacture a plausible line to fill the gap. |
| The written transcript and recorded performance disagree | Establish what is actually present in the version being viewed. |

A script can help verify spelling while still differing from the final performance. A translation can help explain a scene while failing to identify the exact Japanese. An official-looking subtitle can contain condensation. Each is a useful source with a different evidential role.

Errors deserve attention according to their consequences. Confusing a person, a date, a number, a condition, or a negative can change the scene. Removing an audible correction can teach the wrong relationship between text and sound. Conversely, reproducing every tiny hesitation perfectly does not compensate for a line assigned to the wrong speaker.

For an N4/N5 learner, fluent-looking wrong Japanese may be especially hard to question. Editorial honesty about an unresolved fragment is preferable to a confident invention. The unresolved area should be as narrow as the evidence allows; uncertainty about one word is not a reason to discard an otherwise recoverable exchange.

## 11 Applying the craft with audio and text alone

The professional craft described above often assumes a human editor who can watch the programme. Yomisub’s stated automatic workflow has a narrower view: audio, recognized text, and possibly a small amount of nearby dialogue supplied to a local language model. It does not see the picture or understand the whole plot. That changes which judgments it can responsibly make.

The distinction below is an analysis of the evidence each task requires. It is not a claim that any particular recognition system already supplies that evidence accurately.

| Editorial question | Evidence needed | Appropriate scope for an audio/text-only system |
| --- | --- | --- |
| What words were spoken, and when? | The recording and reliable alignment of words or phrases to it | Establish and preserve the audio relationship; a plausible sentence alone cannot supply timings. |
| Did two people speak together? | Overlapping audible speech and reliable separation of speakers | Represent verified overlap; two neighboring transcript lines do not prove simultaneity. |
| Which utterances belong to the same voice? | Acoustic evidence across the exchange | Use consistent neutral labels where supported; retain uncertainty when attribution is weak. |
| What is that person’s name? | An established identity linked to the voice | Use a verified mapping or keep a neutral label. A voice distinction does not establish a character name. |
| Where should a Japanese phrase be divided? | The wording, its grammar, and the performance | Language judgment can suggest good boundaries; audio determines whether a timed division is possible there. |
| What does this spelling or reading mean here? | Nearby dialogue, the sound, and sometimes a verified glossary | Make a constrained proposal; abstain when multiple interpretations remain possible. |
| Will the subtitle cover a face, sign, or existing caption? | Video frames | Use a consistent default placement; collision avoidance cannot be guaranteed without visual evidence. |
| Is this an off-screen speaker, narrator, phone voice, or inner thought? | Sometimes audio cues; often the picture and wider context | Assert only what the available evidence supports. Do not infer a category solely because a line sounds unusual. |
| Which competing line is most important to the plot? | Wider narrative understanding | Do not use guessed importance to discard intelligible speech. |
| Does a label reveal a hidden identity? | What the audience has been told so far | Neutral attribution avoids an invented identity; plot-aware labeling needs additional review. |

**Speaker diarization** means determining which portions of speech belong to which speaker. Identifying that speaker as a named fictional person is another judgment. Keeping a voice label consistent also becomes uncertain when voices are similar, speech overlaps, or a performance changes markedly. A label should communicate the strength of the available evidence, rather than make the display look more certain than the audio analysis is.

For this project, favor a stable subtitle area, clear textual attribution during ambiguity or overlap, and consistent treatment of unresolved speech. A neutral label such as “Speaker A” can communicate an audio distinction without pretending to know a character. The actual label language is an audience choice. Do not infer screen position, appearance, gender, or story role simply to make labels more descriptive.

This leaves some professional judgments unresolved. A fixed subtitle area may still cover an important image. A line may be a joke or a revelation that the software cannot recognize. Preserve timing and avoid displaying future turns early as general protections; describe the remaining visual and narrative limits honestly. Human review can supply missing evidence when available, but the automatic output should not be described as fully reviewed merely because it follows a style guide’s measurable rules.

## 12 What the research supports

Research supports using captions to help people understand spoken material, but results depend on the viewers, language, content, and task. **Understanding a scene while captions are present is different from developing the ability to understand speech later without them.** A comprehension score, a vocabulary test, and a viewer’s preference answer different questions.

**Complete wording can be useful assistance.** In a study of 226 university students learning French, full captions produced better global comprehension than keyword captions or no captions. Keyword captions did not outperform no captions, and detailed questions accompanied by audio showed no difference between groups. This challenges the assumption that displaying fewer words necessarily makes a scene easier. It does not prove that every utterance must always be shown verbatim, or that the same result holds for Japanese learners. [16](https://doi.org/10.1017/S0958344013000256)

**Japanese learner evidence is encouraging but limited.** A study involving 34 learners of Japanese at a Japanese university compared videos with and without subtitles. Its abstract reports an overall comprehension benefit, with individual exceptions. That supports the purpose of caption assistance, but does not establish an N4/N5 timing target or demonstrate lasting listening improvement. A separate survey of 527 Chinese learners of Japanese found that subtitle choices related to learners’ interests and goals; those preferences are not an experimental measure of effectiveness. [17](https://www.kci.go.kr/kciportal/landing/article.kci?arti_id=ART001530093) [21](https://www.jstage.jst.go.jp/article/gbkkg/20/0/20_335/_article/-char/en)

**Four characters per second is not a universal reading limit.** In a small Japanese translated-film study, ten graduate students viewed versions prepared at four, six, and eight characters per second; most preferred six. This questions treating a convention as an absolute human limit. It does not establish six as optimal for everyone, and it did not test yomisub’s learner audience. [20](https://www.jstage.jst.go.jp/article/its/17/0/17_1708/_article/-char/en)

**Furigana research does not settle subtitle design.** The word-recognition evidence discussed in Section 8 concerns a different task from following a timed scene. It cannot establish ideal annotation density or extra display time. Helping someone pronounce a word also does not ensure that they know its meaning. [18](https://bunkyo.repo.nii.ac.jp/records/2000111)

For yomisub, preserve the chosen audio–text relationship, then assess whether the captions help the intended learner follow the exchange, identify the spoken wording, and keep track of the picture. Any claim about later learning needs evidence that measures later learning.

## 13 A brief for future development agents

Read this section as the editorial contract for yomisub. It records the user’s priorities and the synthesis in this document; it is not an industry standard or an implementation specification.

### 13.1 Preserve these distinctions

| Distinction | Why it matters |
| --- | --- |
| Recognition accuracy versus timing accuracy | Correct words can still accompany the wrong sound. Fixing spelling does not fix timing. |
| Fast speech versus delayed subtitles | High reading demand can be acceptable; a growing backlog is a different defect. |
| Line break versus cue boundary | A layout change leaves both parts available; a timed boundary may remove the first part. |
| Alternating turns versus simultaneous speech | Sequential presentation can falsely transform an interruption into a polite exchange. |
| Voice identity versus character identity | Audio can distinguish speakers without establishing their names. |
| Correcting recognition versus simplifying language | The former restores the performance; the latter can replace what the learner is trying to hear. |
| Reading pronunciation versus understanding meaning | Furigana can help with one while leaving the other unresolved. |
| House rule versus evidence about learners | A delivery specification is not a measured limit on human comprehension. |

### 13.2 Judge representative scenes, not just averages

A useful review set contains ordinary conversation, very fast speech, an interruption, two overlapping voices, a brief acknowledgment, a long meaningful pause, a sentence with a late negative or condition, uncertain speech, names, and lyrics competing with dialogue. Include quiet and visually busy scenes when human video review is possible.

Review in continuous playback before judging individual still frames. Ask whether the displayed phrase belongs to the current speech, whether the speaker is clear, and whether a line appears or disappears at a misleading moment. Then inspect the words and grouping. An average reading rate can hide a few severe failures that make an otherwise usable episode confusing.

When comparing editorial choices, keep the question narrow. Compare two line breaks with the same words and timing, or two overlap layouts with the same audio. Changing wording, timing, labels, and typography together makes it difficult to learn which decision helped. Separate perceived comfort, comprehension of the scene, recognition of the spoken Japanese, and later learning.

### 13.3 Default decisions for this brief

1. Preserve the audible Japanese, including meaningful contractions, corrections, uncertainty, and register.
2. Keep phrases close to their actual speech intervals. Do not accumulate delay to achieve a target reading speed.
3. Divide at useful linguistic and performed boundaries. Avoid both flashing fragments and oversized blocks.
4. Show overlapping speech as overlapping, with clear attribution and stable placement where possible.
5. Treat two lines as a presentation preference whose exceptions need judgment, rather than permission to lose speech silently.
6. Apply consistent spelling and punctuation, and verify annotations against the actual utterance.
7. Keep uncertain words and uncertain identities visibly unresolved to the extent necessary.
8. Reserve plot, visual-position, and obstruction judgments for evidence that can support them.

## 14 Focused appendix: small local language models

This appendix answers the additional hardware question. It assumes the reported working environment: an AMD Radeon RX 9060 XT with 16 GB of VRAM, Debian 13, ROCm, and Ollama. It concerns short text judgments around subtitle lines. The main document remains about editorial craft.

### 14.1 Give a model a narrow editorial question

A useful role is to make a bounded language judgment from supplied text. A short instruction with a few relevant neighboring lines is easier to inspect than a request to “make these subtitles good” or “make this Netflix compliant.” A model’s fluent response supplies a proposal, not evidence of what happened in the recording.

| Task related to the guide’s concerns | Suitable local-model contribution | Boundary to preserve |
| --- | --- | --- |
| Linguistic line division | Choose among supplied break candidates or flag a broken grammatical unit | Keep the words unchanged; proposed divisions must still fit the speech. |
| Faithfulness to the original | Compare two supplied versions for lost negation, conditions, corrections, or changes of register | A text comparison cannot establish which version was actually spoken. |
| Spelling consistency | Flag disagreement with a small verified name/term list | Do not invent a name spelling or erase a meaningful nickname. |
| Reading annotations | Propose a kana reading using the line and verified context | Ambiguous readings and names need an unresolved option and audio verification. |
| Suspicious transcription | Point out a specific span worth checking against the recording | Colloquial speech and dialect are allowed; grammatical oddity is not proof of an ASR error. |
| Supplied speaker labels | Flag inconsistent use of known labels in a small excerpt | Do not recover voices, overlap, or named identities from text alone. |
| Fixed presentation limits | No language judgment is needed for exact character counts or duration arithmetic | Use an explicit counting convention; arithmetic is not editorial understanding. |
| Timing, placement, and plot-dependent selection | Explain a supplied conflict or flag missing evidence | Do not invent timestamps, visual obstructions, or narrative priorities. |

These are proposed uses for evaluation, not Netflix-endorsed automation methods. Their reliability on yomisub’s material remains to be measured.

### 14.2 A short list for 16 GB

Start with **Qwen3.5 4B in Q4_K_M** for a simple candidate-selection or flagging task. If its errors are consequential, compare the 9B version on exactly the same examples. Keep Gemma 4 12B as an optional comparison from a different model family. There is no need to run all three together.

| Candidate and exact catalog tag | Published package size | Suggested role |
| --- | --- | --- |
| **Qwen3.5 4B**, `qwen3.5:4b-q4_K_M` | **3.3 GB** | First baseline for choosing line breaks and applying one short language rule. [24](https://ollama.com/library/qwen3.5:4b-q4_K_M) |
| **Qwen3.5 9B**, `qwen3.5:9b-q4_K_M` | **6.6 GB** | Compare when the 4B model mishandles context, contractions, or meaning-preservation judgments. [25](https://ollama.com/library/qwen3.5:9b-q4_K_M) |
| **Gemma 4 12B IT**, `gemma4:12b-it-q4_K_M` | **8.0 GB** | Optional independent comparison for the same short review questions. [26](https://ollama.com/library/gemma4:12b-it-q4_K_M) |

The exact tags identify quantized packages; a similarly named full-precision version has a different memory requirement. These recommendations are an assessment of practical fit and task scope, not a benchmark ranking of Japanese subtitle editors. Qwen lists Japanese among its supported languages; that makes it a plausible candidate, without proving correctness on these particular tasks. [29](https://qwen.ai/blog?id=qwen3.5)

For initial evaluation, use **one model, one request at a time, text only, and a context of about 4,096 tokens**, including room for the answer. These three packages leave a plausible margin for fully GPU-resident use on 16 GB at that modest context. This is an estimate from published sizes, not a measurement on the user’s card. Ollama documents a 4K default context for systems below 24 GiB VRAM and notes that longer contexts require more memory. [27](https://docs.ollama.com/context-length)

Package size is not peak VRAM use. The working budget also includes context storage, runtime working memory, and other GPU users, including the desktop and any simultaneous audio model. Parallel requests can increase context-memory allocation. Successful generation alone also does not prove that a model stayed entirely on the GPU: Ollama distinguishes full GPU loading from CPU/GPU splits. [28](https://docs.ollama.com/faq)

Accordingly, assess residency and responsiveness with the actual short workload before choosing a model. Do not interpret an advertised maximum context window as a promise that the full window fits this card. No tokens-per-second or whole-episode processing time is asserted here.

### 14.3 Keep prompts small and reviewable

For simple selections, begin with a direct, short answer; where available, use the model’s supported non-thinking mode. Both model families document a way to disable extended thinking. More deliberation is a separate option to compare on difficult examples, rather than a requirement for every line. [30](https://huggingface.co/Qwen/Qwen3.5-4B) [31](https://huggingface.co/google/gemma-4-12B-it)

**Example: choose a line break.**

> Choose the better line division for the Japanese below. Keep all characters unchanged. Prefer coherent phrases; keep the negative and modal ending together. Return A, B, or neither, with one short reason. Do not propose timing.
>
> A: 明日の会議には / 出られないかもしれません。
>
> B: 明日の会議には出られないかも / しれません。

The slash marks a candidate line break, not spoken punctuation. Both candidates mean “I might not be able to attend tomorrow’s meeting.” A keeps **かもしれません** together; the task is deliberately easy enough to inspect.

**Example: flag an issue without rewriting.**

> Review this Japanese transcript excerpt for a possible recognition mistake. Colloquial contractions, hesitation, repetition, dialect, and unfinished sentences are allowed. If a specific span needs checking, quote only that span and explain the concern in one sentence. Otherwise answer “no concern.” Do not correct the transcript or claim to know the audio.

This prompt can generate false alarms. Evaluate whether its flags actually help someone review the recording; do not treat every flag as an error.

**Example: protect a conditional.**

> Original: 行けたら行く。
>
> Proposed edit: 行く。
>
> Has the proposed edit removed a condition, negation, uncertainty, or change of speaker? Answer with the affected category and a short explanation, or “none.” Do not rewrite either version.

Gloss: “I’ll go if I can” versus “I’ll go.” This is a comparison of supplied texts. It does not decide which version the recording contains.

### 14.4 Select by consequential errors

Judge candidate models on examples that matter to this project: dropped negatives, broken constructions, expanded contractions, invented name readings, overconfident correction of dialect, and refusal to admit ambiguity. Include cases where the correct action is to leave a good line alone.

A model that changes fewer correct lines may be more useful than one that produces more polished Japanese. A larger model is worth adopting only if its measured improvement justifies its local cost. Keep numerical checks exact, audio judgments grounded in audio, and text-model advice confined to the evidence actually supplied.

## 15 Sources and further reading

Professional guides describe delivery conventions and editorial practice. Research studies address narrower experimental questions. The recommendations for yomisub are the synthesis stated in this document, including the user’s explicit preference for synchronization. The sources do not establish one universal learner subtitle speed or one automatic method that satisfies every professional rule.

### Project and professional guidance

1. **Yomisub README.** [Project purpose and context](https://github.com/sesopenko/yomisub/blob/main/README.md). Read for the project’s stated learning use case; this document is not a code audit.
2. **W3C WAI. Captions/Subtitles.** [Terminology and accuracy considerations](https://www.w3.org/WAI/media/av/captions/).
3. **W3C. Understanding SC 1.2.2: Captions (Prerecorded).** [Accessibility purpose and relevant audio information](https://www.w3.org/WAI/WCAG22/Understanding/captions-prerecorded.html).
4. **Ofcom. Guidelines on Providing Television and On-Demand Access Services.** [Professional access-service guidance](https://www.ofcom.org.uk/siteassets/resources/documents/tv-radio-and-on-demand/broadcast-codes/other-codes/ofcoms-guidelines-on-providing-tv-on-demand-access-services.pdf?v=357066), particularly the subtitling section.
5. **Netflix. Japanese Timed Text Style Guide.** [The specifically requested primary reference](https://partnerhelp.netflixstudios.com/hc/en-us/articles/215767517-Japanese-Timed-Text-Style-Guide). Distinguish Section I, Japanese subtitles, from Section II, Japanese SDH.
6. **Netflix. Timed Text Style Guide: General Requirements.** [General event-duration and presentation requirements](https://partnerhelp.netflixstudios.com/hc/en-us/articles/215758617-Timed-Text-Style-Guide-General-Requirements).
7. **Netflix. Timed Text Style Guide: Subtitle Timing Guidelines.** [Timing, speech, and shot relationships](https://partnerhelp.netflixstudios.com/hc/en-us/articles/360051554394-Timed-Text-Style-Guide-Subtitle-Timing-Guidelines).
8. **DCMP. Captioning Key: Elements of Quality Captioning.** [Quality and preservation of meaning](https://dcmp.org/learn/captioningkey/599DCMP).
9. **DCMP. Captioning Key: Presentation Rate.** [Educational reading-rate guidance](https://dcmp.org/learn/captioningkey/601). Its English word-based conventions are not Japanese learner norms.
10. **DCMP. Captioning Key: Speaker Identification.** [Attribution and information available to the audience](https://dcmp.org/learn/603-captioning-key---speaker-identification).
11. **DCMP. Captioning Key: Text.** [Line division and visual presentation](https://dcmp.org/learn/597-captioning-key---text).
12. **Okosuke / Palabra. Barrier-free subtitle production guidance.** [Japanese professional editorial practice](https://www.okosuke.jp/seisaku). Japanese-language source.
13. **W3C. Requirements for Japanese Text Layout.** [Japanese typographic rules](https://www.w3.org/TR/jlreq/?lang=en), including line-start and line-end restrictions. Typography is broader than subtitle craft.
14. **Japan Foundation. アフレコにチャレンジしよう — Try dubbing!** [Video-based teaching and spoken-language features](https://www.jpf.go.jp/j/project/japanese/teach/tsushin/hint/201301.html), 2013. Japanese-language source.
15. **Japan Foundation. Activate Your Japanese! About.** [Audience choices for Japanese captions and learning material](https://www.hikidasu.jpf.go.jp/jp/about/).

### Research, with scope limits

16. **Montero Perez, M., Peters, E., and Desmet, P. (2014).** *Is less more? Effectiveness and perceived usefulness of keyword and full captioned video for L2 listening comprehension.* [Publisher abstract and study description](https://doi.org/10.1017/S0958344013000256). French L2, not Japanese.
17. **Shin, Jeong Eun (2011).** *The Effect of Video Comprehension with Subtitles.* [Author abstract and bibliographic record](https://www.kci.go.kr/kciportal/landing/article.kci?arti_id=ART001530093). Japanese learner sample; abstract-level evidence used here.
18. **Kawashima, Daisuke (2024).** *Effects of furigana on recognition of Japanese Kanji.* [Institutional repository record and abstract](https://bunkyo.repo.nii.ac.jp/records/2000111). Word-recognition task, not subtitle viewing; abstract-level evidence used here.
19. **Gerber-Morón, O., Szarkowska, A., and Woll, B. (2018).** *The impact of text segmentation on subtitle reading.* [Full article](https://pmc.ncbi.nlm.nih.gov/articles/PMC7901653/). English subtitle segmentation; transfer to Japanese requires care.
20. **Sasaki, Runa (2017).** *Is the Four-Character-per-Second Word Limitation Outdated? An Empirical Study of Japanese Film Subtitling.* [J-STAGE record and abstract](https://www.jstage.jst.go.jp/article/its/17/0/17_1708/_article/-char/en). Small translated-film study, not an N4/N5 learner benchmark.
21. **Peng, Liang, and Sasao (2022).** *The use of video captions and subtitles in Japanese learning: Insights from choice of language.* [J-STAGE record and abstract](https://www.jstage.jst.go.jp/article/gbkkg/20/0/20_335/_article/-char/en). Chinese learner preferences and associations; not proof of a universal causal benefit.
22. **W3C. Understanding SC 1.4.1: Use of Color.** [Why color needs a second visible means of conveying information](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html).
23. **PEPNet-Japan. 動画に字幕を入れる前に — Before inserting captions into videos.** [Japanese educational captioning guidance](https://www.pepnet-j.org/contents/archives/1923). Japanese-language source.

### Local-model appendix sources

24. **Ollama: Qwen3.5 4B Q4_K_M.** [Exact package and size](https://ollama.com/library/qwen3.5:4b-q4_K_M).
25. **Ollama: Qwen3.5 9B Q4_K_M.** [Exact package and size](https://ollama.com/library/qwen3.5:9b-q4_K_M).
26. **Ollama: Gemma 4 12B IT Q4_K_M.** [Exact package and size](https://ollama.com/library/gemma4:12b-it-q4_K_M).
27. **Ollama documentation: Context length.** [Context and memory guidance](https://docs.ollama.com/context-length).
28. **Ollama documentation: FAQ.** [Residency, parallel requests, and memory](https://docs.ollama.com/faq).
29. **Qwen: Qwen3.5 announcement.** [Official family description and language coverage](https://qwen.ai/blog?id=qwen3.5).
30. **Qwen: Qwen3.5-4B model card.** [Official model behavior and usage guidance](https://huggingface.co/Qwen/Qwen3.5-4B).
31. **Google: Gemma 4 12B IT model card.** [Official model capabilities and limitations](https://huggingface.co/google/gemma-4-12B-it).

Model availability, package sizes, and runtime behavior can change. The appendix records the catalog information reviewed on 18 November 2026; the durable principles are bounded tasks, evidence-aware judgments, and verification against the actual learner use case.
