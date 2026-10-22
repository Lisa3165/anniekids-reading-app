import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import test_studio
from studio import JSONResponseError, StudioError, generate_lesson, parse_json_object
from template_flow import request_json


def reply(content, reason='stop'):
    return SimpleNamespace(choices=[SimpleNamespace(finish_reason=reason, message=SimpleNamespace(content=content))])


class JsonRecoveryTests(unittest.TestCase):
    def test_fenced_object_is_accepted_without_changing_strings(self):
        self.assertEqual(parse_json_object('```json\n{"quote":"Line\\nTwo"}\n```'), {'quote':'Line\nTwo'})

    def test_malformed_or_non_object_output_rejected(self):
        for content in ['{"x":', '[]', 'null', '', 'prose {"x":1}', '{"x":1} trailing']:
            with self.subTest(content=content), self.assertRaises(JSONResponseError):
                parse_json_object(content)

    def test_analysis_retries_json_and_still_checks_evidence(self):
        case = test_studio.StudioTests()
        case.setUp()
        with patch('studio.get_api_key', return_value='test'), patch('openai.OpenAI') as client:
            create = client.return_value.chat.completions.create
            create.side_effect = [reply('{bad json'), reply(json.dumps(case.result))]
            self.assertEqual(generate_lesson(case.material, case.chapters, 'A2'), case.result)
            self.assertEqual(create.call_count, 2)

    def test_pack_request_retries_json(self):
        with patch('template_flow.get_api_key', return_value='test'), patch('openai.OpenAI') as client:
            create = client.return_value.chat.completions.create
            create.side_effect = [reply(''), reply('{"ok":true}')]
            self.assertEqual(request_json('Return JSON', {}), {'ok':True})
            self.assertEqual(create.call_count, 2)

    def test_persistent_json_error_is_bounded(self):
        with patch('template_flow.get_api_key', return_value='test'), patch('openai.OpenAI') as client:
            create = client.return_value.chat.completions.create
            create.return_value = reply('{invalid')
            with self.assertRaises(StudioError): request_json('Return JSON', {})
            self.assertEqual(create.call_count, 3)

    def test_truncation_retries_with_smaller_output_instruction(self):
        with patch('template_flow.get_api_key', return_value='test'), patch('openai.OpenAI') as client:
            create = client.return_value.chat.completions.create
            create.side_effect = [reply('{', 'length'), reply('{"ok":true}')]
            self.assertEqual(request_json('Return JSON', {}), {'ok':True})
            self.assertIn('shorter', create.call_args.kwargs['messages'][-1]['content'])
