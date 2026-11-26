from dataclasses import replace
import unittest

from editorial_fixtures import evidence, segment
from yomisub.grouping import PhraseGrouping
from yomisub.layout import CuePlanner
from yomisub.spotting import spot


class RealMediaRegressions(unittest.TestCase):
    def test_solo_asr_fringe_needs_two_sided_lexical_support_and_no_interruption(self):
        seg = segment("a", "広場に行く", 0, 1000, [("広場", 0, 100), ("に", 200, 300), ("行く", 650, 800)])
        solo = evidence([seg], [(150, 900, "A")])
        phrase = spot(replace(solo, planner_version=2)).phrases[0]
        self.assertEqual((phrase.interval.start, phrase.interval.end, phrase.owner.label), (150, 800, "A"))
        self.assertIsNone(spot(solo).phrases[0].owner)
        for turns in [[(150, 400, "A")], [(150, 400, "A"), (650, 900, "B")]]:
            ev = replace(evidence([seg], turns), planner_version=2)
            self.assertIsNone(spot(ev).phrases[0].owner)

    def test_commas_with_touching_estimates_keep_one_phrase_and_whitespace_needs_pause(self):
        seg = segment("a", "そう、待って", 0, 900, [("そう", 0, 200), ("、", 200, 300), ("待って", 300, 900)])
        ev = evidence([seg], [(0, 900, "A")])
        def grouped(ev):
            return replace(ev, groups=PhraseGrouping().group(ev.transcripts[0], "ja"), planner_version=2)
        self.assertEqual([p.text for p in spot(grouped(ev)).phrases], ["そう、待って"])
        seg = segment("b", "先生 そこで待つ", 0, 900,
                      [("先", 0, 150), ("生", 160, 400), (" そこ", 410, 590), ("で", 600, 730), ("待つ", 731, 900)])
        self.assertEqual(len(spot(grouped(evidence([seg], [(0, 900, "A")]))).phrases), 1)
        parts = spot(grouped(evidence([seg], [(0, 340, "A"), (455, 900, "A")]))).phrases
        self.assertEqual([p.text.strip() for p in parts], ["先生", "そこで待つ"])

    def test_zero_duration_space_at_a_real_pause_preserves_recurrent_voice(self):
        seg = segment("a", "先生 今日です", 0, 1000,
                      [("先", 0, 200), ("生", 200, 410), (" ", 410, 410),
                       ("今", 410, 580), ("日", 580, 690), ("です", 690, 1000)])
        ev = evidence([seg], [(0, 400, "A"), (455, 1000, "A")])
        ev = replace(ev, groups=PhraseGrouping().group(ev.transcripts[0], "ja"), planner_version=2)
        phrases = spot(ev).phrases
        self.assertEqual([p.text.strip() for p in phrases], ["先生", "今日です"])
        self.assertEqual(phrases[-1].owner.label, "A")

    def test_unrecognized_tail_and_uncertain_surface_are_addressable(self):
        seg = segment("p", "声", 0, 200, [("声", 0, 200)])
        piece = replace(seg.pieces[0], probability=0.25)
        ev = replace(evidence([replace(seg, pieces=(piece,))], [(0, 200, "A")]), planner_version=2)
        plan = CuePlanner().plan(ev, ())
        self.assertTrue(any(f.id == "p-wording" and f.evidence_ids == (piece.id,) for f in plan.findings))
        gap = next(f for f in plan.findings if f.id.startswith("untranscribed-"))
        self.assertEqual((gap.interval.start, gap.interval.end), (200, 10000))
        self.assertFalse(plan.states[-1].lanes)

    def test_release_uses_last_complete_supported_word_and_keeps_raw_times(self):
        # 記憶 is a single dictionary word made from two model tokens.
        seg = segment("p", "夜の記憶", 0, 2000,
                      [("夜", 0, 700), ("の", 700, 1150), ("記", 1150, 1300), ("憶", 1600, 2000)])
        ev = evidence([seg], [(0, 645, "A"), (680, 1500, "A")])
        ev = replace(ev, groups=PhraseGrouping().group(ev.transcripts[0], "ja"), planner_version=2)
        plan = spot(ev)
        self.assertEqual((plan.phrases[0].text, plan.phrases[0].interval.end), ("夜の記憶", 1150))
        self.assertTrue(any(f.id == "p-release" for f in plan.findings))
        self.assertEqual(ev.transcripts[0].segments[0].timing.end, 2000)

    def test_unvoiced_uncertain_foreign_reading_abstains_and_keeps_hypothesis(self):
        seg = segment("p", "Outro", 8000, 9000, [("Outro", 8000, 9000)])
        seg = replace(seg, pieces=(replace(seg.pieces[0], probability=0.04),))
        ev = replace(evidence([seg]), planner_version=2)
        result = spot(ev)
        self.assertFalse(result.phrases)
        self.assertEqual(result.candidates[0].text, "Outro")
        voiced = replace(evidence([seg], [(7900, 9500, "A")]), planner_version=2)
        self.assertEqual(spot(voiced).phrases[0].text, "Outro")

    def test_rttm_keeps_same_physical_edge_identical_on_adjacent_turns(self):
        from fractions import Fraction
        from types import SimpleNamespace
        from runtime.amd.turns import rttm
        from yomisub.activity import overlap_cores, read_rttm

        class Annotation:
            uri = "clip"

            def itertracks(self, yield_label):
                assert yield_label
                yield SimpleNamespace(start=11.1236, end=13.0583), 0, "A"
                yield SimpleNamespace(start=13.0583, end=16.0138), 0, "B"
        ev = evidence([], duration=20000)
        scan = read_rttm(rttm(Annotation()), "clip", ev.scan.run, ev.sources[1], ev.clock)
        self.assertEqual(overlap_cores(scan, ev.clock), ())
        self.assertEqual(scan.turns[0].timing.end, Fraction("13.0583"))
        self.assertEqual(scan.turns[1].timing.start, scan.turns[0].timing.end)
