from fractions import Fraction as F
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock

from yomisub.activity import ActivitySpan
from yomisub.domain import AudioSource, ModelRun, RecordingClock, SampleInterval, Voice
from yomisub.ports import AudioFile, ExecutionTarget, Stage, StageError, Transcript
from yomisub.stems import SepFormer, StemRefiner, analysis_source


class StemTests(unittest.TestCase):
    def setUp(self):
        self.work = Path(self.enterContext(TemporaryDirectory()))
        self.clock = RecordingClock(16000,320000,F(0),F(20))
        self.target = ExecutionTarget("amd-rocm","pci:test",0,Stage.SEPARATION)
        self.asr = Mock()
        self.worker = Mock()
        self.separator = SepFormer(self.worker)
        self.refiner = StemRefiner(Mock(),self.separator,self.asr)

    def source(self, key):
        return AudioFile(AudioSource(key,"mix",16000,16000,F(32000),core_id=key), self.work/"mix.wav")

    def core(self, key, voices=2, length=1):
        return ActivitySpan(key,SampleInterval(self.clock,32000,32000+16000*length),
                            tuple(Voice('r',str(i)) for i in range(voices)))

    def response(self, cols):
        def worker(action,target,**payload):
            root=Path(payload["output"])
            for col in cols:
                for suffix in ("","-16k"):
                    (root/f"stem-{col}{suffix}.wav").touch()
            return dict(frames=8000,analysis_frames=16000,versions={"speechbrain":"1.0.3"},
                        elapsed_seconds=2,peak_allocated_bytes=10)
        self.worker.request.side_effect = worker

    def test_swapped_source_columns_are_excerpt_local_and_preserve_delay(self):
        self.response([2,1])
        a=self.separator.separate(self.source("a"),self.target,self.work)
        b=self.separator.separate(self.source("b"),self.target,self.work)
        self.assertNotEqual(a.stems[1].source.id,b.stems[1].source.id)
        self.assertEqual(a.analysis[1].source.parent_id,a.stems[1].source.id)
        delayed=AudioSource("stem","crop",8000,8000,F(32000),delay=8,column=1)
        wide=analysis_source(delayed,16000)
        self.assertEqual(wide.recording_sample(16,self.clock),delayed.recording_sample(8,self.clock))

    def test_missing_stem_and_asr_failure_leave_audio_available(self):
        self.response([1])
        self.asr.transcribe.side_effect=StageError("decoder failed")
        result=self.refiner.refine_core(self.core("a"),self.source("a"),"ja",self.work,Mock())
        self.assertEqual(len(result.files),2)
        self.assertEqual(len(result.runs),1)
        self.assertFalse(result.transcripts)
        self.assertEqual(len(result.findings),2)

    def test_two_stems_attempted_independently_and_bounds(self):
        self.response([1,2])
        run=ModelRun('asr','stem2','test','1','large',(),'test','pci:test')
        self.asr.transcribe.side_effect=[StageError("first"),Transcript(run,())]
        res=self.refiner.refine_core(self.core("a"),self.source("a"),"ja",self.work,Mock())
        self.assertEqual(len(res.files),4)
        self.assertEqual(res.transcripts[0].core_id,"a")
        for core in (self.core('b',3),self.core('c',length=13)):
            skipped=self.refiner.refine_core(core,self.source(core.id),'ja',self.work,Mock())
            self.assertEqual(skipped.findings[0].interval,core.interval)
        self.assertEqual(self.worker.request.call_count,1)
