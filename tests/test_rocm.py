import json
import os
from subprocess import CompletedProcess
import unittest
from unittest.mock import patch

from adapter_contracts import check_binding
from yomisub.ports import ExecutionTarget, Stage, StageError
from yomisub.rocm import AmdRocm, RocmWorker


class WorkerTests(unittest.TestCase):
    def setUp(self):
        self.client = RocmWorker('test-python', 'weights')
        self.target = ExecutionTarget('amd-rocm','pci:0000:01:00.0',0,Stage.DIARIZATION)
        self.run = self.enterContext(patch('yomisub.rocm.subprocess.run'))

    def reply(self, **value):
        self.run.return_value = CompletedProcess([],0,json.dumps({'version':1,**value}),'secret in stderr')

    def test_missing_interpreter_bad_protocol_and_inaccessible_weights(self):
        self.run.side_effect = FileNotFoundError('secret')
        with self.assertRaisesRegex(StageError,'Python 3.12'):
            self.client.request('devices')
        self.run.side_effect = None
        self.reply(version=2)
        with self.assertRaisesRegex(StageError,'matching'):
            self.client.request('devices')
        self.reply(error='weights')
        with self.assertRaisesRegex(StageError,'weights.py') as caught:
            self.client.request('probe',self.target)
        self.assertNotIn('secret',str(caught.exception))

    def test_effective_selection_and_optional_capability_are_independent(self):
        dev = self.target.physical_id
        self.reply(value={'devices':[{'id':dev,'name':'Radeon','index':0}]})
        check_binding(self,AmdRocm(self.client),Stage.DIARIZATION,dev)
        self.reply(error='weights')
        with self.assertRaises(StageError):
            self.client.request('probe',ExecutionTarget('amd-rocm',dev,0,Stage.SEPARATION))
        self.reply(value={'stage':'diarization','device':dev})
        with patch.dict(os.environ,HF_TOKEN='secret',ROCR_VISIBLE_DEVICES='0'):
            self.assertEqual(self.client.request('probe',self.target)['device'],dev)
        env = self.run.call_args.kwargs['env']
        self.assertNotIn('HF_TOKEN',env)
        self.assertEqual(env['ROCR_VISIBLE_DEVICES'],'0')
        self.reply(value={'stage':'diarization','device':'wrong'})
        with self.assertRaisesRegex(StageError,'PCI'):
            self.client.request('probe',self.target)
