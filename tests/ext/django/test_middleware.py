import django
from aws_xray_sdk import global_sdk_config
from django.urls import reverse
from django.test import TestCase

from aws_xray_sdk.core import xray_recorder, lambda_launcher
from aws_xray_sdk.core.context import Context
from aws_xray_sdk.core.models import http, facade_segment, segment
from aws_xray_sdk.core import patch
from tests.util import get_new_stubbed_recorder
import os


class XRayTestCase(TestCase):

    def setUp(self):
        django.setup()
        xray_recorder.configure(context=Context())
        xray_recorder.clear_trace_entities()
        global_sdk_config.set_sdk_enabled(True)

    def tearDown(self):
        xray_recorder.clear_trace_entities()

    def test_ok(self):
        url = reverse('200ok')
        self.client.get(url)
        segment = xray_recorder.emitter.pop()

        request = segment.http['request']
        response = segment.http['response']

        assert request['method'] == 'GET'
        assert request['client_ip'] == '127.0.0.1'
        assert response['status'] == 200

    def test_error(self):
        self.client.get('/notfound/')
        segment = xray_recorder.emitter.pop()
        assert segment.error

        request = segment.http['request']
        response = segment.http['response']

        assert request['method'] == 'GET'
        assert request['client_ip'] == '127.0.0.1'
        assert response['status'] == 404

    def test_fault(self):
        url = reverse('500fault')
        try:
            self.client.get(url)
        except Exception:
            pass
        segment = xray_recorder.emitter.pop()
        assert segment.fault

        request = segment.http['request']
        response = segment.http['response']

        assert request['method'] == 'GET'
        assert request['client_ip'] == '127.0.0.1'
        assert response['status'] == 500

        exception = segment.cause['exceptions'][0]
        assert exception.type == 'KeyError'

    def test_db(self):
        patch(('sqlite3',))
        url = reverse('call_db')
        self.client.get(url)
        segment = xray_recorder.emitter.pop()
        assert len(segment.subsegments) == 1

        subsegment = segment.subsegments[0]
        assert subsegment.name == ':memory:'
        assert not subsegment.in_progress

        sql = subsegment.sql
        assert sql['database_type'] == 'sqlite3'
        assert sql['database_version']

    def test_template(self):
        url = reverse('template')
        self.client.get(url)
        segment = xray_recorder.emitter.pop()
        assert len(segment.subsegments) == 1

        subsegment = segment.subsegments[0]
        assert subsegment.name == 'index.html'
        assert not subsegment.in_progress
        assert subsegment.namespace == 'local'

    def test_template_block(self):
        url = reverse('template_block')
        self.client.get(url)
        segment = xray_recorder.emitter.pop()
        assert len(segment.subsegments) == 1

        subsegment = segment.subsegments[0]
        assert subsegment.name == 'block_user.html'
        assert not subsegment.in_progress
        assert subsegment.namespace == 'local'

    def test_trace_header_data_perservation(self):
        url = reverse('200ok')
        self.client.get(url, HTTP_X_AMZN_TRACE_ID='k1=v1')
        segment = xray_recorder.emitter.pop()
        header = segment.get_origin_trace_header()

        assert header.data['k1'] == 'v1'

    def test_response_header(self):
        url = reverse('200ok')
        resp = self.client.get(url, HTTP_X_AMZN_TRACE_ID='Sampled=?')
        segment = xray_recorder.emitter.pop()
        trace_header = resp[http.XRAY_HEADER]

        assert 'Sampled=1' in trace_header
        assert segment.trace_id in trace_header

    def test_disabled_sdk(self):
        global_sdk_config.set_sdk_enabled(False)
        url = reverse('200ok')
        self.client.get(url)
        segment = xray_recorder.emitter.pop()
        assert not segment

    def test_lambda_serverless(self):
        TRACE_ID = '1-5759e988-bd862e3fe1be46a994272793'
        PARENT_ID = '53995c3f42cd8ad8'
        HEADER_VAR = "Root=%s;Parent=%s;Sampled=1" % (TRACE_ID, PARENT_ID)

        os.environ[lambda_launcher.LAMBDA_TRACE_HEADER_KEY] = HEADER_VAR
        lambda_context = lambda_launcher.LambdaContext()

        new_recorder = get_new_stubbed_recorder()
        new_recorder.configure(service='test', sampling=False, context=lambda_context)
        subsegment = new_recorder.begin_subsegment("subsegment")
        assert type(subsegment.parent_segment) == facade_segment.FacadeSegment
        new_recorder.end_subsegment()

        url = reverse('200ok')
        self.client.get(url)
        segment = new_recorder.emitter.pop()
        assert not segment

        # Test Fault in Lambda
        url = reverse('500fault')
        try:
            self.client.get(url)
        except Exception:
            pass
        segment = xray_recorder.emitter.pop()
        assert segment.fault

        request = segment.http['request']
        response = segment.http['response']

        assert request['method'] == 'GET'
        assert request['client_ip'] == '127.0.0.1'
        assert response['status'] == 500

        exception = segment.cause['exceptions'][0]
        assert exception.type == 'KeyError'

    def test_lambda_default_ctx(self):
        # Track to make sure that Django will default to generating segments if context is not the lambda context
        url = reverse('200ok')
        self.client.get(url)
        cur_segment = xray_recorder.emitter.pop()
        assert type(cur_segment) == segment.Segment
