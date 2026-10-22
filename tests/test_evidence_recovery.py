import copy
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import test_studio
from studio import EvidenceError, StudioError, generate_lesson
from template_flow import analyze_book


def reply(result):
    return SimpleNamespace(choices=[SimpleNamespace(finish_reason='stop', message=SimpleNamespace(content=json.dumps(result)))])


class EvidenceRecoveryTests(unittest.TestCase):
    def fixture(self):
        case = test_studio.StudioTests()
        case.setUp()
        invalid = copy.deepcopy(case.result)
        invalid['chapters'][0]['questions'][0]['evidence'] = 'This sentence was invented.'
        return case, invalid

    def test_bad_quote_repaired_then_fully_validated(self):
        case, invalid = self.fixture()
        with patch('studio.get_api_key', return_value='test'), patch('openai.OpenAI') as client:
            create = client.return_value.chat.completions.create
            create.side_effect = [reply(invalid), reply(case.result)]
            self.assertEqual(generate_lesson(case.material, case.chapters, 'A2'), case.result)
            self.assertEqual(create.call_count, 2)
            self.assertIn('Quotation validation failed', create.call_args.kwargs['messages'][-1]['content'])

    def test_persistent_bad_quotes_never_accepted(self):
        case, invalid = self.fixture()
        with patch('studio.get_api_key', return_value='test'), patch('openai.OpenAI') as client:
            create = client.return_value.chat.completions.create
            create.return_value = reply(invalid)
            with self.assertRaises(EvidenceError):
                generate_lesson(case.material, case.chapters, 'A2')
            self.assertEqual(create.call_count, 3)

    def test_resume_only_uses_successful_units(self):
        chapters = [{'title':'One', 'text':'First story.'}, {'title':'Two', 'text':'Second story.'}]
        checkpoint = {}
        with patch('template_flow.generate_lesson', side_effect=[{'ok':1}, StudioError('failed')]):
            with self.assertRaises(StudioError):
                analyze_book({'title':'Book'}, chapters, 'A2', lambda *a: None, checkpoint)
        with patch('template_flow.generate_lesson', return_value={'ok':2}) as generate:
            notes = analyze_book({'title':'Book'}, chapters, 'A2', lambda *a: None, checkpoint)
            self.assertEqual(notes, [{'ok':1}, {'ok':2}])
            self.assertEqual(generate.call_count, 1)
            self.assertEqual(generate.call_args.args[1][0]['title'], 'Two')

    def test_changed_source_does_not_reuse_checkpoint(self):
        checkpoint = {}
        with patch('template_flow.generate_lesson', return_value={'ok':1}) as generate:
            for text in ['Original text.', 'Changed text.']:
                analyze_book({'title':'Book'}, [{'title':'One', 'text':text}], 'A2', lambda *a: None, checkpoint)
            self.assertEqual(generate.call_count, 2)
