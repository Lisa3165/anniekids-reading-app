import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import httpx
from openai import BadRequestError, AuthenticationError
from studio import api_error_message
from template_flow import request_json

class ApiCompatibilityTests(unittest.TestCase):
    def test_status_diagnostics_do_not_echo_secrets(self):
        response = httpx.Response(401, request=httpx.Request('POST', 'https://api.deepseek.com/chat/completions'))
        error = AuthenticationError('private-key-must-not-appear', response=response, body=None)
        message = api_error_message(error)
        self.assertIn('401', message)
        self.assertNotIn('private-key', message)

    def test_deepseek_output_limit(self):
        reply = SimpleNamespace(choices=[SimpleNamespace(finish_reason='stop', message=SimpleNamespace(content=json.dumps({'ok':True})))])
        with patch('template_flow.get_api_key', return_value='test'), patch('openai.OpenAI') as client:
            client.return_value.chat.completions.create.return_value = reply
            self.assertEqual(request_json('Return JSON', {}), {'ok':True})
            self.assertEqual(client.return_value.chat.completions.create.call_args.kwargs['max_tokens'], 8192)
