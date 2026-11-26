import json
from pathlib import Path
import unittest

from evaluation.score import Display, interval_result, map_owners, overlap_events, paired, score_phrases


def reference(name, surface, owner='A', edges=None):
    ref = {'id': name, 'forms': [surface], 'owner': owner, 'window_ms': [0, 4000]}
    if edges is not None:
        ref['speech_edges_ms'] = edges
    return ref


class EvaluationTests(unittest.TestCase):
    def test_adjacent_states_retain_continuing_line_and_distinct_owners(self):
        refs = [reference('a', '行こう', edges=[100, 600]), reference('b', '待って', 'B'),
                reference('again', '行こう'), reference('missing', 'はい')]
        display = [Display(100, 300, '行こう', 'V1'), Display(300, 800, '行こう', 'V1'),
                   Display(300, 800, '待って', 'V1'), Display(1500, 1800, '行こう')]
        result = score_phrases(refs, display, owner_map={'V1': 'A'})
        self.assertEqual(result['a']['error_ms'], [0, 200])
        self.assertEqual(result['b']['ownership'], 'wrong')
        self.assertEqual(result['again']['ownership'], 'unresolved')
        self.assertFalse(result['missing']['recovered'])
        self.assertEqual(map_owners([('V1','A'), ('V1','A'), ('V1','B')]), {'V1':'A'})

    def test_fragmented_phrase_and_two_phrases_in_one_cue(self):
        refs = [reference('a', 'あした'), reference('b', '行こう'), reference('c', 'はい')]
        result = score_phrases(refs, [Display(0,500,'あし'),Display(500,800,'た'),
                                       Display(900,1200,'行こう、はい')])
        self.assertEqual(result['a']['display_ms'], [0,800])
        self.assertEqual(result['b']['display_ms'], result['c']['display_ms'])
        self.assertEqual(result['a']['ownership'], 'unavailable')

    def test_do_not_reuse_chars_or_join_simultaneous_lines(self):
        refs = [reference('one', 'いい'), reference('two', 'いい'), reference('false', '赤青')]
        result = score_phrases(refs, [Display(0,200,'いい'),Display(250,500,'赤'),Display(250,500,'青')])
        self.assertTrue(result['one']['recovered'])
        self.assertFalse(result['two']['recovered'])
        self.assertFalse(result['false']['recovered'])

    def test_events_are_one_to_one_with_both_edges_within_tolerance(self):
        result = overlap_events([(1000, 2000),(2500,3500)], [(900,1950),(950,2050),(2500,4001)])
        self.assertEqual(result, {'hits':1,'misses':1,'false_positives':2,'edge_errors_ms':[[-50,50]]})
        self.assertEqual(overlap_events([(0,20)], [(20,40)])['hits'], 0)

    def test_no_speech_abstention_and_spurious_words(self):
        self.assertEqual(interval_result((10,100),[Display(10,80,'[音楽]')]),'empty')
        self.assertEqual(interval_result((10,100),[],[(20,90)]),'abstained')
        self.assertEqual(interval_result((10,100),[Display(20,80,'はい')],[(20,90)]),'displayed')

    def test_preserve_ids_even_if_totals_match_and_require_independent_edges(self):
        refs = [reference('old', 'いい'), reference('new', 'そう')]
        refs[0]['waveform_placement_ms'] = [100,200]
        before = score_phrases(refs, [Display(100,200,'いい')])
        after = score_phrases(refs, [Display(100,200,'そう')])
        check = paired(before, after)
        self.assertEqual(check['lost_ids'], ['old'])
        self.assertFalse(check['coverage_pass'])
        self.assertEqual(check['timed_ids'], [])
        self.assertFalse(check['timing_pass'])

    def test_frozen_manual_subset_and_two_median_gate(self):
        root = Path(__file__).resolve().parents[1] / 'evaluation'
        scores = json.loads((root/'legacy-scores.json').read_text())['ingcrowd01-first23']
        outcome = paired(scores, scores)
        self.assertEqual(outcome['timed_ids'], ['a1','a3','a41','a4'])
        self.assertEqual(outcome['legacy_median_abs_ms'], [1815,1305])
        self.assertFalse(outcome['timing_pass'])
        fixed = {key: {**v, 'error_ms':[0,0]} if 'error_ms' in v else v for key,v in scores.items()}
        self.assertTrue(paired(scores,fixed)['timing_pass'])
