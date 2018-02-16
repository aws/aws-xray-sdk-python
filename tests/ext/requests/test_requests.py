import pytest
import requests

from aws_xray_sdk.core import patch
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core.context import Context
from aws_xray_sdk.ext.util import strip_url


patch(('requests',))

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


def test_ok():
    status_code = 200
    url = 'http://{}/status/{}?foo=bar'.format(BASE_URL, status_code)
    requests.get(url)
    subsegment = xray_recorder.current_segment().subsegments[0]
    assert subsegment.name == strip_url(url)

    http_meta = subsegment.http
    assert http_meta['request']['url'] == url
    assert http_meta['request']['method'].upper() == 'GET'
    assert http_meta['response']['status'] == status_code


def test_error():
    status_code = 400
    url = 'http://{}/status/{}'.format(BASE_URL, status_code)
    requests.post(url)
    subsegment = xray_recorder.current_segment().subsegments[0]
    assert subsegment.name == url
    assert subsegment.error

    http_meta = subsegment.http
    assert http_meta['request']['url'] == url
    assert http_meta['request']['method'].upper() == 'POST'
    assert http_meta['response']['status'] == status_code


def test_throttle():
    status_code = 429
    url = 'http://{}/status/{}'.format(BASE_URL, status_code)
    requests.head(url)
    subsegment = xray_recorder.current_segment().subsegments[0]
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
    requests.put(url)
    subsegment = xray_recorder.current_segment().subsegments[0]
    assert subsegment.name == url
    assert subsegment.fault

    http_meta = subsegment.http
    assert http_meta['request']['url'] == url
    assert http_meta['request']['method'].upper() == 'PUT'
    assert http_meta['response']['status'] == status_code


def test_invalid_url():
    try:
        requests.get('http://doesnt.exist')
    except Exception:
        # prevent uncatch exception from breaking test run
        pass
    subsegment = xray_recorder.current_segment().subsegments[0]
    assert subsegment.fault

    exception = subsegment.cause['exceptions'][0]
    assert exception.type == 'ConnectionError'
