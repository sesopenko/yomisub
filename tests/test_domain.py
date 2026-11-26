import unittest
from dataclasses import FrozenInstanceError
from fractions import Fraction as F

from yomisub.domain import (
    Attribution, AudioSource, Lane, ListenerDecision, PhraseCandidate, PlannedPhrase,
    RawTiming, RecordingClock, ReviewFinding, SampleInterval, ScreenState,
    TextPiece, TextSpan, TranscriptSegment, Voice, VoiceTurn,
)


class DomainTests(unittest.TestCase):
    def setUp(self):
        self.clock = RecordingClock(44100, 44100, F(1, 4), F(2))

    def test_derived_clock_keeps_fractional_sample_with_delay_and_padding(self):
        source = AudioSource("stem-1", "crop", 16000, 200, F(11), 2, 4, 1, column=1)
        mapped = source.recording_sample(4, self.clock)
        self.assertEqual(mapped, 11 + F(441, 160))
        self.assertEqual(self.clock.playback_time(mapped), F(1, 4) + F(11, 44100) + F(1, 16000))
        self.assertIsNone(AudioSource("original", None, 44100, 44100).column)

    def test_raw_invalid_endpoints_survive_validation(self):
        for start, end in [(8, 3), (0, 44101), (1, 1)]:
            with self.subTest(start=start, end=end):
                raw = RawTiming(start, end, "samples")
                piece = TextPiece("piece", 14, " そう", TextSpan(0, 3), raw)
                segment = TranscriptSegment("segment", "mix-run", " そう", raw, (piece,))
                with self.assertRaises(ValueError):
                    SampleInterval(self.clock, raw.start, raw.end)
                self.assertEqual(segment.pieces[0].timing, raw)

    def test_source_observation_can_precede_video(self):
        clock = RecordingClock(100, 100, F(-1, 10), F(1))
        span = SampleInterval(clock, 0, 20)
        with self.assertRaises(ValueError):
            PlannedPhrase("p", "test", None, span, ("segment",))
        self.assertEqual(clock.playback_time(span.start), F(-1, 10))

    def test_two_owners_wordless_turn_and_listener_overlay_are_independent(self):
        overlap = SampleInterval(self.clock, 10, 30)
        a, b = Voice("scan", "A"), Voice("scan", "B")
        turn = VoiceTurn("turn-b", b, RawTiming(10, 30, "samples"), overlap)
        candidate = PhraseCandidate("p", "まって", ("mix-segment",), overlap,
                                    (Attribution(a, ("turn-a",)), Attribution(b, (turn.id,))))
        decision = ListenerDecision("listen", candidate.id, "listener", "owner", a)
        finding = ReviewFinding("unknown-words", "Second voice has no words", (turn.id,), overlap)
        self.assertEqual(candidate.owners[1].voice, turn.voice)
        self.assertEqual(finding.evidence_ids, (turn.id,))
        self.assertEqual(decision.target_id, candidate.id)
        with self.assertRaises(FrozenInstanceError):
            candidate.text = "changed"
        first = PlannedPhrase("first", candidate.text, a, overlap, (candidate.id, decision.id))
        second = PlannedPhrase("second", "別", b, overlap, ("other-reading",))
        state = ScreenState(overlap, (Lane(0, first.id), Lane(1, second.id)))
        self.assertEqual(tuple(lane.phrase_id for lane in state.lanes), ("first", "second"))
