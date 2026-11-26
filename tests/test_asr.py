import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from adapter_contracts import check_transcript
from yomisub.asr import WhisperJSON, parse_transcript
from yomisub.domain import AudioSource, ModelRun, TextSpan
from yomisub.models import get_model_path
from yomisub.ports import AudioFile, ExecutionTarget, Stage
from test_models import DownloadResponse


def example():
    return {"model":{"multilingual":True}, "transcription":[{"text":" 東京へ","tokens":[
        {"text":"[_BEG_]", "id":50364, "t_dtw":-1},
        {"text":" 東京","id":60,"offsets":{"from":300,"to":100},"p":0.8,"t_dtw":17},
        {"text":"へ","id":20}],"offsets":{"from":0,"to":600}}]}


class ASRTests(unittest.TestCase):
    def run_info(self, id):
        return ModelRun(id, "mix", "whisper.cpp", "hash", "model", (), "test", "id")

    def test_decode_local_timing_and_exact_offsets(self):
        seg = parse_transcript(example(), self.run_info('base')).segments[0]
        control, first, final = seg.pieces
        self.assertIsNone(control.span)
        self.assertIsNone(control.dtw_ticks)
        self.assertEqual((first.surface, first.span), (' 東京',TextSpan(0,3)))
        self.assertEqual((first.timing.start, first.timing.end, first.dtw_ticks), (300,100,17))
        self.assertIsNone(final.timing.end)
        alternate = example()
        alternate['transcription'][0]['text'] = '異なる読み'
        other = parse_transcript(alternate,self.run_info('alt')).segments[0]
        self.assertTrue(all(p.span is None for p in other.pieces))
        self.assertNotEqual(other.pieces[1].id, first.id)
        self.assertEqual(other.text,'異なる読み')

    def test_one_whole_mix_invocation_and_shared_contract(self):
        import json
        with TemporaryDirectory() as d:
            root = Path(d)
            source = AudioFile(AudioSource('mix','original',16000,160000), root/'whole.wav')
            target = ExecutionTarget('test','device',0,Stage.BASELINE_ASR)
            runner = Mock()
            def invoke(cli, args, target):
                self.assertEqual(args[args.index('-f')+1],str(source.path))
                Path(args[args.index('-of')+1]).with_suffix('.json').write_text(json.dumps(example()))
            runner.invoke.side_effect = invoke
            engine = WhisperJSON(runner)
            with patch.object(engine, '_resources',return_value=('cli','1.0',Path('medium.bin'))):
                actual = engine.transcribe(source,'ja','medium',target,root)
            check_transcript(self,actual,source.source)
            runner.invoke.assert_called_once()
            self.assertIn('-ojf',actual.run.options)

    def test_truncated_file_without_content_length_cannot_enter_verified_cache(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            expected = hashlib.sha1(b'complete').hexdigest()
            with patch('yomisub.models.urlopen',return_value=DownloadResponse(b'half',None)):
                with self.assertRaisesRegex(ValueError,'Incorrect Whisper checkpoint'):
                    get_model_path('large-v3',print,cache_dir=root,expected_sha1=expected)
            self.assertEqual(list(root.iterdir()),[])
            (root/'ggml-large-v3.bin').write_bytes(b'complete')
            with patch('yomisub.models.urlopen') as fetch:
                self.assertTrue(get_model_path('large-v3',print,cache_dir=root,expected_sha1=expected).is_file())
                fetch.assert_not_called()
