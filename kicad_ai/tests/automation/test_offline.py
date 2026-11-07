# SPDX-License-Identifier: GPL-3.0-or-later
import hashlib
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from kicad_ai.automation.local_model import LocalModel, LocalModelError
from kicad_ai.agents.architect_agent import ArchitectAgent
from kicad_ai.channels.ipc_client import KiCadIPCClient


class OfflineTests(unittest.TestCase):
    def test_cloud_keys_never_enable_remote_calls(self):
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'test', 'OPENAI_API_KEY': 'test',
                                    'EMB_MODEL_PATH': ''}, clear=True):
            with patch('socket.socket.connect', side_effect=AssertionError('Network forbidden')) as connect:
                with self.assertRaises(LocalModelError):
                    ArchitectAgent().analyze_requirements('temperature monitoring')
                connect.assert_not_called()

    def test_url_and_unc_models_rejected(self):
        for value in ('https://example.test/model.gguf', r'\\server\model.gguf', '//server/model.gguf'):
            with patch.dict(os.environ, {'EMB_MODEL_PATH': value}, clear=True):
                with self.assertRaises(LocalModelError):
                    LocalModel().load()

    def test_model_digest_and_local_constructor(self):
        with tempfile.TemporaryDirectory() as temp:
            model = Path(temp) / 'test.gguf'
            model.write_bytes(b'test weights, not a real model')
            engine = Mock()
            engine.create_chat_completion.return_value = {'choices': [{'finish_reason': 'stop', 'message': {
                'content': json.dumps({'summary': 'Need more detail', 'questions': ['What input voltage?']})}}]}
            constructor = Mock(return_value=engine)
            env = {'EMB_MODEL_PATH': str(model), 'EMB_MODEL_SHA256': '0' * 64}
            with patch.dict(os.environ, env, clear=True), patch.dict('sys.modules', {'llama_cpp': SimpleNamespace(Llama=constructor)}):
                with self.assertRaises(LocalModelError):
                    LocalModel().load()
                constructor.assert_not_called()
                os.environ['EMB_MODEL_SHA256'] = hashlib.sha256(model.read_bytes()).hexdigest()
                with patch('socket.socket.connect', side_effect=AssertionError('Network forbidden')) as connect:
                    result = LocalModel().questions({'function': 'monitor temperature'})
                    self.assertEqual(result['questions'], ['What input voltage?'])
                    connect.assert_not_called()
                self.assertEqual(constructor.call_args.kwargs['model_path'], str(model))

    def test_truncated_or_malformed_response_does_not_proceed(self):
        model = LocalModel()
        model.engine = Mock()
        model.engine.create_chat_completion.return_value = {'choices': [{'finish_reason': 'length'}]}
        with self.assertRaises(LocalModelError):
            model.questions({})
        model.engine.create_chat_completion.return_value = {'choices': [{'finish_reason': 'stop', 'message': {'content': '{"questions":"bad"}'}}]}
        with self.assertRaises(LocalModelError):
            model.questions({})

    def test_legacy_tcp_transport_disabled(self):
        with patch('socket.socket.connect', side_effect=AssertionError('Network forbidden')) as connect:
            client = KiCadIPCClient('remote.invalid')
            self.assertFalse(client.connect())
            self.assertEqual(client.reload_board('board')['status'], 'error')
            connect.assert_not_called()
