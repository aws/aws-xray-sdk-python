import pytest

import httpx
from aws_xray_sdk.core import patch
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core.context import Context
from aws_xray_sdk.ext.util import strip_url, get_hostname


patch(("httpx",))

# httpbin.org is created by the same author of requests to make testing http easy.
BASE_URL = "httpbin.org"


@pytest.fixture(autouse=True)
def construct_ctx():
    """
    Clean up context storage on each test run and begin a segment
    so that later subsegment can be attached. After each test run
    it cleans up context storage again.
    """
    xray_recorder.configure(service="test", sampling=False, context=Context())
    xray_recorder.clear_trace_entities()
    xray_recorder.begin_segment("name")
    yield
    xray_recorder.clear_trace_entities()


@pytest.mark.parametrize("use_client", (True, False))
def test_ok(use_client):
    status_code = 200
    url = "http://{}/status/{}?foo=bar".format(BASE_URL, status_code)
    if use_client:
        with httpx.Client() as client:
            response = client.get(url)
    else:
        response = httpx.get(url)
    assert "x-amzn-trace-id" in response._request.headers

    subsegment = xray_recorder.current_segment().subsegments[0]
    assert get_hostname(url) == BASE_URL
    assert subsegment.namespace == "remote"
    assert subsegment.name == get_hostname(url)

    http_meta = subsegment.http
    assert http_meta["request"]["url"] == strip_url(url)
    assert http_meta["request"]["method"].upper() == "GET"
    assert http_meta["response"]["status"] == status_code


@pytest.mark.parametrize("use_client", (True, False))
def test_error(use_client):
    status_code = 400
    url = "http://{}/status/{}".format(BASE_URL, status_code)
    if use_client:
        with httpx.Client() as client:
            response = client.post(url)
    else:
        response = httpx.post(url)
    assert "x-amzn-trace-id" in response._request.headers

    subsegment = xray_recorder.current_segment().subsegments[0]
    assert subsegment.namespace == "remote"
    assert subsegment.name == get_hostname(url)
    assert subsegment.error

    http_meta = subsegment.http
    assert http_meta["request"]["url"] == strip_url(url)
    assert http_meta["request"]["method"].upper() == "POST"
    assert http_meta["response"]["status"] == status_code


@pytest.mark.parametrize("use_client", (True, False))
def test_throttle(use_client):
    status_code = 429
    url = "http://{}/status/{}".format(BASE_URL, status_code)
    if use_client:
        with httpx.Client() as client:
            response = client.head(url)
    else:
        response = httpx.head(url)
    assert "x-amzn-trace-id" in response._request.headers

    subsegment = xray_recorder.current_segment().subsegments[0]
    assert subsegment.namespace == "remote"
    assert subsegment.name == get_hostname(url)
    assert subsegment.error
    assert subsegment.throttle

    http_meta = subsegment.http
    assert http_meta["request"]["url"] == strip_url(url)
    assert http_meta["request"]["method"].upper() == "HEAD"
    assert http_meta["response"]["status"] == status_code


@pytest.mark.parametrize("use_client", (True, False))
def test_fault(use_client):
    status_code = 500
    url = "http://{}/status/{}".format(BASE_URL, status_code)
    if use_client:
        with httpx.Client() as client:
            response = client.put(url)
    else:
        response = httpx.put(url)
    assert "x-amzn-trace-id" in response._request.headers

    subsegment = xray_recorder.current_segment().subsegments[0]
    assert subsegment.namespace == "remote"
    assert subsegment.name == get_hostname(url)
    assert subsegment.fault

    http_meta = subsegment.http
    assert http_meta["request"]["url"] == strip_url(url)
    assert http_meta["request"]["method"].upper() == "PUT"
    assert http_meta["response"]["status"] == status_code


@pytest.mark.parametrize("use_client", (True, False))
def test_nonexistent_domain(use_client):
    with pytest.raises(httpx.ConnectError):
        if use_client:
            with httpx.Client() as client:
                client.get("http://doesnt.exist")
        else:
            httpx.get("http://doesnt.exist")

    subsegment = xray_recorder.current_segment().subsegments[0]
    assert subsegment.namespace == "remote"
    assert subsegment.fault

    exception = subsegment.cause["exceptions"][0]
    assert exception.type == "ConnectError"


@pytest.mark.parametrize("use_client", (True, False))
def test_invalid_url(use_client):
    url = "KLSDFJKLSDFJKLSDJF"
    with pytest.raises(httpx.UnsupportedProtocol):
        if use_client:
            with httpx.Client() as client:
                client.get(url)
        else:
            httpx.get(url)

    subsegment = xray_recorder.current_segment().subsegments[0]
    assert subsegment.namespace == "remote"
    assert subsegment.name == get_hostname(url)
    assert subsegment.fault

    http_meta = subsegment.http
    assert http_meta["request"]["url"] == "/{}".format(strip_url(url))

    exception = subsegment.cause["exceptions"][0]
    assert exception.type == "UnsupportedProtocol"


@pytest.mark.parametrize("use_client", (True, False))
def test_name_uses_hostname(use_client):
    if use_client:
        client = httpx.Client()
    else:
        client = httpx

    try:
        url1 = "http://{}/fakepath/stuff/koo/lai/ahh".format(BASE_URL)
        client.get(url1)
        subsegment = xray_recorder.current_segment().subsegments[-1]
        assert subsegment.namespace == "remote"
        assert subsegment.name == BASE_URL
        http_meta1 = subsegment.http
        assert http_meta1["request"]["url"] == strip_url(url1)
        assert http_meta1["request"]["method"].upper() == "GET"

        url2 = "http://{}/".format(BASE_URL)
        client.get(url2, params={"some": "payload", "not": "toBeIncluded"})
        subsegment = xray_recorder.current_segment().subsegments[-1]
        assert subsegment.namespace == "remote"
        assert subsegment.name == BASE_URL
        http_meta2 = subsegment.http
        assert http_meta2["request"]["url"] == strip_url(url2)
        assert http_meta2["request"]["method"].upper() == "GET"

        url3 = "http://subdomain.{}/fakepath/stuff/koo/lai/ahh".format(BASE_URL)
        try:
            client.get(url3)
        except httpx.ConnectError:
            pass
        subsegment = xray_recorder.current_segment().subsegments[-1]
        assert subsegment.namespace == "remote"
        assert subsegment.name == "subdomain." + BASE_URL
        http_meta3 = subsegment.http
        assert http_meta3["request"]["url"] == strip_url(url3)
        assert http_meta3["request"]["method"].upper() == "GET"
    finally:
        if use_client:
            client.close()


@pytest.mark.parametrize("use_client", (True, False))
def test_strip_http_url(use_client):
    status_code = 200
    url = "http://{}/get?foo=bar".format(BASE_URL)
    if use_client:
        with httpx.Client() as client:
            response = client.get(url)
    else:
        response = httpx.get(url)
    assert "x-amzn-trace-id" in response._request.headers

    subsegment = xray_recorder.current_segment().subsegments[0]
    assert subsegment.namespace == "remote"
    assert subsegment.name == get_hostname(url)

    http_meta = subsegment.http
    assert http_meta["request"]["url"] == strip_url(url)
    assert http_meta["request"]["method"].upper() == "GET"
    assert http_meta["response"]["status"] == status_code
