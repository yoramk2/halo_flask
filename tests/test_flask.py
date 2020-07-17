from __future__ import print_function

import json
import os

from faker import Faker
from flask import Flask, request
from flask_restful import Api
from nose.tools import eq_
from jsonpath_ng import jsonpath, parse
from halo_flask.base_util import BaseUtil
from halo_flask.circuitbreaker import CircuitBreakerError
from halo_flask.flask.utilx import Util
from halo_flask.errors import status
from halo_flask.flask.mixinx import AbsApiMixinX,PerfMixinX
from halo_flask.flask.viewsx import PerfLinkX
from halo_flask.exceptions import ApiError,HaloMethodNotImplementedException
from halo_flask.logs import log_json
from halo_flask import saga
from halo_flask.const import HTTPChoice
from halo_flask.apis import AbsRestApi, AbsSoapApi, SoapResponse, ApiMngr  # CnnApi,GoogleApi,TstApi
from halo_flask.flask.viewsx import Resource,AbsBaseLinkX
from halo_flask.request import HaloContext
from halo_flask.apis import load_api_config
from halo_flask.ssm import set_app_param_config,get_app_param_config,set_host_param_config
from halo_flask.flask.viewsx import load_global_data
from halo_flask.security import HaloSecurity
import unittest

#6,7,9923,9941 failing

fake = Faker()
app = Flask(__name__)
api = Api(app)

from halo_flask.request import HaloRequest
from halo_flask.response import HaloResponse


##################################### test #########################
"""
###performance testing###
npm install -g artillery
artillery -V
artillery quick --count 10 -n 20 http://127.0.0.1:5000/loc/info
artillery run artilery.yml
config:
  target: 'http://127.0.0.1:5000'
  phases:
    - duration: 60
      arrivalRate: 20
  defaults:
    headers:
      x-my-service-auth: '987401838271002188298567'
scenarios:
  - flow:
    - get:
        url: "/loc/info"

"""
from halo_flask.circuitbreaker import CircuitBreaker,CircuitBreakerMonitor
from requests.exceptions import RequestException
class MyCircuitBreaker(CircuitBreaker):
    FAILURE_THRESHOLD = 3
    RECOVERY_TIMEOUT = 60
    EXPECTED_EXCEPTION = RequestException

class CnnApi(AbsRestApi):
    name = 'Cnn'

    @MyCircuitBreaker()
    def do_cb_request(self, method, url, timeout, data=None, headers=None, auth=None):
        return super(CnnApi,self).do_cb_request(method, url, timeout, data=None, headers=None, auth=None)

class GoogleApi(AbsRestApi):
    name = 'Google'

class TstApi(AbsRestApi):
    name = 'Tst'

    @MyCircuitBreaker()
    def do_cb_request(self, method, url, timeout, data=None, headers=None, auth=None):
        return super(TstApi, self).do_cb_request(method, url, timeout, data=None, headers=None, auth=None)

class Tst2Api(AbsSoapApi):
    name = 'Tst2'

    def do_method1(self,timeout, data=None, headers=None, auth=None):
        if not data:
            data = {"first":"one",'second':"two"}
        soap_ret = self.client.service.Method1(data["first"], data['second'])
        print(str(soap_ret))
        content = json.dumps({"msg":soap_ret})
        response = SoapResponse(content,{},200)
        return response

class Tst3Api(AbsRestApi):
    name = 'Tst3'

class Tst4Api(AbsRestApi):
    name = 'Tst4'

class AwsApi(AbsRestApi):
    name = 'halo-webapp-service-dev-halo_webapp'

class PrimoServiceApi(AbsRestApi):
    name='PrimoService-dev-hello'

from halo_flask.flask.mixinx import AbsBaseMixinX,AbsApiMixinX,AbsDbMixin
class DbTest(AbsApiMixinX):
    pass
class DbMixin(AbsDbMixin):
    pass


class Sec(HaloSecurity):
    def get_secret(self):
        return '12345'
    def get_user_roles(self,user):
        return ['tst']

#API_LIST = {"Google": 'tests.test_flask.GoogleApi', "Cnn": "tests.test_flask.CnnApi","Tst":"tests.test_flask.TstApi","Tst2":"tests.test_flask.Tst2Api","Tst3":"tests.test_flask.Tst3Api","Tst4":"tests.test_flask.Tst4Api"}

#ApiMngr.set_api_list(API_LIST)

class A1(AbsApiMixinX):

    def set_back_api(self,halo_request, foi=None):
        if not foi:#not in seq
            if not halo_request.sub_func:#not in bq
                if halo_request.request.method == HTTPChoice.delete.value:
                    return ApiMngr.get_api_instance("Cnn",halo_request.context,HTTPChoice.delete.value)
                    #return CnnApi(halo_request.context,HTTPChoice.delete.value)
        return super(A1,self).set_back_api(halo_request,foi)

    def extract_json(self,halo_request,api, back_response, seq=None):
        if seq == None:#no event
            if halo_request.request.method == HTTPChoice.get.value:#method type
                return {"tst_get":"good"}
            if halo_request.request.method == HTTPChoice.delete.value:#method type
                return {"tst_delete":"good"}
        else:#in event
            if halo_request.request.method == HTTPChoice.put.value:#method type
                if seq == '1':
                    return {"tst_put":"good1"}
                if seq == '2':
                    return {"tst_put":"good2"}
            if halo_request.request.method == HTTPChoice.post.value:#method type
                if seq == '1':
                    return {"tst_post":"good1"}
                if seq == '2':
                    return {"tst_post":"good2"}
            if halo_request.request.method == HTTPChoice.patch.value:#method type
                return {"tst_patch":"good"}

class A3(AbsApiMixinX):

    def do_operation(self, halo_request):
        # 1. validate input params
        self.validate_req(halo_request)
        # 2. run pre conditions
        self.validate_pre(halo_request)
        # 3. processing engine abc
        # 4. Build the payload target response structure which is Compliant
        payload = self.create_resp_payload(halo_request, {})
        # 5. setup headers for reply
        headers = self.set_resp_headers(halo_request, halo_request.request.headers)
        # 6. build json and add to halo response
        halo_response = self.create_response(halo_request, payload, headers)
        # 7. post condition
        self.validate_post(halo_request, halo_response)
        # 8. do filter
        self.do_filter(halo_request,halo_response)
        # 9. return json response
        return halo_response

    def do_filter(self, halo_request, halo_response):  #
        request_filter = self.get_request_filter(halo_request)
        request_filter.do_filter(halo_request, halo_response)

class A2(Resource, A1, AbsBaseLinkX):

    def set_api_data(self,halo_request,api, seq=None, dict=None):
        if halo_request.request.method == HTTPChoice.post.value:
            if seq == '1':
                return {}
            if seq == '3':
                return {}
        ret = super(A2,self).set_api_data(halo_request,api, seq, dict)
        return ret

    def set_api_headers_deposit(self,halo_request,api, seq=None, dict=None):
        return super(A2,self).set_api_headers(halo_request,api, seq, dict)

    def set_api_vars_deposit(self,halo_request,api, seq=None, dict=None):
        return super(A2,self).set_api_vars(halo_request,api, seq, dict)

    def set_api_auth_deposit(self,halo_request,api, seq=None, dict=None):
        return super(A2,self).set_api_auth(halo_request,api, seq, dict)

    def set_api_data_deposit(self,halo_request,api, seq=None, dict=None):
        ret = super(A2,self).set_api_data(halo_request,api, seq, dict)
        return ret

    def execute_api_deposit(self,halo_request, back_api, back_vars, back_headers, back_auth, back_data=None, seq=None, dict=None):
        return super(A2,self).execute_api(halo_request, back_api, back_vars, back_headers, back_auth, back_data, seq, dict)

    def extract_json_deposit(self,halo_request,api, back_response, seq=None):
        if seq == None:#no event
            if halo_request.request.method == HTTPChoice.get.value:#method type
                return {"tst_get_deposit":"good"}
            if halo_request.request.method == HTTPChoice.delete.value:#method type
                return {"tst_delete_deposit":"good"}
        else:#in event
            if halo_request.request.method == HTTPChoice.put.value:#method type
                if seq == '1':
                    return {"tst_put_deposit":"good1"}
                if seq == '2':
                    return {"tst_put_deposit":"good2"}
            if halo_request.request.method == HTTPChoice.post.value:#method type
                if seq == '1':
                    return {"tst_post_deposit":"good1"}
                if seq == '2':
                    return {"tst_post_deposit":"good2"}
            if halo_request.request.method == HTTPChoice.patch.value:#method type
                return {"tst_patch_deposit":"good"}

    def create_resp_payload(self, halo_request, dict_back_json):
        if dict_back_json:
            dict_back_json = {
              "employees": [
                {
                  "id": 1,
                  "name": "Pankaj",
                  "salary": "10000"
                },
                {
                  "name": "David",
                  "salary": "5000",
                  "id": 2
                }
              ]
            }
            dict_back_json1 = {
	"store": {
		"book": [{
			"category": "reference",
			"author": "Nigel Rees",
			"title": "Sayings of the Century",
			"price": 8.95
		}, {
			"category": "fiction",
			"author": "Evelyn Waugh",
			"title": "Sword of Honour",
			"price": 12.99
		}, {
			"category": "fiction",
			"author": "Herman Melville",
			"title": "Moby Dick",
			"isbn": "0-553-21311-3",
			"price": 8.99
		}, {
			"category": "fiction",
			"author": "J. R. R. Tolkien",
			"title": "The Lord of the Rings",
			"isbn": "0-395-19395-8",
			"price": 22.99
		}],
		"bicycle": {
			"color": "red",
			"price": 19.95
		}
	},
	"expensive": 10
}
            return  super(A2,self).create_resp_payload(halo_request, dict_back_json)

class A4(A2):
    secure = True

class A5(AbsApiMixinX):
    secure = True

class A6(Resource, A5, AbsBaseLinkX):
    pass

class P1(PerfMixinX):
    pass

class P2(PerfLinkX):
    pass

from halo_flask.flask.filter import RequestFilter,RequestFilterClear
class TestFilter(RequestFilter):
    def augment_event_with_headers_and_data(self,event, halo_request,halo_response):
        event.put(HaloContext.items.get(HaloContext.CORRELATION), halo_request.request.headers[HaloContext.items.get(HaloContext.CORRELATION)])
        return event

class TestRequestFilterClear(RequestFilterClear):
    def run(self,event):
        print("insert_events_to_repository " + str(event.serialize()))


class CAContext(HaloContext):
    TESTER = "TESTER"

    HaloContext.items[TESTER] = "x-tester-id"

def get_host_name():
    if 'HALO_HOST' in os.environ:
        return os.environ['HALO_HOST']
    else:
        return 'HALO_HOST'

class TestUserDetailTestCase(unittest.TestCase):
    """
    Tests /users detail operations.
    """
    def start(self):
        from halo_flask.const import LOC
        app.config['ENV_TYPE'] = LOC
        app.config['SSM_TYPE'] = "AWS"
        #app.config['PROVIDER'] = "AWS"
        app.config['FUNC_NAME'] = "FUNC_NAME"
        #app.config['API_CONFIG'] = None
        app.config['AWS_REGION'] = 'us-east-1'
        #app.config['CIRCUIT_BREAKER'] = False
        with app.test_request_context(method='GET', path='/?abc=def'):
            try:
                load_api_config(app.config['ENV_TYPE'], app.config['SSM_TYPE'], app.config['FUNC_NAME'],
                                app.config['API_CONFIG'])
            except Exception as e:
                eq_(e.__class__.__name__, "NoApiClassException")

    def setUp(self):
        #self.url = 'http://127.0.0.1:8000/?abc=def'
        #self.perf_url = 'http://127.0.0.1:8000/perf'
        #app.config['TESTING'] = True
        #app.config['WTF_CSRF_ENABLED'] = False
        #app.config['DEBUG'] = False
        #app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' +  os.path.join(app.config['BASEDIR'], TEST_DB)
        #self.app = app#.test_client()
        #app.config.from_pyfile('../settings.py')
        app.config.from_object('settings')
        self.a1 = A1()
        self.a2 = A2()
        self.a3 = A3()
        self.a4 = A4()
        self.a5 = A5()
        self.a6 = A6()
        self.p1 = P1()
        self.p2 = P2()
        self.start()

    def test_000_start(self):
        from halo_flask.const import LOC
        app.config['ENV_TYPE'] = LOC
        app.config['SSM_TYPE'] = "AWS"
        app.config['FUNC_NAME'] = "FUNC_NAME"
        #app.config['API_CONFIG'] =
        app.config['AWS_REGION'] = 'us-east-1'
        with app.test_request_context(method='GET', path='/?abc=def'):
            try:
                load_api_config(app.config['ENV_TYPE'], app.config['SSM_TYPE'], app.config['FUNC_NAME'],
                                app.config['API_CONFIG'])
            except Exception as e:
                eq_(e.__class__.__name__, "NoApiClassException")

    def test_00_start(self):
        app.config['SSM_TYPE'] = "AWS"
        app.config['AWS_REGION'] = 'us-east-1'
        with app.test_request_context(method='GET', path='/?abc=def'):
            try:
                HALO_HOST = get_host_name()
                params = {}
                params["url"] = set_host_param_config(HALO_HOST)
                set_app_param_config(app.config['SSM_TYPE'],params)
            except Exception as e:
                eq_(e.__class__.__name__, "NoApiClassException")

    def test_01_start(self):
        app.config['SSM_TYPE'] = "AWS"
        app.config['AWS_REGION'] = 'us-east-1'
        app.config['FUNC_NAME'] = "halo_flask"
        with app.test_request_context(method='GET', path='/?abc=def'):
            try:
                val = get_app_param_config(app.config['SSM_TYPE'], app.config['FUNC_NAME'],"url")
                print("get_app_param_config="+str(val))
            except Exception as e:
                eq_(e.__class__.__name__, "NoApiClassException")

    def test_0_start(self):
        with app.test_request_context(method='GET', path='/?abc=def'):
            try:
                if 'INIT_DATA_MAP' in app.config and 'INIT_CLASS_NAME' in app.config:
                    data_map = app.config['INIT_DATA_MAP']
                    class_name = app.config['INIT_CLASS_NAME']
                    load_global_data(class_name, data_map)
            except Exception as e:
                eq_(e.__class__.__name__, "NoApiClassException")

    def test_1_get_request_returns_exception(self):
        with app.test_request_context(method='GET', path='/?abc=def'):
            try:
                response = self.a1.process_get(request, {})
                eq_(1,2)
            except Exception as e:
                eq_(e.__class__.__name__, "NoApiClassException")

    def test_2_delete_request_returns_dict(self):
        with app.test_request_context(method='DELETE', path='/?abc=def'):
            response = self.a1.process_delete(request, {})
            eq_(response.payload, {"tst_delete":"good"})

    def test_3_put_request_returns_dict(self):
        with app.test_request_context(method='PUT', path='/?abc=def'):
            response = self.a1.process_put(request, {})
            eq_(response.payload, {'1': {'tst_put': 'good1'}, '2': {'tst_put': 'good2'}, '3': None})

    def test_4_post_request_returns_a_given_string(self):
        with app.test_request_context(method='POST', path='/?abc=def'):
            response = self.a1.process_post(request, {})
            print("response=" + str(response.payload))
            eq_(response.code, status.HTTP_201_CREATED)
            eq_(response.payload, {'$.BookHotelResult': {'tst_post': 'good1'}, '$.BookFlightResult': {'tst_post': 'good2'}, '$.BookRentalResult': None})

    def test_5_patch_request_returns_a_given_string(self):
        with app.test_request_context(method='PATCH', path='/?abc=def'):
            response = self.a1.process_patch(request, {})
            print("response=" + str(response.payload))
            eq_(response.code, status.HTTP_200_OK)
            eq_(response.payload, {'$.BookHotelResult': {'tst_patch': 'good'}, '$.BookFlightResult': {'tst_patch': 'good'}, '$.BookRentalResult': {'tst_patch': 'good'}})

    def test_6_api_request_returns_a_CircuitBreakerError(self):
        app.config['PROVIDER'] = "AWS"
        app.config['CIRCUIT_BREAKER'] = True
        with app.test_request_context(method='GET', path='/?a=b'):
            api = TstApi(Util.get_halo_context(request))
            timeout = Util.get_timeout(request)
            try:
                response = api.get(timeout)
            except ApiError as e:
                pass
            try:
                response = api.get(timeout)
            except ApiError as e:
                pass
            try:
                response = api.get(timeout)
            except ApiError as e:
                pass
            try:
                response = api.get(timeout)
            except CircuitBreakerError as e:
                print(str(e))
                eq_(e.__class__.__name__, "CircuitBreakerError")

    def test_7_api_request_returns_success(self):
        app.config['PROVIDER'] = "AWS"
        app.config['CIRCUIT_BREAKER'] = True
        #self.test_6_api_request_returns_a_CircuitBreakerError()
        with app.test_request_context(method='GET', path='/?a=b'):
            api = TstApi(Util.get_halo_context(request))
            timeout = Util.get_timeout(request)
            try:
                response = api.get(timeout)
            except ApiError as e:
                print(str(e))
            try:
                response = api.get(timeout)
            except ApiError as e:
                print(str(e))
            try:
                response = api.get(timeout)
            except ApiError as e:
                print(str(e))
            try:
                response = api.get(timeout)
            except Exception as e:
                print(str(e))
            for c in CircuitBreakerMonitor.get_open():
                print(str(c))
            api = CnnApi(Util.get_halo_context(request))
            timeout = Util.get_timeout(request)
            try:
                response = api.get(timeout)
                for c in CircuitBreakerMonitor.get_circuits():
                    print(str(c))
                eq_(response.status_code, status.HTTP_200_OK)
            except ApiError as e:
                eq_(1,2)

    def test_80_api_request_returns_a_fail(self):
        with app.test_request_context(method='GET', path='/?a=b'):
            api = CnnApi(Util.get_halo_context(request))
            api.url = api.url + "/lgkmlgkhm??l,mhb&&,g,hj "
            timeout = Util.get_timeout(request)
            try:
                response = api.get(timeout)
                assert False
            except ApiError as e:
                eq_(e.status_code, status.HTTP_404_NOT_FOUND)
                #eq_(e.__class__.__name__,"CircuitBreakerError")

    def test_810_api_request_soap_returns(self):
        with app.test_request_context(method='GET', path='/'):
            api = Tst2Api(Util.get_halo_context(request),method='method1')
            timeout = Util.get_timeout(request)
            try:
                data = {}
                data['first'] = 'start'
                data['second'] = 'end'
                response = api.run(timeout,data)
                print("response=" + str(response.content))
                eq_(json.loads(response.content)['msg'],'Your input parameters are start and end')
            except ApiError as e:
                #eq_(e.status_code, status.HTTP_404_NOT_FOUND)
                eq_(response.payload['first'],'start')

    def test_811_api_request_soap_returns(self):
        app.config['CIRCUIT_BREAKER'] = True
        with app.test_request_context(method='GET', path='/'):
            api = Tst2Api(Util.get_halo_context(request),method='method1')
            timeout = Util.get_timeout(request)
            try:
                data = {}
                data['first'] = 'start'
                data['second'] = 'end'
                response = api.run(timeout,data)
                print("response=" + str(response.content))
                eq_(json.loads(response.content)['msg'],'Your input parameters are start and end')
            except ApiError as e:
                #eq_(e.status_code, status.HTTP_404_NOT_FOUND)
                eq_(response.payload['first'],'start')

    def test_812_api_request_soap_returns(self):
        app.config['CIRCUIT_BREAKER'] = True
        with app.test_request_context(method='GET', path='/'):
            api = Tst2Api(Util.get_halo_context(request),method='method2')
            timeout = Util.get_timeout(request)
            try:
                data = {}
                data['first'] = 'start'
                data['second'] = 'end'
                response = api.run(timeout,data)
                print("response=" + str(response.content))
                eq_(json.loads(response.content)['msg'],'Your input parameters are start and end')
            except HaloMethodNotImplementedException as e:
                #eq_(e.status_code, status.HTTP_404_NOT_FOUND)
                eq_(e.__class__.__name__,"HaloMethodNotImplementedException")

    def test_82_api_request_rpc_returns(self):
        app.config['PROVIDER'] = "AWS"
        with app.test_request_context(method='GET', path='/?a=b'):
            api = Tst3Api(Util.get_halo_context(request))
            timeout = Util.get_timeout(request)
            try:
                response = api.get(timeout)
                assert False
            except ApiError as e:
                eq_(e.status_code, status.HTTP_404_NOT_FOUND)
                #eq_(e.__class__.__name__,"CircuitBreakerError")

    def test_83_api_request_event_returns(self):
        app.config['PROVIDER'] = "AWS"
        with app.test_request_context(method='GET', path='/?a=b'):
            api = Tst4Api(Util.get_halo_context(request))
            timeout = Util.get_timeout(request)
            try:
                response = api.get(timeout)
                assert False
            except ApiError as e:
                eq_(e.status_code, status.HTTP_404_NOT_FOUND)
                #eq_(e.__class__.__name__,"CircuitBreakerError")

    def test_9_send_event(self):
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

    def test_900_event_filter(self):
        app.config['SSM_TYPE'] = "AWS"
        app.config['AWS_REGION'] = 'us-east-1'
        app.config['PROVIDER'] = "AWS"
        app.config['REQUEST_FILTER_CLASS'] = 'test_flask.TestFilter'
        with app.test_request_context(method='POST', path='/?a=b',headers= {HaloContext.items.get(HaloContext.CORRELATION):"123"},data={"a":"1"}):
            response = self.a2.process_post(request,{})
            eq_(response.payload, [{'id': 1, 'name': 'Pankaj', 'salary': '10000'}, {'name': 'David', 'salary': '5000', 'id': 2}])

    def test_901_event_filter(self):
        app.config['PROVIDER'] = "AWS"
        app.config['REQUEST_FILTER_CLASS'] = 'test_flask.TestFilter'
        with app.test_request_context(method='GET', path='/?a=b',headers= {HaloContext.items.get(HaloContext.CORRELATION):"123"}):
            response = self.a2.process_get(request,{})
            eq_(response.payload, [{'id': 1, 'name': 'Pankaj', 'salary': '10000'}, {'name': 'David', 'salary': '5000', 'id': 2}])

    def test_902_event_filter(self):
        app.config['PROVIDER'] = "AWS"
        app.config['REQUEST_FILTER_CLASS'] = 'test_flask.TestFilter'
        app.config['REQUEST_FILTER_CLEAR_CLASS'] = 'test_flask.TestRequestFilterClear'
        with app.test_request_context(method='GET', path='/?a=b',headers= {HaloContext.items.get(HaloContext.CORRELATION):"123"}):
            response = self.a2.process_get(request,{})

    def test_903_event_filter(self):
        app.config['PROVIDER'] = "AWS"
        app.config['REQUEST_FILTER_CLASS'] = 'test_flask.TestFilter'
        app.config['REQUEST_FILTER_CLEAR_CLASS'] = 'test_flask.TestRequestFilterClear'
        with app.test_request_context(method='GET', path='/?a=b',headers= {HaloContext.items.get(HaloContext.CORRELATION):"123"}):
            response = self.a2.do_process(HTTPChoice.get,request.args)

    def test_91_system_debug_enabled(self):
        with app.test_request_context(method='GET', path='/?a=b'):
            os.environ['DEBUG_LOG'] = 'true'
            flag = 'false'
            for i in range(0, 180):
                ret = Util.get_system_debug_enabled()
                print(ret)
                if ret == 'true':
                    flag = ret
            eq_(flag, 'true')

    def test_92_debug_enabled(self):
        app.config['PROVIDER'] = "AWS"
        headers = {'HTTP_X_HALO_DEBUG_LOG_ENABLED': 'true'}
        with app.test_request_context(method='GET', path='/?a=b', headers=headers):
            ret = Util.get_halo_context(request)
            eq_(ret.dict[HaloContext.items[HaloContext.DEBUG_LOG]], 'true')

    def test_93_json_log(self):
        import traceback
        app.config['PROVIDER'] = "AWS"
        headers = {'HTTP_X_HALO_DEBUG_LOG_ENABLED': 'true'}
        with app.test_request_context(method='GET', path='/?a=b', headers=headers):
            halo_context = Util.get_halo_context(request)
            try:
                raise Exception("test it")
            except Exception as e:
                e.stack = traceback.format_exc()
                ret = log_json(halo_context, {"abc": "def"}, err=e)
                print(str(ret))
                eq_(ret[HaloContext.items[HaloContext.DEBUG_LOG]], 'true')

    def test_94_get_request_with_debug(self):
        app.config['PROVIDER'] = 'ONPREM'
        headers = {'x-halo-debug-log-enabled': 'true'}
        with app.test_request_context(method='GET', path='/?a=b', headers=headers):
            ret = Util.get_debug_enabled(request)
            eq_(ret, 'true')

    def test_95_debug_event(self):
        event = {HaloContext.items[HaloContext.DEBUG_LOG]: 'true'}
        ret = BaseUtil.get_correlation_from_event(event)
        eq_(BaseUtil.event_req_context[HaloContext.items[HaloContext.DEBUG_LOG]], 'true')
        ret = BaseUtil.get_correlation_from_event(event)
        eq_(ret[HaloContext.items[HaloContext.DEBUG_LOG]], 'true')

    def test_96_pref_mixin(self):
        with app.test_request_context(method='GET', path='/perf'):
            response = self.p1.process_get(request, {})
            eq_(response.code, status.HTTP_200_OK)

    def test_97_pref_mixin1(self):
        with app.test_request_context(method='GET', path='/perf/tst'):
            response = self.p2.get()
            eq_(response.status_code, status.HTTP_200_OK)

    def test_98_run_simple_delete(self):
        with app.test_request_context(method='DELETE', path="/start"):
            response = self.a2.delete()
            eq_(response.status_code, status.HTTP_200_OK)

    def test_990_run_seq_get(self):
        with app.test_request_context(method='GET', path="/"):
            response = self.a2.get()
            eq_(response.status_code, status.HTTP_200_OK)

    def test_991_load_saga(self):
        with app.test_request_context(method='POST', path="/"):
            with open("../env/config/saga.json") as f:
                jsonx = json.load(f)
            sagax = saga.load_saga("test",HaloRequest(request), jsonx, app.config['SAGA_SCHEMA'])
            eq_(len(sagax.actions), 6)

    def test_9920_run_saga(self):
        with app.test_request_context(method='POST', path="/"):
            response = self.a2.post()
            eq_(response.status_code, status.HTTP_201_CREATED)

    def test_9921_run_saga_bq(self):
        with app.test_request_context(method='POST', path="/tst?sub_func=deposit"):
            response = self.a2.post()
            eq_(response.status_code, status.HTTP_201_CREATED)

    def test_9922_run_saga_bq_error(self):
        with app.test_request_context(method='POST', path="/tst?sub_func=tst"):
            try:
                response = self.a2.post()
                eq_(1,2)
            except Exception as e:
                eq_(e.__class__.__name__, "InternalServerError")

    def test_9923_trans_json(self):
        with app.test_request_context(method='GET', path="/tst"):
            try:
                response = self.a2.get()
                eq_(response.data, b'{"employees": [{"id": 1, "name": "Pankaj", "salary": "10000"}, {"name": "David", "salary": "5000", "id": 2}]}')
            except Exception as e:
                eq_(e.__class__.__name__, "InternalServerError")

    def test_9930_rollback_saga(self):
        with app.test_request_context(method='PUT', path="/"):
            try:
                response = self.a2.process_put(request, {})
                assert False
            except Exception as e:
                eq_(e.__class__.__name__, "ApiError")

    def test_9931_rollback_saga_error(self):
        with app.test_request_context(method='PATCH', path="/"):
            try:
                response = self.a2.process_patch(request, {})
                assert False
            except Exception as e:
                eq_(e.__class__.__name__, "SagaError")


    def test_9932_all_rollback_saga(self):
        with app.test_request_context(method='PUT', path="/"):
            try:
                response = self.a2.put()
                assert False
            except Exception as e:
                eq_(e.__class__.__name__, "InternalServerError")

    def test_9933_all_rollback_saga_bq(self):
        with app.test_request_context(method='PUT', path="/test?sub_func=deposit"):
            try:
                response = self.a2.put()
                assert False
            except Exception as e:
                eq_(e.__class__.__name__, "InternalServerError")

    def test_9940_ssm_aws(self):  # @TODO test without HALO_AWS
        header = {'HTTP_HOST': '127.0.0.2'}
        app.config['HALO_HOST'] = 'halo_flask'
        app.config['SSM_TYPE'] = "AWS"
        #app.config['PROVIDER'] = "AWS"
        app.config['AWS_REGION'] = 'us-east-1'
        with app.test_request_context(method='GET', path='/?a=b', headers=header):
            try:
                from halo_flask.ssm import set_app_param_config
                params = {}
                params["id"] = "124"
                set_app_param_config(app.config['SSM_TYPE'],params )
                import time
                print("sleep.")
                time.sleep(5.4)
                from halo_flask.ssm import get_app_config
                config = get_app_config(app.config['SSM_TYPE'])
                eq_(config.get_param("halo_flask")["id"], '124')
            except Exception as e:
                eq_(e.__class__.__name__, "ProviderError")

    def test_9941_ssm_aws(self):  # @TODO test with HALO_AWS
        header = {'HTTP_HOST': '127.0.0.2'}
        app.config['HALO_HOST'] = 'halo_flask'
        app.config['SSM_TYPE'] = "AWS"
        app.config['PROVIDER'] = "AWS"
        app.config['AWS_REGION'] = 'us-east-1'
        with app.test_request_context(method='GET', path='/?a=b', headers=header):
            from halo_flask.ssm import set_app_param_config,set_host_param_config
            params = {}
            params["url"] = set_host_param_config("127.0.0.1:8000")
            set_app_param_config(app.config['SSM_TYPE'], params)
            import time
            print("sleep.")
            time.sleep(5.4)
            from halo_flask.ssm import get_app_config
            config = get_app_config(app.config['SSM_TYPE'])
            eq_(config.get_param("halo_flask")["url"], 'https://127.0.0.1:8000/loc')

    def test_9942_ssm_aws(self):  # @TODO test with HALO_AWS
        header = {'HTTP_HOST': '127.0.0.2'}
        app.config['HALO_HOST'] = 'halo_flask'
        app.config['SSM_TYPE'] = "AWS"
        app.config['PROVIDER'] = "AWS"
        app.config['AWS_REGION'] = 'us-east-1'
        with app.test_request_context(method='GET', path='/?a=b', headers=header):
            from halo_flask.ssm import set_app_param_config
            import uuid
            uuidx = uuid.uuid4().__str__()
            print(uuidx)
            params = {}
            params["session_id"] = uuidx
            set_app_param_config(app.config['SSM_TYPE'], params)
            import time
            print("sleep.")
            time.sleep(5.4)
            from halo_flask.ssm import get_app_config
            config = get_app_config(app.config['SSM_TYPE'])
            eq_(config.get_param(app.config['HALO_HOST'])["session_id"], uuidx)

    def test_9944_ssm_aws(self):  # @TODO test with HALO_AWS
        header = {'HTTP_HOST': '127.0.0.2'}
        app.config['HALO_HOST'] = 'halo_flask'
        app.config['SSM_TYPE'] = None
        #app.config['PROVIDER'] = "AWS"
        #app.config['AWS_REGION'] = 'us-east-1'
        with app.test_request_context(method='GET', path='/?a=b', headers=header):
            try:
                from halo_flask.ssm import set_app_param_config
                from halo_flask.ssm import set_host_param_config
                params = {}
                params["url"] = set_host_param_config("halo_flask:8000")
                set_app_param_config(app.config['SSM_TYPE'], params)
                import time
                print("sleep.")
                time.sleep(5.4)
                from halo_flask.ssm import get_app_config
                config = get_app_config(app.config['SSM_TYPE'])
                eq_(config.get_param(app.config['HALO_HOST'])["url"], 'https://127.0.0.1:8000/loc')
            except Exception as e:
                eq_(e.__class__.__name__, "NoSSMDefinedError")

    def test_9945_ssm_aws(self):  # @TODO test with HALO_AWS
        header = {'HTTP_HOST': '127.0.0.2'}
        app.config['HALO_HOST'] = 'halo_flask'
        app.config['SSM_TYPE'] = "XYZ"
        #app.config['PROVIDER'] = "AWS"
        #app.config['AWS_REGION'] = 'us-east-1'
        with app.test_request_context(method='GET', path='/?a=b', headers=header):
            try:
                from halo_flask.ssm import set_app_param_config
                from halo_flask.ssm import set_host_param_config
                params = {}
                params["url"] = set_host_param_config("halo_flask:8000")
                set_app_param_config(app.config['SSM_TYPE'], params)
                import time
                print("sleep.")
                time.sleep(5.4)
                from halo_flask.ssm import get_app_config
                config = get_app_config(app.config['SSM_TYPE'])
                eq_(config.get_param("halo_flask")["url"], 'https://halo_flask:8000/loc')
            except Exception as e:
                eq_(e.__class__.__name__, "NotSSMTypeError")

    def test_995_ssm_onperm(self):  # @TODO
        header = {'HTTP_HOST': '127.0.0.2'}
        app.config['SSM_TYPE'] = "ONPREM"
        app.config['ONPREM_SSM_CLASS_NAME'] = 'OnPremClient'
        app.config['ONPREM_SSM_MODULE_NAME'] = 'halo_flask.providers.ssm.onprem_ssm_client'
        with app.test_request_context(method='GET', path='/?a=b', headers=header):
            from halo_flask.ssm import set_app_param_config
            params = {}
            params["url"] = "124"
            set_app_param_config(app.config['SSM_TYPE'], params)
            from halo_flask.ssm import get_app_config
            config = get_app_config(app.config['SSM_TYPE'])
            t = config.get_param('halo_flask')
            print("t="+str(t))
            eq_(str(t), '<Section: FUNC_NAME>')#'<Section: DEFAULT>')

    def test_996_error_handler(self):
        with app.test_request_context(method='DELETE', path='/perf'):
            response = self.p1.process_delete(request, {})
            #print("x="+str(response.content))
            #print("ret=" + str(json.loads(response.content)))
            #eq_(json.loads(response.content)['error']['error_message'], 'test error msg')
            eq_(response.code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_997_timeout(self):
        with app.test_request_context(method='GET', path='/?a=b'):
            os.environ["AWS_LAMBDA_FUNCTION_NAME"] = "halo_flask"
            timeout = Util.get_timeout(request)
            eq_(timeout, 3)



    def test_998_perf_get(self):
        with app.test_request_context(method='GET', path='/perf'):
            response = self.p1.process_get(request, {})
            eq_(response.code, status.HTTP_200_OK)

    def test_999_perf_get_link(self):
        with app.test_request_context(method='GET', path='/perf'):
            response = self.p2.get()
            eq_(response.status_code, status.HTTP_200_OK)

    def test_9991_tst2_get(self):
        with app.test_request_context(method='GET', path='/xst2/2/tst1/1/tst/0/'):
            response = self.a2.get()
            eq_(response.status_code, status.HTTP_200_OK)

    def test_99911_filter(self):
        with app.test_request_context(method='GET', path='/xst2/2/tst1/1/tst/0/'):
            response = self.a3.process_get(request, {})
            eq_(response.code, status.HTTP_200_OK)

    def test_99911_filter(self):
        with app.test_request_context(method='GET', path='/xst2/2/tst1/1/tst/0/'):
            response = self.a3.process_get(request, {})
            eq_(response.code, status.HTTP_200_OK)

    def test_9992_CORR(self):
        headers = {'HTTP_HOST': '127.0.0.2','x-correlation-id':"123"}
        app.config['HALO_CONTEXT_LIST'] = [HaloContext.CORRELATION]
        with app.test_request_context(method='GET', path='/xst2/2/tst1/1/tst/0/',headers=headers):
            response = self.a2.get()
            eq_(response.status_code, status.HTTP_200_OK)

    def test_9993_NOCORR(self):
        header = {'HTTP_HOST': '127.0.0.2'}
        app.config['HALO_CONTEXT_LIST'] = [HaloContext.CORRELATION]
        with app.test_request_context(method='GET', path='/xst2/2/tst1/1/tst/0/',headers=header):
            try:
                response = self.a2.get()
                return False
            except Exception as e:
                eq_(e.__class__.__name__, "InternalServerError")

    def test_9994_CORR(self):
        app.config['PROVIDER'] = "AWS"
        headers = {'HTTP_HOST': '127.0.0.2','x-tester-id':"123"}
        app.config['HALO_CONTEXT_LIST'] = [CAContext.TESTER]
        app.config['HALO_CONTEXT_CLASS'] = 'test_flask.CAContext'
        with app.test_request_context(method='GET', path='/xst2/2/tst1/1/tst/0/',headers=headers):
            response = self.a2.get()
            eq_(response.status_code, status.HTTP_200_OK)

    def test_9995_NOCORR(self):
        header = {'HTTP_HOST': '127.0.0.2'}
        app.config['HALO_CONTEXT_LIST'] = [CAContext.TESTER]
        app.config['HALO_CONTEXT_CLASS'] = 'test_flask.CAContext'
        with app.test_request_context(method='GET', path='/xst2/2/tst1/1/tst/0/',headers=header):
            try:
                response = self.a2.get()
                return False
            except Exception as e:
                eq_(e.__class__.__name__, "InternalServerError")

    def test_9996_NOCORR(self):
        from halo_flask.flask.viewsx import load_global_data
        app.config["INIT_CLASS_NAME"] = 'halo_flask.flask.viewsx.GlobalService'
        app.config["INIT_DATA_MAP"] = {'INIT_STATE': "Idle", 'PROP_URL':
            "C:\\dev\\projects\\halo\\halo_flask\\halo_flask\\env\\config\\flask_setting_mapping.json"}
        load_global_data(app.config["INIT_CLASS_NAME"], app.config["INIT_DATA_MAP"])

    def test_9997_db(self):
        app.config['DBACCESS_CLASS'] = 'test_flask.DbMixin'
        with app.test_request_context(method='GET', path='/xst2/2/tst1/1/tst/0/'):
            db = DbTest()
            req = HaloRequest(request)
            db.get_dbaccess(req,True)

    def test_9998_db(self):
        app.config['DBACCESS_CLASS'] = 'test_flask.DbMixin'
        with app.test_request_context(method='GET', path='/xst2/2/tst1/1/tst/0/'):
            db = DbTest()
            req = HaloRequest(request)
            db.get_dbaccess(req,False)


    def test_99991_security_need_token(self):
        app.config['CIRCUIT_BREAKER'] = False
        with app.test_request_context(method='GET', path='/xst2/2/tst1/1/tst/0/'):
            try:
                response = self.a4.get()
                eq_(1,2)
            except Exception as e:
                eq_(e.data['errors']['error']["error_code"], 10108)

    def test_99992_security_bad_token(self):
        app.config['CIRCUIT_BREAKER'] = False
        app.config['SESSION_MINUTES'] = 30
        public_id = '12345'
        secret = '123456'#different token
        hdr = HaloSecurity.user_token(None, public_id,30,secret)
        headers = {'HTTP_HOST': '127.0.0.2', 'x-halo-access-token': hdr['token']}
        with app.test_request_context(method='GET', path='/xst2/2/tst1/1/tst/0/',headers=headers):
            try:
                response = self.a4.get()
                eq_(1,2)
            except Exception as e:
                eq_(e.data['errors']['error']["error_code"], 10109)

    def test_99992_security_good_token(self):
        app.config['CIRCUIT_BREAKER'] = False
        app.config['SESSION_MINUTES'] = 30
        secret = '123456'
        app.config['SECRET_KEY'] = secret
        public_id = '12345'
        hdr = HaloSecurity.user_token(None, public_id,30,secret)
        headers = {'HTTP_HOST': '127.0.0.2', 'x-halo-access-token': hdr['token']}
        with app.test_request_context(method='GET', path='/xst2/2/tst1/1/tst/0/',headers=headers):
            try:
                response = self.a4.get()
                eq_(1,2)
            except Exception as e:
                eq_(e.data['errors']['error']["error_code"], 500)

    def test_99993_security_good_token_no_role_needed(self):
        app.config['CIRCUIT_BREAKER'] = False
        app.config['SESSION_MINUTES'] = 30
        secret = '12345'
        app.config['SECRET_KEY'] = secret
        app.config['HALO_SECURITY_CLASS'] = 'tests.test_flask.Sec'
        public_id = '12345'
        hdr = HaloSecurity.user_token(None, public_id, 30, secret)
        headers = {'HTTP_HOST': '127.0.0.2', 'x-halo-access-token': hdr['token']}
        with app.test_request_context(method='GET', path='/xst2/2/tst1/1/tst/0/', headers=headers):
            try:
                self.a4.method_roles = []
                response = self.a4.get()
                eq_(1,2)
            except Exception as e:
                eq_(e.data['errors']['error']["error_code"], 500)

    def test_99994_security_good_token_role_needed_missing(self):
        app.config['CIRCUIT_BREAKER'] = False
        app.config['SESSION_MINUTES'] = 30
        secret = '12345'
        app.config['SECRET_KEY'] = secret
        app.config['HALO_SECURITY_CLASS'] = 'tests.test_flask.Sec'
        public_id = '12345'
        hdr = HaloSecurity.user_token(None, public_id, 30, secret)
        headers = {'HTTP_HOST': '127.0.0.2', 'x-halo-access-token': hdr['token']}
        with app.test_request_context(method='GET', path='/xst2/2/tst1/1/tst/0/', headers=headers):
            try:
                self.a4.method_roles = ['tst1']
                response = self.a4.get()
                eq_(1,2)
            except Exception as e:
                eq_(e.data['errors']['error']["error_code"], 500)

    def test_99995_security_good_token_role_needed_exist(self):
        app.config['PROVIDER'] = "AWS"
        app.config['CIRCUIT_BREAKER'] = False
        app.config['SESSION_MINUTES'] = 30
        secret = '12345'
        app.config['SECRET_KEY'] = secret
        app.config['HALO_SECURITY_CLASS'] = 'tests.test_flask.Sec'
        public_id = '12345'
        hdr = HaloSecurity.user_token(None, public_id, 30, secret)
        headers = {'HTTP_HOST': '127.0.0.2', 'x-halo-access-token': hdr['token']}
        with app.test_request_context(method='GET', path='/xst2/2/tst1/1/tst/0/', headers=headers):
            try:
                self.a4.method_roles = ['tst']
                response = self.a4.get()
                eq_(response.status_code,200)
            except Exception as e:
                print(str(e))
                eq_(1,2)

    def test_99996_aws_invoke_sync_fail(self):
        app.config['PROVIDER'] = "AWS"
        app.config['CIRCUIT_BREAKER'] = False
        app.config['SESSION_MINUTES'] = 30
        secret = '12345'
        app.config['SECRET_KEY'] = secret
        app.config['HALO_SECURITY_CLASS'] = 'tests.test_flask.Sec'
        public_id = '12345'
        hdr = HaloSecurity.user_token(None, public_id, 30, secret)
        headers = {'HTTP_HOST': '127.0.0.2', 'x-halo-access-token': hdr['token']}
        with app.test_request_context(method='GET', path='/xst2/2/tst1/1/tst/0/', headers=headers):
            try:
                self.a5.method_roles = ['tst']
                response = self.a5.process_get(request,{})
                eq_(1,2)
            except Exception as e:
                eq_(e.__class__, 'halo_aws.providers.cloud.aws.exceptions.ProviderError')

    def test_99997_aws_invoke_sync_fail(self):
        app.config['PROVIDER'] = "AWS"
        app.config['CIRCUIT_BREAKER'] = False
        app.config['SESSION_MINUTES'] = 30
        secret = '12345'
        app.config['SECRET_KEY'] = secret
        app.config['HALO_SECURITY_CLASS'] = 'tests.test_flask.Sec'
        public_id = '12345'
        hdr = HaloSecurity.user_token(None, public_id, 30, secret)
        headers = {'HTTP_HOST': '127.0.0.2', 'x-halo-access-token': hdr['token']}
        with app.test_request_context(method='GET', path='/xst2/2/tst1/1/tst/0/', headers=headers):
            try:
                self.a6.method_roles = ['tst']
                response = self.a6.get()
                eq_(1,2)
            except Exception as e:
                eq_(e.__class__, 'halo_aws.providers.cloud.aws.exceptions.ProviderError')

    def test_99998_aws_invoke_sync_success(self):
        app.config['PROVIDER'] = "AWS"
        app.config['CIRCUIT_BREAKER'] = False
        app.config['HALO_CONTEXT_LIST'] = ["CORRELATION"]
        app.config['SESSION_MINUTES'] = 30
        secret = '12345'
        app.config['SECRET_KEY'] = secret
        app.config['HALO_SECURITY_CLASS'] = 'tests.test_flask.Sec'
        public_id = '12345'
        hdr = HaloSecurity.user_token(None, public_id, 30, secret)
        headers = {'HTTP_HOST': '127.0.0.2', 'x-halo-access-token': hdr['token'],'x-halo-correlation-id':'123456'}
        with app.test_request_context(method='POST', path='/xst2/2/tst1/1/tst/0/', headers=headers):
            try:
                self.a5.method_roles = ['tst']
                response = self.a5.process_post(request, {})
                eq_(response.code, 201)
            except Exception as e:
                print(str(e))
                eq_(1,2)

    def test_99999_aws_invoke_sync_success(self):
        app.config['PROVIDER'] = "AWS"
        app.config['DEBUG'] = True
        app.config['CIRCUIT_BREAKER'] = False
        app.config['HALO_CONTEXT_LIST'] = ["CORRELATION"]
        app.config['SESSION_MINUTES'] = 30
        secret = '12345'
        app.config['SECRET_KEY'] = secret
        app.config['HALO_SECURITY_CLASS'] = 'tests.test_flask.Sec'
        public_id = '12345'
        hdr = HaloSecurity.user_token(None, public_id, 30, secret)
        headers = {'HTTP_HOST': '127.0.0.2', 'x-halo-access-token': hdr['token'],'x-halo-correlation-id':'123456'}
        with app.test_request_context(method='POST', path='/xst2/2/tst1/1/tst/0/', headers=headers):
            try:
                self.a6.method_roles = ['tst']
                response = self.a6.post()
                eq_(response.status_code, 201)
            except Exception as e:
                print(str(e))
                eq_(1,2)