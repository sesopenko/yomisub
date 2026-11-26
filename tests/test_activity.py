from fractions import Fraction as F
from pathlib import Path
from unittest.mock import Mock
import unittest

from adapter_contracts import check_scan
from yomisub.activity import activity, coverage, overlap_cores, read_rttm
from yomisub.domain import AudioSource, ModelRun, RecordingClock, SampleInterval
from yomisub.ports import AudioFile, ExecutionTarget, PreparedTrack, Stage, StageError
from yomisub.scanner import SpeakerScanner


def rows(parts):
    return '\n'.join(f'SPEAKER clip 1 {s} {d} <NA> <NA> {label} <NA> <NA>' for s,d,label in parts)


class ActivityTests(unittest.TestCase):
    def setUp(self):
        self.clock = RecordingClock(1000,40000,F(0),F(40))
        self.src = AudioSource("mix","original",16000,640000)
        self.run = ModelRun('scan','mix','test','1','model',(),'test','device')

    def parse(self, text, uri="clip"):
        return read_rttm(text,uri,self.run,self.src,self.clock)

    def test_recorded_interval_and_offset(self):
        text = (Path(__file__).resolve().parents[1]/'docs/whisper-example-speaker-turns.rttm').read_text()
        for offset in (0, 2):
            self.clock = RecordingClock(1000,40000,F(offset),F(45))
            core, = overlap_cores(self.parse(text,'S01E10'),self.clock)
            self.assertEqual((core.interval.start,core.interval.end), (26221,26744))
            self.assertEqual(self.clock.playback_time(core.interval.start), F(26221,1000)+offset)
            self.assertEqual(self.clock.playback_time(core.interval.end), F(26744,1000)+offset)

    def test_nested_duplicate_and_changing_active_set(self):
        scan = self.parse(rows([(0,5,'A'),(1,1,'A'),(1,1,'A'),(1,1,'B'),(2,2,'B'),(2,1,'C')]))
        cores = overlap_cores(scan,self.clock)
        self.assertEqual([(c.interval.start,c.interval.end,len(c.voices)) for c in cores],
                         [(1000,2000,2),(2000,3000,3),(3000,4000,2)])
        region = SampleInterval(self.clock,0,6000)
        stats = coverage(scan,region)
        self.assertEqual((stats.uncovered,stats.simultaneous),(1000,3000))
        self.assertEqual({v.label:n for v,n in stats.per_voice.items()},{'A':5000,'B':3000,'C':1000})

    def test_silence_malformed_and_crash(self):
        with self.assertRaises(StageError):
            self.parse(rows([(1,-1,'A')]))
        with self.assertRaises(StageError):
            self.parse('SPEAKER clip 1')
        worker = Mock()
        scanner = SpeakerScanner(worker)
        file = AudioFile(self.src,Path('mix.wav'))
        track = PreparedTrack(self.clock,file,file)
        target = ExecutionTarget('amd-rocm','pci:test',0,Stage.DIARIZATION)
        worker.request.return_value = dict(versions=dict(pyannote='3',torch='2',hip='6'),
                                           elapsed_seconds=1,peak_allocated_bytes=2,rttm='')
        scan = scanner.scan(track,target,Path('.'))
        check_scan(self,scan,self.src)
        self.assertEqual(scan.turns,())
        worker.request.side_effect = StageError('worker crashed')
        with self.assertRaisesRegex(StageError,'crashed'):
            scanner.scan(track,target,Path('.'))
