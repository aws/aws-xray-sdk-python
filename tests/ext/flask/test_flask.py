import pytest
from flask import Flask, render_template_string

from aws_xray_sdk.ext.flask.middleware import XRayMiddleware
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
recorder.configure(service='test', sampling=False)
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
