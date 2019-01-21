import django
import aws_xray_sdk
from django.core.urlresolvers import reverse
from django.test import TestCase

from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core.context import Context
from aws_xray_sdk.core.models import http


class XRayTestCase(TestCase):

    def setUp(self):
        django.setup()
        xray_recorder.configure(context=Context(),
                                context_missing='LOG_ERROR')
        xray_recorder.clear_trace_entities()
        aws_xray_sdk.global_sdk_config.set_sdk_enabled(True)

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
        aws_xray_sdk.global_sdk_config.set_sdk_enabled(False)
        url = reverse('200ok')
        self.client.get(url)
        segment = xray_recorder.emitter.pop()
        assert not segment
