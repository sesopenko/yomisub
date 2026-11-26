import unittest

from yomisub.asr import parse_transcript
from yomisub.domain import ModelRun
from yomisub.grouping import PhraseGrouping


def grouped(text, pieces, language='ja'):
    obj={'model':{'multilingual':True},'transcription':[{'text':text,'offsets':{'from':0,'to':10000},
         'tokens':[{'text':s,'id':n,'offsets':{'from':n*100,'to':n*100+100}} for n,s in enumerate(pieces)]}]}
    tr=parse_transcript(obj,ModelRun('r','mix','test','1','m',(),'test','d'))
    return PhraseGrouping().group(tr,language)[0]


class GroupTests(unittest.TestCase):
    def test_exact_join_repetitions_multichar_and_wrap_inside_piece(self):
        text=' ここはここ。次です'
        g=grouped(text,[' ここ','はここ。','次です'])
        self.assertEqual(''.join(text[s.start:s.end] for s in g.surfaces),text)
        self.assertIn(4,g.wrap_offsets)
        self.assertNotIn(4,g.cut_offsets)
        self.assertIn(7,g.cut_offsets)
        self.assertEqual(g.split_mode,'C')
        self.assertEqual(g.tokenizer_version,'0.7.0')
        self.assertEqual(g.dictionary_version,'20261015')
        self.assertEqual(g.piece_ids[0],('r:s0:t0',))

    def test_protect_negative_contraction_and_late_reversal(self):
        for text in ['できない','食べちゃった','できるかもしれない','食べられません']:
            with self.subTest(text=text):
                self.assertFalse(grouped(text,list(text)).wrap_offsets)
        text = '行く。今日はできない。'
        g=grouped(text,['行く。','今日は','でき','ない。'])
        self.assertIn(3,g.cut_offsets)
        self.assertNotIn(text.index('ない'),g.wrap_offsets)

    def test_unsplit_fallback_and_other_language(self):
        g=grouped('日本','東京')
        self.assertEqual(g.strategy,'segment')
        self.assertTrue(g.diagnostic)
        en=grouped('some text',['some',' text'],'en')
        self.assertFalse(en.cut_offsets)
        self.assertIsNone(en.diagnostic)
