import unittest

from editorial_fixtures import evidence, retry, segment
from yomisub.domain import ListenerDecision, Voice
from yomisub.reconcile import reconcile


class ReconciliationTests(unittest.TestCase):
    def test_fight_listener_replaces_merged_owner_and_preserves_raw(self):
        segments=[segment(str(i),s,i*1000,i*1000+500) for i,s in enumerate(['こうします','そう','耐えられる'])]
        ev=evidence(segments,[(0,4000,'merged')])
        auto=reconcile(ev)
        self.assertEqual([c.owners[0].voice.label for c in auto.candidates],['merged']*3)
        edits=[ListenerDecision('o'+str(i),str(i),'listener','owner',Voice('listener',v))
               for i,v in enumerate('ABB')]
        corrected=reconcile(ev,edits)
        self.assertEqual([c.owners[0].voice.label for c in corrected.candidates],list('ABB'))
        self.assertEqual(auto,reconcile(ev))
        self.assertEqual(ev.transcripts[0].segments,tuple(segments))

    def test_confirmed_wording_and_unique_timed_solo_continuation(self):
        core='scan:span:2000:3000'
        text='待ってね'
        tokens=[('待って',2500,2950),('ね',3050,3300)]
        extra=[retry('retry',core,text,2450,3400,tokens),retry('stem2',core,text,2450,3400,tokens,2)]
        ev=evidence([segment('primary','王様',1000,3000,[('王様',1400,1700)])],
                    [(1000,3000,'A'),(2000,3400,'B')],extra)
        primary,other=reconcile(ev).candidates
        self.assertEqual((primary.text,primary.owners[0].voice.label),('王様','A'))
        self.assertEqual(other.owners[0].voice.label,'B')
        self.assertIn('retry-s-1',other.owners[0].evidence_ids)
        self.assertTrue(other.secondary and other.wording_supported)
        self.assertIn('stem2-s',primary.alternative_ids)
        self.assertIn('stem2-s',other.evidence_ids)

    def test_mixed_voices_and_matching_stem_leave_owner_open(self):
        core='scan:span:2000:3000'
        e=evidence([segment('primary','待つ',2000,3000)],
                   [(2000,3000,'A'),(2000,3000,'B')],
                   [retry('r',core,'そう',2100,2550,[('そう',2100,2550)]),
                    retry('stem',core,'そう',2100,2550,[],1)])
        res=reconcile(e)
        self.assertTrue(res.candidates[1].wording_supported)
        self.assertFalse(res.candidates[1].owners)
        self.assertTrue(any(f.id==core+'-unresolved' for f in res.findings))
        edit=ListenerDecision('word','primary','reader','wording','待って')
        self.assertEqual(reconcile(e,[edit]).candidates[0].text,'待って')
        self.assertEqual(e.transcripts[0].segments[0].text,'待つ')

    def test_padding_never_adds_line_and_distinct_repetitions_survive(self):
        core='scan:span:1000:4500'
        obs=[retry('r1',core,'そう',1200,1700,[]),retry('r2',core,'そう',1250,1750,[]),
             retry('r3',core,'そう',3000,3500,[]),retry('padding',core,'はい',500,700,[],context_only=True)]
        e=evidence([],[(1000,4500,'A'),(1000,4500,'B')],obs)
        res=reconcile(e)
        self.assertEqual(len(res.candidates),2)
        self.assertEqual(res.candidates[0].evidence_ids,('r1-s','r2-s'))
        self.assertEqual(res.candidates[1].id,'r3-s')
