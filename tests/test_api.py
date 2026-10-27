"""Exercise real Flask routes with temporary files and synthetic timings."""
import copy
import csv
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

import app as web
import auth


def sample(seed=0):
    rng = np.random.default_rng(seed)
    result=[]; timestamp=0.0
    for key in auth.TARGET:
        result.extend([{'key':key,'action':'down','timestamp':timestamp},
                       {'key':key,'action':'up','timestamp':timestamp+float(rng.uniform(25,65))}])
        timestamp += float(rng.uniform(100,180))
    return result


class APITests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.data=self.root/'data';self.models=self.root/'models'
        for target,name,value in [(auth,'DATA_DIR',self.data),(auth,'MODEL_DIR',self.models),(web,'DATA_DIR',self.data)]:
            p=patch.object(target,name,value);p.start();self.addCleanup(p.stop)
        web.app.config.update(TESTING=True)
        self.client=web.app.test_client()

    def request(self,path='/collect',uid='userA',events=None):
        return self.client.post(path,json={'user_id':uid,'events':sample() if events is None else events})

    def test_homepage_is_read_from_project_not_current_directory(self):
        old=os.getcwd()
        try:
            os.chdir(self.root)
            self.assertIn(b'hello world',self.client.get('/').data)
        finally:os.chdir(old)

    def test_collect_and_status_have_expected_shape(self):
        self.assertEqual(self.request().json,{'status':'ok','total':1})
        self.assertEqual(self.request().json['total'],2)
        self.assertEqual(self.client.get('/status').json,{'userA':2})
        with (self.data/'userA.csv').open() as handle:
            self.assertEqual(len(next(csv.reader(handle))),31)

    def test_invalid_ids_cannot_create_files(self):
        for path in ['/collect','/auth']:
            for uid in ['../escape',r'..\escape','NUL','user.name',{},False,'x'*65]:
                with self.subTest(path=path,uid=uid):
                    response=self.request(path,uid)
                    self.assertEqual(response.status_code,400)
                    self.assertIn('error',response.json)
        self.assertFalse(self.data.exists())
        self.assertFalse((self.root/'escape.csv').exists())

    def test_malformed_bodies_return_json_without_writes(self):
        for path in ['/collect','/auth']:
            for body in [None,[],True,{}, {'user_id':'userA'}, {'user_id':'userA','events':[],'extra':1}]:
                response=self.client.post(path,data=__import__('json').dumps(body),content_type='application/json')
                self.assertEqual(response.status_code,400)
                self.assertIn('error',response.json)
            for body,kind in [('{','application/json'),('hello','text/plain')]:
                response=self.client.post(path,data=body,content_type=kind)
                self.assertEqual(response.status_code,400)
                self.assertIsInstance(response.json,dict)

    def test_wrong_text_and_invalid_timestamps_never_reach_storage(self):
        wrong=sample()
        for event,key in zip(wrong,[key for key in auth.TARGET[::-1] for _ in range(2)]):event['key']=key
        invalid=sample();invalid[0]['timestamp']='invalid'
        for path in ['/collect','/auth']:
            for data in [wrong,invalid]:
                self.assertEqual(self.request(path,events=data).status_code,400)
        self.assertFalse(self.data.exists())

    def test_request_size_limit_returns_json_413(self):
        response=self.client.post('/collect',data='x'*70000,content_type='application/json')
        self.assertEqual(response.status_code,413)
        self.assertIn('error',response.json)

    def test_missing_template_and_empty_build_are_clear(self):
        self.assertEqual(self.request('/auth').status_code,400)
        self.assertEqual(self.client.post('/build_templates').json['details'],{})

    def test_insufficient_samples_do_not_create_models(self):
        self.request()
        result=self.client.post('/build_templates').json
        self.assertEqual((result['built'],result['failed']),(0,1))
        self.assertFalse(self.models.exists())

    def test_full_synthetic_collect_build_auth_flow(self):
        for seed in range(40):self.assertEqual(self.request(events=sample(seed)).status_code,200)
        result=self.client.post('/build_templates').json
        self.assertEqual((result['built'],result['failed']),(1,0))
        response=self.request('/auth',events=sample(0))
        self.assertEqual(response.status_code,200)
        self.assertIsInstance(response.json['passed'],bool)
        self.assertTrue(np.isfinite(response.json['distance']))
        self.assertGreater(response.json['threshold'],0)

    def test_corrupt_csv_is_reported_without_partial_model(self):
        self.data.mkdir();(self.data/'userA.csv').write_text('not,a,sample\n')
        result=self.client.post('/build_templates')
        self.assertEqual(result.status_code,200)
        self.assertEqual(result.json['failed'],1)
        self.assertFalse(self.models.exists())

    def test_constant_samples_do_not_produce_zero_threshold_model(self):
        for _ in range(32):self.request()
        self.assertEqual(self.client.post('/build_templates').json['failed'],1)
        self.assertFalse(self.models.exists())

    def test_symlink_targets_are_not_read_or_written(self):
        self.data.mkdir();outside=self.root/'outside.csv';outside.write_text('original')
        try:(self.data/'userA.csv').symlink_to(outside)
        except OSError as exc:self.skipTest('Symlink creation unavailable: '+str(exc))
        self.assertEqual(self.request().status_code,400)
        self.assertEqual(outside.read_text(),'original')
        self.assertEqual(self.client.get('/status').json,{})
        self.assertEqual(self.client.post('/build_templates').json['details'],{})
        self.models.mkdir()
        (self.models/'userA_scaler.pkl').symlink_to(outside)
        self.assertEqual(self.request('/auth').status_code,400)

    def test_all_library_entrypoints_reject_unsafe_id(self):
        for function,args in [(auth.load_user_data,('../escape',)),(auth.build_template,('../escape',)),
                              (auth.authenticate_user,('../escape',np.ones(31)))]:
            with self.subTest(function=function.__name__),self.assertRaises(auth.InputError):function(*args)


if __name__=='__main__':unittest.main()
