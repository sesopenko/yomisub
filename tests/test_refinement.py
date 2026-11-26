from fractions import Fraction as F
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock
import wave

from yomisub.activity import ActivitySpan, read_rttm
from yomisub.domain import AudioSource, ModelRun, RawTiming, RecordingClock, SampleInterval, TranscriptSegment
from yomisub.ports import AudioFile, PreparedTrack, StageError, Transcript
from yomisub.refinement import OverlapRefiner, anchored_interval, link_transcript


class RetryTests(unittest.TestCase):
    def setUp(self):
        self.work = Path(self.enterContext(TemporaryDirectory()))
        path = self.work / 'mix.wav'
        with wave.open(str(path),'wb') as f:
            f.setparams((1,2,16000,0,'NONE','not compressed'))
            f.writeframes(bytes(16000*2*6))
        self.src = AudioSource('mix','original',16000,96000)
        self.clock = RecordingClock(16000,96000,F(0),F(6))
        self.track = PreparedTrack(self.clock,AudioFile(AudioSource('original',None,16000,96000),path),
                                   AudioFile(self.src,path))
        self.run = ModelRun('scan','mix','test','1','model',(),'test','dev')
        self.asr = Mock()
        self.refiner = OverlapRefiner(Mock(), self.asr)

    def invoke(self, intervals):
        text = '\n'.join(f'SPEAKER c 1 {s} {d} <NA> <NA> {label} <NA> <NA>' for s,d,label in intervals)
        scan = read_rttm(text,'c',self.run,self.src,self.clock)
        return self.refiner.refine(Mock(),self.track,scan,self.work,Mock())

    def test_edges_intersecting_context_and_crowding(self):
        def decode(crop, lang, model, target, work):
            start = 1750 - crop.source.origin / 16
            seg = TranscriptSegment(crop.source.id+'-s','retry','same',RawTiming(start,start+100,'milliseconds'),())
            return Transcript(self.run,(seg,))
        self.asr.transcribe.side_effect = decode
        result = self.invoke([(0,6,'A'),(0,1,'B'),(2,1,'B'),(2,1,'C'),(5,1,'C')])
        self.assertEqual(self.asr.transcribe.call_count,3)
        a,b,c = result.files
        self.assertEqual((a.source.origin,c.source.origin+c.source.frames),(0,96000))
        self.assertGreater(a.source.frames,b.source.origin)
        self.assertEqual(len({t.core_id for t in result.transcripts}),3)
        for tr, file in zip(result.transcripts[:2],result.files):
            self.assertEqual(tr.context_only_segment_ids,(tr.segments[0].id,))
            self.assertEqual(anchored_interval(tr.segments[0].timing,file.source,self.clock).start,28000)

    def test_no_core_and_failed_retry(self):
        self.assertFalse(self.invoke([(0,4,'A')]).files)
        self.asr.transcribe.assert_not_called()
        self.asr.transcribe.side_effect = StageError('bad checkpoint')
        result = self.invoke([(0,4,'A'),(1,1,'B')])
        self.assertEqual(len(result.files),1)
        self.assertEqual(result.findings[0].interval.end,32000)
        self.assertEqual(result.findings[0].evidence_ids,(result.files[0].source.core_id,))

    def test_documented_s01e10_alternatives_keep_distinct_origins(self):
        clock = RecordingClock(1000,30000,F(0),F(30))
        core = ActivitySpan('overlap',SampleInterval(clock,26221,26744),())
        for origin, text in [(24000,'あつりょくに くっしない'),(24221,'だれかいるのか')]:
            src = AudioSource('crop'+str(origin),'mix',1000,5000,F(origin))
            segment = TranscriptSegment('s','r',text,RawTiming(1000,2000,'milliseconds'),())
            linked = link_transcript(Transcript(self.run,(segment,)),src,core)
            self.assertEqual(linked.segments[0].text,text)
            self.assertEqual(anchored_interval(segment.timing,src,clock).start,origin+1000)
