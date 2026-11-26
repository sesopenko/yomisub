from dataclasses import replace
import unittest

from editorial_fixtures import evidence, retry, segment
from yomisub.domain import ListenerDecision
from yomisub.ports import Grouping
from yomisub.spotting import spot


class SpottingTests(unittest.TestCase):
    def test_independent_edges_long_phrase_short_reply_and_no_accumulation(self):
        ev=evidence([segment('p','長い話',0,7500,[('長い',100,200),('話',7300,7450)]),
                     segment('b','はい',8000,8200,[('はい',8020,8080)])],[(0,9000,'A')])
        a,b=spot(ev,[ListenerDecision('end','p','R','end',7400)]).phrases
        self.assertEqual((a.interval.start,a.interval.end),(100,7400))
        self.assertEqual((b.interval.start,b.interval.end),(8020,8080))
        a,b=spot(ev,[ListenerDecision('start','p','R','start',50)]).phrases
        self.assertEqual((a.interval.start,a.interval.end),(50,7450))

    def test_bad_edges_fall_back_and_silence_stays_clear(self):
        ev=evidence([segment('fx','[音楽]',0,3000),segment('inv','そう',1200,1600,[('そう',15480,2970)]),
                     segment('bad','本当',9500,10500)],[(1200,1600,'A')])
        res=spot(ev)
        self.assertEqual([(p.id,p.interval.end) for p in res.phrases],[('inv',1600)])
        self.assertTrue(any(f.id=='inv-anchors' for f in res.findings))
        self.assertTrue(any(f.id=='bad-timing' for f in res.findings))

    def test_supported_cut_and_replacement_surface_without_old_offsets(self):
        seg=segment('s','行く。できない',0,1000,[('行く。',10,200),('でき',300,500),('ない',510,900)])
        group=Grouping('s',(),(3,), 'fixture')
        ev=evidence([seg],[(0,1000,'A')],groups=[group])
        result=spot(ev)
        self.assertEqual([(p.text,p.interval.start,p.interval.end) for p in result.phrases],
                         [('行く。',10,200),('できない',300,900)])
        corrected=spot(ev,[ListenerDecision('w','s','R','wording','そう')])
        self.assertEqual([(p.text,p.interval.end) for p in corrected.phrases],[('そう',900)])

    def test_expanding_into_overlap_and_narrowing_loses_lexical_owner(self):
        ev=evidence([segment('p','待ってね',0,2000,[('待って',200,600),('ね',1500,1800)])],
                    [(0,2500,'A'),(1000,2500,'B')])
        self.assertEqual(spot(ev).phrases[0].owner.label,'A')
        narrowed=spot(ev,[ListenerDecision('s','p','L','start',1200)])
        self.assertIsNone(narrowed.phrases[0].owner)
        solo=evidence([segment('p','そう',0,500)],[(0,2500,'A'),(1000,2500,'B')])
        expanded=spot(solo,[ListenerDecision('e','p','L','end',1700)])
        self.assertIsNone(expanded.phrases[0].owner)

    def test_second_line_requires_lexical_edges_and_independent_owner(self):
        core='scan:span:2000:3000'
        pieces=[('待って',2410,2960),('ね',3010,3250)]
        observations=[retry('r',core,'待ってね',2400,3300,pieces),retry('stem',core,'待ってね',2400,3300,[],2)]
        ev=evidence([segment('first','行く',1000,3000,[('行く',1500,1700)])],
                    [(1000,3000,'A'),(2000,3400,'B')],observations)
        proposed=spot(ev)
        second=next(p for p in proposed.phrases if p.id=='r-s')
        self.assertEqual((second.interval.start,second.interval.end,second.owner.label),(2410,3250,'B'))
        no_anchor=replace(ev,transcripts=(ev.transcripts[0],replace(ev.transcripts[1],segments=(
            replace(ev.transcripts[1].segments[0],pieces=()),)),ev.transcripts[2]))
        self.assertEqual(len(spot(no_anchor).phrases),1)
