import pytest
import sys

from aws_xray_sdk.core import patch
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core.context import Context
from aws_xray_sdk.ext.util import strip_url, get_hostname

if sys.version_info >= (3, 0, 0):
    import http.client as httplib
    from urllib.parse import urlparse
else:
    import httplib
    from urlparse import urlparse


# httpbin.org is created by the same author of requests to make testing http easy.
BASE_URL = 'httpbin.org'


@pytest.fixture(autouse=True)
def construct_ctx():
    """
    Clean up context storage on each test run and begin a segment
    so that later subsegment can be attached. After each test run
    it cleans up context storage again.
    """
    from aws_xray_sdk.ext.httplib import unpatch, reset_ignored

    patch(('httplib',))
    xray_recorder.configure(service='test', sampling=False, context=Context())
    xray_recorder.clear_trace_entities()
    xray_recorder.begin_segment('name')

    yield
    xray_recorder.clear_trace_entities()
    unpatch()
    reset_ignored()


def _do_req(url, method='GET', use_https=True):
    parts = urlparse(url)
    host, _, port = parts.netloc.partition(':')
    if port == '':
        port = None
    if use_https:
        conn = httplib.HTTPSConnection(parts.netloc, port)
    else:
        conn = httplib.HTTPConnection(parts.netloc, port)

    path = '{}?{}'.format(parts.path, parts.query) if parts.query else parts.path
    conn.request(method, path)
    resp = conn.getresponse()


def test_ok():
    status_code = 200
    url = 'https://{}/status/{}?foo=bar&baz=foo'.format(BASE_URL, status_code)
    _do_req(url)
    subsegment = xray_recorder.current_segment().subsegments[1]
    assert subsegment.name == get_hostname(url)

    http_meta = subsegment.http
    assert http_meta['request']['url'] == strip_url(url)
    assert http_meta['request']['method'].upper() == 'GET'
    assert http_meta['response']['status'] == status_code


def test_error():
    status_code = 400
    url = 'https://{}/status/{}'.format(BASE_URL, status_code)
    _do_req(url, 'POST')
    subsegment = xray_recorder.current_segment().subsegments[1]
    assert subsegment.name == get_hostname(url)
    assert subsegment.error

    http_meta = subsegment.http
    assert http_meta['request']['url'] == strip_url(url)
    assert http_meta['request']['method'].upper() == 'POST'
    assert http_meta['response']['status'] == status_code


def test_throttle():
    status_code = 429
    url = 'https://{}/status/{}'.format(BASE_URL, status_code)
    _do_req(url, 'HEAD')
    subsegment = xray_recorder.current_segment().subsegments[1]
    assert subsegment.name == get_hostname(url)
    assert subsegment.error
    assert subsegment.throttle

    http_meta = subsegment.http
    assert http_meta['request']['url'] == strip_url(url)
    assert http_meta['request']['method'].upper() == 'HEAD'
    assert http_meta['response']['status'] == status_code


def test_fault():
    status_code = 500
    url = 'https://{}/status/{}'.format(BASE_URL, status_code)
    _do_req(url, 'PUT')
    subsegment = xray_recorder.current_segment().subsegments[1]
    assert subsegment.name == get_hostname(url)
    assert subsegment.fault

    http_meta = subsegment.http
    assert http_meta['request']['url'] == strip_url(url)
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


def test_correct_identify_http():
    status_code = 200
    url = 'http://{}/status/{}?foo=bar&baz=foo'.format(BASE_URL, status_code)
    _do_req(url, use_https=False)
    subsegment = xray_recorder.current_segment().subsegments[0]
    assert subsegment.name == get_hostname(url)

    http_meta = subsegment.http
    assert http_meta['request']['url'].split(":")[0] == 'http'


def test_correct_identify_https():
    status_code = 200
    url = 'https://{}/status/{}?foo=bar&baz=foo'.format(BASE_URL, status_code)
    _do_req(url, use_https=True)
    subsegment = xray_recorder.current_segment().subsegments[0]
    assert subsegment.name == get_hostname(url)

    https_meta = subsegment.http
    assert https_meta['request']['url'].split(":")[0] == 'https'


def test_ignore_url():
    from aws_xray_sdk.ext.httplib import add_ignored
    path = '/status/200'
    url = 'https://{}{}'.format(BASE_URL, path)
    add_ignored(urls=[path])
    _do_req(url, use_https=True)
    assert len(xray_recorder.current_segment().subsegments) == 0


def test_ignore_hostname():
    from aws_xray_sdk.ext.httplib import add_ignored
    path = '/status/200'
    url = 'https://{}{}'.format(BASE_URL, path)
    add_ignored(hostname=BASE_URL)
    _do_req(url, use_https=True)
    assert len(xray_recorder.current_segment().subsegments) == 0


def test_ignore_hostname_glob():
    from aws_xray_sdk.ext.httplib import add_ignored
    path = '/status/200'
    url = 'https://{}{}'.format(BASE_URL, path)
    add_ignored(hostname='http*.org')
    _do_req(url, use_https=True)
    assert len(xray_recorder.current_segment().subsegments) == 0


class CustomHttpsConnection(httplib.HTTPSConnection):
    pass


def test_ignore_subclass():
    from aws_xray_sdk.ext.httplib import add_ignored
    path = '/status/200'
    subclass = 'tests.ext.httplib.test_httplib.CustomHttpsConnection'
    add_ignored(subclass=subclass)
    conn = CustomHttpsConnection(BASE_URL)
    conn.request('GET', path)
    conn.getresponse()
    assert len(xray_recorder.current_segment().subsegments) == 0


def test_ignore_multiple_match():
    from aws_xray_sdk.ext.httplib import add_ignored
    path = '/status/200'
    subclass = 'tests.ext.httplib.test_httplib.CustomHttpsConnection'
    add_ignored(subclass=subclass, hostname=BASE_URL)
    conn = CustomHttpsConnection(BASE_URL)
    conn.request('GET', path)
    conn.getresponse()
    assert len(xray_recorder.current_segment().subsegments) == 0


def test_ignore_multiple_no_match():
    from aws_xray_sdk.ext.httplib import add_ignored
    path = '/status/200'
    subclass = 'tests.ext.httplib.test_httplib.CustomHttpsConnection'
    add_ignored(subclass=subclass, hostname='fake.host')
    conn = CustomHttpsConnection(BASE_URL)
    conn.request('GET', path)
    conn.getresponse()
    assert len(xray_recorder.current_segment().subsegments) > 0
