from fractions import Fraction as F
import unittest

from yomisub.domain import PlannedPhrase,RecordingClock,SampleInterval,Voice
from yomisub.layout import layout


class LayoutTests(unittest.TestCase):
    clock=RecordingClock(1000,5000,F(0),F(5))

    def phrase(self,id,text,a,b,who=None):
        return PlannedPhrase(id,text,Voice('r',who) if who else None,SampleInterval(self.clock,a,b),())

    def test_staggered_entry_release_and_demand(self):
        phrases=(self.phrase('a','ABCDEFGH',0,2000,'A'),self.phrase('b','あいうえおか',1000,3000,'B'))
        states,findings=layout(self.clock,phrases)
        self.assertEqual([[l.phrase_id for l in s.lanes] for s in states],[['a'],['a','b'],['b'],[]])
        self.assertEqual([s.characters_per_second for s in states],[4,7,3,0])
        self.assertEqual(states[1].lanes[1],states[2].lanes[0])
        self.assertFalse(findings)

    def test_stable_same_onset_crowding_and_coincident_transition(self):
        p=(self.phrase('z','一',0,2500,'z'),self.phrase('a','二',0,1000,'a'),
           self.phrase('c','三',0,1000),self.phrase('d','四',1000,2000,'a'))
        states,findings=layout(self.clock,p)
        self.assertEqual(layout(self.clock,p[::-1]),(states,findings))
        first,second=states[:2]
        self.assertEqual([l.phrase_id for l in first.lanes],['a','c','z'])
        self.assertIsNone(first.lanes[1].label)
        self.assertEqual(first.lanes[0].label,second.lanes[0].label)
        self.assertEqual(first.lanes[0].number,second.lanes[0].number)
        self.assertEqual(first.lanes[-1],second.lanes[-1])
        self.assertEqual(findings[0].evidence_ids,('a','c','z'))
