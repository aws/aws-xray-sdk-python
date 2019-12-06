import pytest
import requests

from aws_xray_sdk.core import patch
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core.context import Context
from aws_xray_sdk.ext.util import strip_url, get_hostname


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
    assert get_hostname(url) == BASE_URL
    assert subsegment.name == get_hostname(url)

    http_meta = subsegment.http
    assert http_meta['request']['url'] == strip_url(url)
    assert http_meta['request']['method'].upper() == 'GET'
    assert http_meta['response']['status'] == status_code


def test_error():
    status_code = 400
    url = 'http://{}/status/{}'.format(BASE_URL, status_code)
    requests.post(url)
    subsegment = xray_recorder.current_segment().subsegments[0]
    assert subsegment.name == get_hostname(url)
    assert subsegment.error

    http_meta = subsegment.http
    assert http_meta['request']['url'] == strip_url(url)
    assert http_meta['request']['method'].upper() == 'POST'
    assert http_meta['response']['status'] == status_code


def test_throttle():
    status_code = 429
    url = 'http://{}/status/{}'.format(BASE_URL, status_code)
    requests.head(url)
    subsegment = xray_recorder.current_segment().subsegments[0]
    assert subsegment.name == get_hostname(url)
    assert subsegment.error
    assert subsegment.throttle

    http_meta = subsegment.http
    assert http_meta['request']['url'] == strip_url(url)
    assert http_meta['request']['method'].upper() == 'HEAD'
    assert http_meta['response']['status'] == status_code


def test_fault():
    status_code = 500
    url = 'http://{}/status/{}'.format(BASE_URL, status_code)
    requests.put(url)
    subsegment = xray_recorder.current_segment().subsegments[0]
    assert subsegment.name == get_hostname(url)
    assert subsegment.fault

    http_meta = subsegment.http
    assert http_meta['request']['url'] == strip_url(url)
    assert http_meta['request']['method'].upper() == 'PUT'
    assert http_meta['response']['status'] == status_code


def test_nonexistent_domain():
    try:
        requests.get('http://doesnt.exist')
    except Exception:
        # prevent uncatch exception from breaking test run
        pass
    subsegment = xray_recorder.current_segment().subsegments[0]
    assert subsegment.fault

    exception = subsegment.cause['exceptions'][0]
    assert exception.type == 'ConnectionError'


def test_invalid_url():
    url = 'KLSDFJKLSDFJKLSDJF'
    try:
        requests.get(url)
    except Exception:
        # prevent uncatch exception from breaking test run
        pass
    subsegment = xray_recorder.current_segment().subsegments[0]
    assert subsegment.name == get_hostname(url)
    assert subsegment.fault

    http_meta = subsegment.http
    assert http_meta['request']['url'] == strip_url(url)

    exception = subsegment.cause['exceptions'][0]
    assert exception.type == 'MissingSchema'


def test_name_uses_hostname():
    url1 = 'http://{}/fakepath/stuff/koo/lai/ahh'.format(BASE_URL)
    requests.get(url1)
    subsegment = xray_recorder.current_segment().subsegments[-1]
    assert subsegment.name == BASE_URL
    http_meta1 = subsegment.http
    assert http_meta1['request']['url'] == strip_url(url1)
    assert http_meta1['request']['method'].upper() == 'GET'

    url2 = 'http://{}/'.format(BASE_URL)
    requests.get(url2, params={"some": "payload", "not": "toBeIncluded"})
    subsegment = xray_recorder.current_segment().subsegments[-1]
    assert subsegment.name == BASE_URL
    http_meta2 = subsegment.http
    assert http_meta2['request']['url'] == strip_url(url2)
    assert http_meta2['request']['method'].upper() == 'GET'

    url3 = 'http://subdomain.{}/fakepath/stuff/koo/lai/ahh'.format(BASE_URL)
    try:
        requests.get(url3)
    except Exception:
        # This is an invalid url so we dont want to break the test
        pass
    subsegment = xray_recorder.current_segment().subsegments[-1]
    assert subsegment.name == "subdomain." + BASE_URL
    http_meta3 = subsegment.http
    assert http_meta3['request']['url'] == strip_url(url3)
    assert http_meta3['request']['method'].upper() == 'GET'


def test_strip_http_url():
    status_code = 200
    url = 'http://{}/get?foo=bar'.format(BASE_URL)
    requests.get(url)
    subsegment = xray_recorder.current_segment().subsegments[0]
    assert subsegment.name == get_hostname(url)

    http_meta = subsegment.http
    assert http_meta['request']['url'] == strip_url(url)
    assert http_meta['request']['method'].upper() == 'GET'
    assert http_meta['response']['status'] == status_code

