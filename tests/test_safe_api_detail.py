import unittest
from types import SimpleNamespace
from unittest.mock import patch
from studio import api_error_message

class SafeDetailTests(unittest.TestCase):
    def test_parameter_details_preserved_credentials_redacted(self):
        error = SimpleNamespace(status_code=400, body={'error':{'message':'max_tokens must be <= 8192; sk-secret123; custom-secret'}}, request=SimpleNamespace(headers={'Authorization':'Bearer custom-secret'}))
        with patch('studio.get_api_key', return_value='custom-secret'):
            message = api_error_message(error)
        self.assertIn('max_tokens', message)
        self.assertNotIn('secret123', message)
        self.assertNotIn('custom-secret', message)

    def test_flat_body_and_missing_body(self):
        with patch('studio.get_api_key', return_value=None):
            self.assertIn('unknown model', api_error_message(SimpleNamespace(status_code=400, body={'message':'unknown model'})))
            self.assertIn('未提供', api_error_message(SimpleNamespace(status_code=400)))

    def test_non_400_does_not_show_response_message(self):
        message = api_error_message(SimpleNamespace(status_code=401, body={'message':'private response'}))
        self.assertNotIn('private response', message)
