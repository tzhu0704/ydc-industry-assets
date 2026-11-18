import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from education_utils import allowed_url,evidence_from_hits,validate_lesson,content_status,route_content,math_check,textbook_excerpt

class EducationTests(unittest.TestCase):
    def setUp(self):
        self.evidence=[dict(id='S1',url='https://openstax.org/a',text='The zero-product property states that if ab = 0 then a = 0 or b = 0.')]
        self.lesson=dict(answer_en='Explain factoring.',answer_zh='用因式分解。',claims=[dict(source_id='S1',quote='The zero-product property states',explanation_en='Supported text.',explanation_zh='依据原文。')],gaps=[])
    def test_valid_quote(self):
        self.assertEqual(validate_lesson(self.lesson,self.evidence),[])
    def test_fabricated_quote(self):
        self.lesson['claims'][0]['quote']='A fabricated rule that the source does not contain.'
        self.assertTrue(validate_lesson(self.lesson,self.evidence))
    def test_unknown_citation(self):
        self.lesson['claims'][0]['source_id']='S99'
        self.assertTrue(validate_lesson(self.lesson,self.evidence))
    def test_missing_answer_language(self):
        self.lesson['answer_zh']=''
        self.assertTrue(validate_lesson(self.lesson,self.evidence))
    def test_no_evidence_claims(self):
        self.lesson['claims']=[]
        self.assertTrue(validate_lesson(self.lesson,self.evidence))
    def test_domain_boundary(self):
        self.assertFalse(allowed_url('https://openstax.org.evil.test/a',['openstax.org']))
        self.assertTrue(allowed_url('https://assets.openstax.org/a',['openstax.org']))
        self.assertFalse(allowed_url('javascript:alert(1)',['openstax.org']))
    def test_short_excerpt_excluded(self):
        self.assertEqual(evidence_from_hits([dict(url='https://openstax.org/a',description='tiny')],['openstax.org']),[])
    def test_http200_empty_body(self):
        self.assertEqual(content_status(dict(markdown='   '))[0],'empty_body')
    def test_short_body(self):
        self.assertEqual(content_status(dict(markdown='short'))[0],'short_body')
    def test_blocked_body(self):
        self.assertEqual(content_status(dict(markdown='Verify you are human '+('x'*400)))[0],'blocked_body')
    def test_nested_body(self):
        self.assertEqual(content_status(dict(contents=dict(markdown='body '*100)))[0],'usable')
    def test_error_even_with_body(self):
        self.assertEqual(content_status(dict(error='pdf_too_large',markdown='body '*100))[0],'provider_error')
    def test_batch_matched_by_url(self):
        items=[dict(url='b',markdown='body '*100),dict(url='a',markdown='')]
        self.assertEqual([r['status'] for r in route_content(items,['a','b','c'])],['empty_body','usable','missing_item'])
    def test_duplicate_not_trusted(self):
        self.assertEqual(route_content([dict(url='a'),dict(url='a')],['a'])[0]['status'],'duplicate_item')
    def test_textbook_preamble_removed(self):
        text,meta=textbook_excerpt('cookie navigation\n# Lesson\nThe Calvin cycle follows light reactions.')
        self.assertTrue(text.startswith('# Lesson'))
        self.assertIn('Calvin cycle',text)
        self.assertFalse(meta['truncated'])
        self.assertGreater(meta['skipped_preamble_chars'],0)
    def test_textbook_truncation_disclosed(self):
        text,meta=textbook_excerpt('# Lesson\n'+'x'*500,limit=100)
        self.assertEqual(len(text),100)
        self.assertTrue(meta['truncated'])
    def test_math_verified_by_substitution(self):
        self.assertTrue(math_check([1,-5,6],[2,3]))
        self.assertFalse(math_check([1,-5,6],[2,4]))
        self.assertFalse(math_check([1,-5,6],[2,2]))
        self.assertFalse(math_check([0,-5,6],[2,3]))

if __name__=='__main__': unittest.main()

class FallbackIntegrationTests(unittest.TestCase):
    def test_empty_fulltext_uses_labeled_search_excerpts(self):
        from unittest.mock import patch
        from run import fulltext_lesson
        hit=dict(url='https://openstax.org/a',title='Scientific method',description='A hypothesis is a testable explanation. '+('Evidence ' * 20))
        with patch('run.fetch_search',return_value=dict(results=dict(web=[hit]))), \
             patch('run.fetch_contents',return_value=[dict(url=hit['url'],markdown='')]), \
             patch('run.teach',return_value=(dict(answer_en='Excerpt only',answer_zh='仅节选'),[])) as model, \
             patch('run.save') as save:
            fulltext_lesson('fixture','Teach the scientific method',{},['openstax.org'])
        self.assertIn('Full text unavailable',model.call_args.args[0])
        self.assertEqual(model.call_args.args[1][0]['text'],hit['description'])
        self.assertEqual(save.call_args.args[3]['retrieval_mode'],'search_excerpt_only')
        self.assertEqual(save.call_args.args[4]['contents_attempts'][0]['status'],'empty_body')

    def test_no_sources_does_not_call_model(self):
        from unittest.mock import patch
        from run import teach
        with patch('run.chat') as model:
            with self.assertRaises(RuntimeError):teach('Task',[],[])
        model.assert_not_called()

    def test_permanent_http_error_is_not_retried(self):
        from unittest.mock import patch
        import urllib.error
        from you_api import _request
        error=urllib.error.HTTPError('https://example.org',422,'Invalid parameter',{},None)
        with patch('you_api._api_key',return_value='example-placeholder'), \
             patch('urllib.request.urlopen',side_effect=error) as network,patch('you_api.time.sleep') as sleep:
            with self.assertRaises(urllib.error.HTTPError):_request('https://example.org',{})
        self.assertEqual(network.call_count,1)
        sleep.assert_not_called()

    def test_transient_http_error_retries_once(self):
        from unittest.mock import patch
        import urllib.error
        from you_api import _request
        error=urllib.error.HTTPError('https://example.org',503,'Unavailable',{},None)
        with patch('you_api._api_key',return_value='example-placeholder'), \
             patch('urllib.request.urlopen',side_effect=error) as network,patch('you_api.time.sleep') as sleep:
            with self.assertRaises(urllib.error.HTTPError):_request('https://example.org',{})
        self.assertEqual(network.call_count,2)
        sleep.assert_called_once_with(1)
