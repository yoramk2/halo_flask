from __future__ import print_function

import json
import os

from faker import Faker
from nose.tools import eq_
from rest_framework import status
from rest_framework.test import APITestCase

fake = Faker()

import django

# from django.conf import settings
# settings.configure(default_settings=settings, DEBUG=True)
django.setup()


class TestUserDetailTestCase(APITestCase):
    """
    Tests /users detail operations.
    """

    def setUp(self):
        self.url = 'http://127.0.0.1:8000/?abc=def'

    def mock_request(self, type, header={}):
        from django.test.client import RequestFactory
        rf = RequestFactory()
        if type == 'GET':
            get_request = rf.get('/hello/', **header)
            return get_request
        else:
            post_request = rf.post('/submit/', {'foo': 'bar'}, **header)
            return post_request

    def test_get_request_returns_a_given_string(self):
        response = self.client.get(self.url)
        eq_(response.status_code, status.HTTP_200_OK)
        eq_(json.loads(response.content), {"test": "good"})

    def test_post_request_returns_a_given_code(self):
        payload = {'first_name': 'new_first_name'}
        response = self.client.post(self.url, payload)
        eq_(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put_request_updates_a_code(self):
        payload = {'first_name': 'new_first_name'}
        response = self.client.put(self.url, payload)
        eq_(response.status_code, status.HTTP_400_BAD_REQUEST)
        # print("response " + str(response))
        # eq_(response.data, 'new_first_name')

    def test_api_request_returns_a_given_string(self):
        from halolib.apis import ApiTest
        api = ApiTest('123')
        response = api.get()
        print("google response " + str(response.content))
        eq_(response.status_code, status.HTTP_200_OK)

    def test_api_request_returns_a_fail(self):
        from halolib.exceptions import ApiError
        from halolib.apis import ApiTest
        api = ApiTest('123')
        api.url = api.url + "/lgkmlgkhm??l,mhb&&,g,hj "
        try:
            response = api.get()
        except ApiError as e:
            eq_(e.status_code, status.HTTP_404_NOT_FOUND)

    def test_send_event(self):
        from halolib.events import AbsBaseEvent
        class Event1Event(AbsBaseEvent):
            target_service = 'func1'
            key_name = 'def'
            key_val = '456'

        event = Event1Event()
        dict = {"name": "david"}
        response = event.send_event(dict)
        print("event response " + str(response))
        eq_(response, 'sent event')

    def test_system_debug_enabled(self):
        from halolib.util import Util
        os.environ['DEBUG_LOG'] = 'true'
        flag = 'false'
        for i in range(0, 60):
            ret = Util.get_system_debug_enabled(self.mock_request('GET'))
            # print(ret)
            if ret == 'true':
                flag = ret
        eq_(flag, 'true')

    def test_debug_enabled(self):
        from halolib.util import Util
        header = {'HTTP_DEBUG_LOG_ENABLED': 'true'}
        req = self.mock_request('GET', header)
        ret = Util.get_req_context(req)
        eq_(ret["debug-log-enabled"], 'true')

    def test_json_log(self):
        from halolib.logs import log_json
        from halolib.util import Util
        from halolib.exceptions import ApiError
        import traceback
        import logging
        logger = logging.getLogger(__name__)
        header = {'HTTP_DEBUG_LOG_ENABLED': 'true'}
        req = self.mock_request('GET', header)
        req_context = Util.get_req_context(req)
        err = ApiError("test it")
        try:
            e = exception()
        except Exception as e:
            err.stack = traceback.format_exc()
        ret = log_json(logger, req_context, logging.DEBUG, "test", {"abc": "def"}, err=err)
        eq_(ret["debug-log-enabled"], 'true')

    def test_get_request_with_debug(self):
        header = {'HTTP_DEBUG_LOG_ENABLED': 'true'}
        response = self.client.get(self.url, **header)
        eq_(response.status_code, status.HTTP_200_OK)
        eq_(json.loads(response.content), {"test": "good"})
