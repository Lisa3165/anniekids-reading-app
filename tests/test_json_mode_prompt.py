import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from template_flow import request_json

class JsonModePromptTests(unittest.TestCase):
    def test_every_json_mode_call_has_explicit_keyword_even_on_retry(self):
        valid = SimpleNamespace(choices=[SimpleNamespace(finish_reason='stop', message=SimpleNamespace(content=json.dumps({'framework':'Plan'})))])
        invalid = SimpleNamespace(choices=[SimpleNamespace(finish_reason='stop', message=SimpleNamespace(content='broken'))])
        with patch('template_flow.get_api_key', return_value='test'), patch('openai.OpenAI') as client:
            create = client.return_value.chat.completions.create
            create.side_effect = [invalid, valid]
            result = request_json('Return a teaching framework.', {'title':'Book'})
            self.assertEqual(result['framework'], 'Plan')
            for call in create.call_args_list:
                self.assertEqual(call.kwargs['response_format'], {'type':'json_object'})
                self.assertIn('json', call.kwargs['messages'][0]['content'])

    def test_framework_and_summary_paths_use_shared_json_requirement(self):
        from template_flow import make_framework
        note = {'analysis':{}, 'chapters':[{'title':'One','big_question':'Why?', 'questions':[], 'task':'Read','teacher_notes':'Read'}]}
        response = SimpleNamespace(choices=[SimpleNamespace(finish_reason='stop', message=SimpleNamespace(content='{"framework":"Plan"}'))])
        with patch('template_flow.get_api_key', return_value='test'), patch('openai.OpenAI') as client:
            client.return_value.chat.completions.create.return_value = response
            self.assertEqual(make_framework({'title':'Book'}, [note], {}), 'Plan')
            messages = client.return_value.chat.completions.create.call_args.kwargs['messages']
            self.assertIn('json', messages[0]['content'])
