from fractions import Fraction as F
from html import unescape
from types import SimpleNamespace
import unittest
import re
import srt

from yomisub.domain import PlannedPhrase, RecordingClock, SampleInterval, Voice
from yomisub.layout import layout
from yomisub.ports import CuePlan
from yomisub.writers import AssWriter, SrtWriter, ticks


def make_plan(values):
    clock=RecordingClock(10000,40000,F(0),F(4))
    phrases=tuple(PlannedPhrase(id,text,Voice("r",id),SampleInterval(clock,a,b),()) for id,text,a,b in values)
    states,findings=layout(clock,phrases)
    return CuePlan(phrases,states,findings)


class WriterTests(unittest.TestCase):
    def test_parsed_exports_share_words_and_keep_literal_controls(self):
        p=make_plan([('a','駅で待ってる。',0,14000),('b',r'{\pos(9,9)}\N<はい>',9000,18000)])
        cues=list(srt.parse(SrtWriter().render(p).data.decode()))
        self.assertEqual([c.start.total_seconds() for c in cues],[0,.9,1.4])
        self.assertIn(p.phrases[1].text,unescape(cues[-1].content))
        lines=[l.split(',',9) for l in AssWriter().render(p).data.decode().splitlines() if l.startswith('Dialogue:')]
        self.assertEqual([(l[1],l[2]) for l in lines],[('0:00:00.00','0:00:01.40'),('0:00:00.90','0:00:01.80')])
        literal=re.sub(r'^\{[^}]*\}','',lines[1][-1]).replace('\\{','{').replace('\\}','}').replace('\u2060','')
        self.assertIn(p.phrases[1].text,literal)
        self.assertNotIn(r'{\pos(9,9)}',lines[1][-1])
        self.assertNotIn(r'\N',lines[1][-1])

    def test_round_half_up_clamp_and_unique_finding(self):
        p=make_plan([('a','短',14,17),('b','一',15,16)])
        srt_result,ass_result=SrtWriter().render(p),AssWriter().render(p)
        self.assertEqual({f.id for f in ass_result.findings},{'ass-precision-a','ass-precision-b'})
        self.assertTrue(srt_result.data)
        self.assertEqual(len({f.id for f in srt_result.findings}),len(srt_result.findings))
        clock=RecordingClock(10000,1000,F(0),F(99,1000))
        self.assertEqual(ticks(SampleInterval(clock,49,50),100,{}),(0,1))
        self.assertEqual(ticks(SampleInterval(clock,980,990),100,{}),(9,9))
