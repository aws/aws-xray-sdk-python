import pytest
import sys

from aws_xray_sdk.core import patch
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core.context import Context
from aws_xray_sdk.ext.util import strip_url

if sys.version_info >= (3, 0, 0):
    import http.client as httplib
    from urllib.parse import urlparse
else:
    import httplib
    from urlparse import urlparse


patch(('httplib',))

# httpbin.org is created by the same author of requests to make testing http easy.
BASE_URL = 'httpbin.org'


@pytest.fixture(autouse=True)
def construct_ctx():
    """
    Clean up context storage on each test run and begin a segment
    so that later subsegment can be attached. After each test run
    it cleans up context storage again.
    """
    xray_recorder.configure(service='test', sampling=False, context=Context())
    xray_recorder.clear_trace_entities()
    xray_recorder.begin_segment('name')
    yield
    xray_recorder.clear_trace_entities()


def _do_req(url, method='GET'):
    parts = urlparse(url)
    host, _, port = parts.netloc.partition(':')
    if port == '':
        port = None
    conn = httplib.HTTPConnection(parts.netloc, port)

    path = '{}?{}'.format(parts.path, parts.query) if parts.query else parts.path
    conn.request(method, path)
    resp = conn.getresponse()


def test_ok():
    status_code = 200
    url = 'http://{}/status/{}?foo=bar&baz=foo'.format(BASE_URL, status_code)
    _do_req(url)
    subsegment = xray_recorder.current_segment().subsegments[1]
    assert subsegment.name == strip_url(url)

    http_meta = subsegment.http
    assert http_meta['request']['url'] == url
    assert http_meta['request']['method'].upper() == 'GET'
    assert http_meta['response']['status'] == status_code


def test_error():
    status_code = 400
    url = 'http://{}/status/{}'.format(BASE_URL, status_code)
    _do_req(url, 'POST')
    subsegment = xray_recorder.current_segment().subsegments[1]
    assert subsegment.name == url
    assert subsegment.error

    http_meta = subsegment.http
    assert http_meta['request']['url'] == url
    assert http_meta['request']['method'].upper() == 'POST'
    assert http_meta['response']['status'] == status_code


def test_throttle():
    status_code = 429
    url = 'http://{}/status/{}'.format(BASE_URL, status_code)
    _do_req(url, 'HEAD')
    subsegment = xray_recorder.current_segment().subsegments[1]
    assert subsegment.name == url
    assert subsegment.error
    assert subsegment.throttle

    http_meta = subsegment.http
    assert http_meta['request']['url'] == url
    assert http_meta['request']['method'].upper() == 'HEAD'
    assert http_meta['response']['status'] == status_code


def test_fault():
    status_code = 500
    url = 'http://{}/status/{}'.format(BASE_URL, status_code)
    _do_req(url, 'PUT')
    subsegment = xray_recorder.current_segment().subsegments[1]
    assert subsegment.name == url
    assert subsegment.fault

    http_meta = subsegment.http
    assert http_meta['request']['url'] == url
    assert http_meta['request']['method'].upper() == 'PUT'
    assert http_meta['response']['status'] == status_code


def test_invalid_url():
    try:
        _do_req('http://doesnt.exist')
    except Exception:
        # prevent uncatch exception from breaking test run
        pass
    subsegment = xray_recorder.current_segment().subsegments[0]
    assert subsegment.fault

    exception = subsegment.cause['exceptions'][0]
    assert exception.type == 'gaierror'
