import copy
import json
import io
import unittest
from unittest.mock import patch
import generate_insights as app

class NarratorTests(unittest.TestCase):
    def test_paste_control_characters_are_rejected_locally(self):
        for key in ['\x16', 'sk-example\x16', '"sk-example"', 'sk-example text']:
            with self.assertRaisesRegex(ValueError, 'password box'):
                app.validate_key_input(key)
        self.assertEqual(app.validate_key_input(' sk-proj-example_abc-xyz '), 'sk-proj-example_abc-xyz')

    def setUp(self):
        self.metrics=json.loads((app.ROOT/'outputs'/'ai_metrics.json').read_text())
        self.facts=app.catalog(self.metrics)
        self.brief=app.preview(self.facts)

    def test_preview_has_traceable_formatted_facts(self):
        app.validate_brief(self.brief,self.facts)
        text=app.render(self.brief,self.facts,'preview')
        self.assertIn('895,507.22',text)
        self.assertIn('79.81%',text)
        self.assertIn('no API call made',text)

    def test_rejects_invented_numbers(self):
        self.brief['risks']=['Profit rose 35%.']
        with self.assertRaises(ValueError): app.validate_brief(self.brief,self.facts)

    def test_rejects_unknown_fact(self):
        self.brief['risks']=['Revenue {{f99999}}']
        with self.assertRaises(ValueError): app.validate_brief(self.brief,self.facts)

    def test_rejects_failed_validation(self):
        self.metrics['validation']['failures']=1
        with self.assertRaises(ValueError): app.catalog(self.metrics)

    def test_refusal_and_incomplete(self):
        for response in [{'status':'incomplete'}, {'status':'completed','output':[{'type':'message','content':[{'type':'refusal','refusal':'No'}]}]}]:
            with self.assertRaises(ValueError): app.extract_response(response)

    def test_extracts_message_after_reasoning(self):
        response={'status':'completed','output':[{'type':'reasoning'}, {'type':'message','content':[{'type':'output_text','text':json.dumps(self.brief)}]}]}
        self.assertEqual(app.extract_response(response),self.brief)

    def test_request_uses_structured_output_and_only_aggregate_input(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self,*args): pass
            def read(self): return b'{"status":"completed","output":[]}'
        with patch.object(app.urllib.request,'urlopen',return_value=Response()) as mocked:
            app.request_brief('configured-model','test-only-key','instructions',self.metrics,self.facts)
            request=mocked.call_args.args[0]; payload=json.loads(request.data)
            self.assertEqual(request.full_url,'https://api.openai.com/v1/responses')
            self.assertFalse(payload['store'])
            self.assertTrue(payload['text']['format']['strict'])
            self.assertNotIn('customer_unique_id',payload['input'])

    def test_api_error_explains_rejection_without_echoing_key(self):
        body=json.dumps({'error': {'message': 'Unsupported parameter: example. Key sk-test-secret'}}).encode()
        error=app.urllib.error.HTTPError('https://api.openai.com/v1/responses',400,'Bad Request',{},io.BytesIO(body))
        with patch.object(app.urllib.request,'urlopen',side_effect=error):
            with self.assertRaises(ValueError) as caught:
                app.request_brief('configured-model','sk-test-secret','instructions',self.metrics,self.facts)
        self.assertIn('Unsupported parameter: example',str(caught.exception))
        self.assertNotIn('sk-test-secret',str(caught.exception))

    def test_non_json_api_error_has_safe_fallback(self):
        error=app.urllib.error.HTTPError('https://api.openai.com/v1/responses',400,'Bad Request',{},io.BytesIO(b'<html>error</html>'))
        with patch.object(app.urllib.request,'urlopen',side_effect=error):
            with self.assertRaisesRegex(ValueError,'HTTP 400'):
                app.request_brief('configured-model','test-key','instructions',self.metrics,self.facts)

if __name__=='__main__': unittest.main()
