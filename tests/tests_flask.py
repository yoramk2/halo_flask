from __future__ import print_function

import json
import os

from faker import Faker
from flask import Flask, request
from flask_restful import Api
from nose.tools import eq_


from halo_flask.flask.utilx import Util, status
from halo_flask.flask.mixinx import AbsBaseMixinX,TestMixinX
from halo_flask.flask.viewsx import TestLinkX
from halo_flask.exceptions import ApiError
from halo_flask.logs import log_json
from halo_flask import saga
from halo_flask.providers.cloud.aws.models import AbsModel
from halo_flask.apis import ApiTest,GoogleApi
import unittest



fake = Faker()
app = Flask(__name__)
api = Api(app)

from halo_flask.response import HaloResponse
class T1(AbsBaseMixinX):
    def process_get(self, request, vars):
        ret = HaloResponse()
        ret.payload = {'data': {'test2': 'good'}}
        ret.code = 200
        ret.headers = []
        return ret

    def process_delete(self, request, vars):
        ret = HaloResponse()
        ret.payload = {'data': {'test2': 'good'}}
        ret.code = 500
        ret.headers = []
        return ret

class T2(TestMixinX):
    pass

class T3(TestLinkX):
    pass

from halo_flask.flask.viewsx import PerfLinkX as PerfLink
class S1(PerfLink):
    pass


class TestUserDetailTestCase(unittest.TestCase):
    """
    Tests /users detail operations.
    """

    def setUp(self):
        #self.url = 'http://127.0.0.1:8000/?abc=def'
        #self.perf_url = 'http://127.0.0.1:8000/perf'
        #app.config['TESTING'] = True
        #app.config['WTF_CSRF_ENABLED'] = False
        #app.config['DEBUG'] = False
        #app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' +  os.path.join(app.config['BASEDIR'], TEST_DB)
        #self.app = app#.test_client()
        app.config.from_pyfile('../settings.py')
        self.t1 = T1()
        self.t2 = T2()
        self.t3 = T3()


    def test_get_request_returns_a_given_string(self):
        with app.test_request_context(method='GET', path='/?abc=def'):
            response = self.t1.process_get(request, {})
            print("response=" + str(response.payload))
            eq_(response.code, status.HTTP_200_OK)
            eq_(response.payload, {'data': {'test2': 'good'}})

    def test_api_request_returns_a_given_string(self):
        with app.test_request_context(method='GET', path='/?a=b'):
            api = ApiTest(Util.get_req_context(request))
            timeout = Util.get_timeout(request)
            try:
                response = api.get(timeout)
            except ApiError as e:
                #eq_(e.status_code, status.HTTP_403_NOT_FOUND)
                eq_(e.__class__.__name__,"CircuitBreakerError")

    def test_api_request_returns_a_given_string1(self):
        with app.test_request_context(method='GET', path='/?a=b'):
            api = GoogleApi(Util.get_req_context(request))
            timeout = Util.get_timeout(request)
            try:
                response = api.get(timeout)
            except ApiError as e:
                #eq_(e.status_code, status.HTTP_403_NOT_FOUND)
                eq_(e.__class__.__name__,"CircuitBreakerError")

    def test_api_request_returns_a_fail(self):
        with app.test_request_context(method='GET', path='/?a=b'):
            api = ApiTest(Util.get_req_context(request))
            api.url = api.url + "/lgkmlgkhm??l,mhb&&,g,hj "
            timeout = Util.get_timeout(request)
            try:
                response = api.get(timeout)
            except ApiError as e:
                eq_(e.status_code, status.HTTP_404_NOT_FOUND)
                #eq_(e.__class__.__name__,"CircuitBreakerError")

    def test_send_event(self):
        with app.test_request_context(method='GET', path='/?a=b'):
            from halo_flask.events import AbsBaseEvent
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
        with app.test_request_context(method='GET', path='/?a=b'):
            os.environ['DEBUG_LOG'] = 'true'
            flag = 'false'
            for i in range(0, 80):
                ret = Util.get_system_debug_enabled()
                print(ret)
                if ret == 'true':
                    flag = ret
            eq_(flag, 'true')

    def test_debug_enabled(self):
        header = {'HTTP_DEBUG_LOG_ENABLED': 'true'}
        with app.test_request_context(method='GET', path='/?a=b', headers=header):
            ret = Util.get_req_context(request)
            eq_(ret["debug-log-enabled"], 'true')

    def test_json_log(self):
        import traceback
        header = {'HTTP_DEBUG_LOG_ENABLED': 'true'}
        with app.test_request_context(method='GET', path='/?a=b', headers=header):
            req_context = Util.get_req_context(request)
            try:
                raise Exception("test it")
            except Exception as e:
                e.stack = traceback.format_exc()
                ret = log_json(req_context, {"abc": "def"}, err=e)
                print(str(ret))
                eq_(ret["debug-log-enabled"], 'true')

    def test_get_request_with_debug(self):
        header = {'HTTP_DEBUG_LOG_ENABLED': 'true'}
        with app.test_request_context(method='GET', path='/?a=b', headers=header):
            ret = Util.get_debug_enabled(request)
            eq_(ret, 'true')

    def test_debug_event(self):
        event = {'debug-log-enabled': 'true'}
        ret = Util.get_correlation_from_event(event)
        eq_(Util.event_req_context["debug-log-enabled"], 'true')
        ret = Util.get_correlation_from_event(event)
        eq_(ret["debug-log-enabled"], 'true')

    def test_pref_mixin(self):
        with app.test_request_context(method='GET', path='/perf'):
            response = self.t1.process_get(request, {})
            eq_(response.code, status.HTTP_200_OK)

    def test_model_get_pre(self):
        from pynamodb.attributes import UTCDateTimeAttribute, UnicodeAttribute
        class TestModel(AbsModel):
            class Meta:
                table_name = 'tbl-upc-53-loc'
                host = "http://localhost:8600"

            created_on = UTCDateTimeAttribute(null=False)
            pkey = UnicodeAttribute(hash_key=True)

        m = TestModel()
        a, b = m.get_pre()
        eq_(a, "pkey")

    def test_model_get_pre_val(self):
        from pynamodb.attributes import UTCDateTimeAttribute, UnicodeAttribute
        class TestModel(AbsModel):
            class Meta:
                table_name = 'tbl-upc-53-loc'
                host = "http://localhost:8600"

            created_on = UTCDateTimeAttribute(null=False)
            pkey = UnicodeAttribute(hash_key=True)

        m = TestModel()
        m.pkey = "123"
        a, b = m.get_pre_val()
        eq_(a, "123")

    def test_model_idem_id(self):
        from pynamodb.attributes import UTCDateTimeAttribute, UnicodeAttribute
        class TestModel(AbsModel):
            class Meta:
                table_name = 'tbl-upc-53-loc'
                host = "http://localhost:8600"

            created_on = UTCDateTimeAttribute(null=False)
            pkey = UnicodeAttribute(hash_key=True)

        m = TestModel()
        m.pkey = "456"
        ret = m.get_idempotent_id("123")
        eq_(ret, "8b077e79d995ac82ea9217c7b34c8b57")

    def test_model_idem_db(self):
        from pynamodb.attributes import UTCDateTimeAttribute, UnicodeAttribute
        from pynamodb.exceptions import PutError
        import datetime
        import uuid
        class TestModel(AbsModel):
            class Meta:
                table_name = 'tbl-upc-53-tst'
                host = "http://localhost:8600"

            created_on = UTCDateTimeAttribute(null=False)
            pkey = UnicodeAttribute(hash_key=True)

        if not TestModel.exists():
            TestModel.create_table(read_capacity_units=1, write_capacity_units=1)
        m = TestModel()
        m.pkey = str(uuid.uuid4())
        m.created_on = datetime.datetime.utcnow()
        request_id = str(uuid.uuid4())
        ret = m.save(request_id)
        try:
            ret1 = m.save(request_id)
        except PutError as e:
            print(str(e))
            ret1 = ret
        eq_(ret, ret1)

    def test_load_saga(self):
        with open("saga.json") as f:
            jsonx = json.load(f)
        with open("schema.json") as f1:
            schema = json.load(f1)
        sagax = saga.load_saga("test", jsonx, schema)
        eq_(len(sagax.actions), 6)

    def test_run_saga(self):
        with app.test_request_context(method='PUT', path="/"):
            response = self.t2.process_put(request, {})
            eq_(response.code, status.HTTP_200_OK)

    def test_rollback_saga(self):
        with app.test_request_context(method='POST', path="/"):
            response = self.t2.process_post(request, {})
            eq_(response.code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_ssm_aws(self):  # @TODO
        header = {'HTTP_HOST': '127.0.0.2'}
        with app.test_request_context(method='GET', path='/?a=b', headers=header):
            from halo_flask.ssm import set_app_param_config
            set_app_param_config("AWS", "124")
            from halo_flask.ssm import get_app_config
            config = get_app_config("AWS")
            eq_(config.get_param("halo_base")["url"], 'https://127.0.0.1:8000/loc')

    def test_ssm_onperm(self):  # @TODO
        header = {'HTTP_HOST': '127.0.0.2'}
        app.config['SSM_TYPE'] = "ONPREM"
        app.config['ONPREM_SSM_CLASS_NAME'] = 'OnPremClient'
        app.config['ONPREM_SSM_MODULE_NAME'] = 'halo_flask.providers.ssm.onprem_ssm_client'
        with app.test_request_context(method='GET', path='/?a=b', headers=header):
            from halo_flask.ssm import set_app_param_config
            set_app_param_config("AWS", "124")
            from halo_flask.ssm import get_app_config
            config = get_app_config("ONPREM")
            eq_(config.get_param('halo_base')["url"], 'https://127.0.0.1:8000/loc')

    def test_error_handler(self):
        with app.test_request_context(method='DELETE', path='/perf'):
            response = self.t1.process_delete(request, {})
            #print("x="+str(response.content))
            #print("ret=" + str(json.loads(response.content)))
            #eq_(json.loads(response.content)['error']['error_message'], 'test error msg')
            eq_(response.code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_timeout(self):
        with app.test_request_context(method='GET', path='/?a=b'):
            os.environ["AWS_LAMBDA_FUNCTION_NAME"] = "halo_flask"
            timeout = Util.get_timeout(request)
            eq_(timeout, 3)







