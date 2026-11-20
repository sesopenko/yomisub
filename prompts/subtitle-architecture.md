# subtitle architecture input analysis

docs/japanese-subtitling-craft-for-yomisub.md contains SME guidance on producing subtitles for the project.  enhancement with local models is a future iteration to do.

What needs to be done for now is to design an architectural structure for the code base to support subtitling as the guide outlines.

This means:

Understanding the parameter flags and the output of whisper in detail, and how it converts spoken audio to text is important, that's the input capabilities.

Understanding of docs/japanese-subtitling-craft-for-yomisub.md then needs to be done.

A couple runs on some example video would be useful as well.

gitignored-inputs/examples/S01E01.mp4 contains some calm dialog with multiple voice actors
gitignored-inputs/examples/S01E02.mp4 contains a theme song with vocals
gitignored-inputs/examples/S01E03.mp4 contains some action that makes it a little hard to understand the audio, potentially, because characters are speaking in the middle of a fight.

I've already solved some problems around tokenization, it's timing issues and display issues I'm working through, as well as good sub-stringing.  I think I already have some code that pulls different actors, making it possible to separate who's speaking, but overlaying them with good timing hasn't been solved.

The tokenization solution I have so far isn't bad, would likely need some refactoring for reuse and repurposing. But don't take existing timing solutions in the project as ideal, docs/japanese-subtitling-craft-for-yomisub.md is better guidance.

For this plan, whisper must be run against the examples with different outputs looked at, to ascertain what can be output from whisper.  the agent can also ask me questions about what I'm hearing with my own ears, to confirm things.

Then the build agent is to record findings in docs/whisper-input-findings.md

These findings are to ascertain the capabilities of whisper that can fulfill the direction of docs/japanese-subtitling-craft-for-yomisub.md, with deterministic handling of things in new python architecture in mind.