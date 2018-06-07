import pytest
from flask import Flask, render_template_string

from aws_xray_sdk.ext.flask.middleware import XRayMiddleware
from aws_xray_sdk.core.context import Context
from aws_xray_sdk.core.models import http
from tests.util import get_new_stubbed_recorder


# define a flask app for testing purpose
app = Flask(__name__)


@app.route('/ok')
def ok():
    return 'ok'


@app.route('/error')
def error():
    return 'Not Found', 404


@app.route('/fault')
def fault():
    return {}['key']


@app.route('/template')
def template():
    return render_template_string('hello template')


# add X-Ray middleware to flask app
recorder = get_new_stubbed_recorder()
recorder.configure(service='test', sampling=False, context=Context())
XRayMiddleware(app, recorder)

# enable testing mode
app.config['TESTING'] = True
app = app.test_client()

BASE_URL = 'http://localhost{}'


@pytest.fixture(autouse=True)
def cleanup():
    """
    Clean up context storage before and after each test run
    """
    recorder.clear_trace_entities()
    yield
    recorder.clear_trace_entities()


def test_ok():
    path = '/ok'
    app.get(path)
    segment = recorder.emitter.pop()
    assert not segment.in_progress

    request = segment.http['request']
    response = segment.http['response']

    assert request['method'] == 'GET'
    assert request['url'] == BASE_URL.format(path)
    assert request['client_ip'] == '127.0.0.1'
    assert response['status'] == 200
    assert response['content_length'] == 2


def test_error():
    path = '/error'
    app.get(path)
    segment = recorder.emitter.pop()
    assert not segment.in_progress
    assert segment.error

    request = segment.http['request']
    response = segment.http['response']
    assert request['method'] == 'GET'
    assert request['url'] == BASE_URL.format(path)
    assert request['client_ip'] == '127.0.0.1'
    assert response['status'] == 404


def test_fault():
    path = '/fault'
    try:
        app.get(path)
    except Exception:
        pass
    segment = recorder.emitter.pop()
    assert not segment.in_progress
    assert segment.fault

    response = segment.http['response']
    assert response['status'] == 500

    exception = segment.cause['exceptions'][0]
    assert exception.type == 'KeyError'


def test_render_template():
    path = '/template'
    app.get(path)
    segment = recorder.emitter.pop()
    assert not segment.in_progress
    # segment should contain a template render subsegment
    assert segment.subsegments

    subsegment = segment.subsegments[0]
    assert subsegment.name
    assert subsegment.namespace == 'local'
    assert not subsegment.in_progress


def test_incoming_sampling_decision_respected():
    path = '/ok'
    resp = app.get(path, headers={http.XRAY_HEADER: 'Sampled=0'})
    resp_header = resp.headers[http.XRAY_HEADER]
    segment = recorder.emitter.pop()

    assert not segment
    # The SDK should still send the headers back regardless of sampling decision
    assert 'Root' in resp_header


def test_trace_header_data_perservation():
    path = '/ok'
    app.get(path, headers={http.XRAY_HEADER: 'k1=v1'})
    segment = recorder.emitter.pop()
    header = segment.get_origin_trace_header()

    assert header.data['k1'] == 'v1'


def test_sampled_response_header():
    path = '/ok'
    resp = app.get(path, headers={http.XRAY_HEADER: 'Sampled=?;k1=v1'})
    segment = recorder.emitter.pop()

    resp_header = resp.headers[http.XRAY_HEADER]
    assert segment.trace_id in resp_header
    assert 'Sampled=1' in resp_header
