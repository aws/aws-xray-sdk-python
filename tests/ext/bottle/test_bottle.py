import pytest
from bottle import Bottle, request, response, template, view, HTTPError, TEMPLATE_PATH
from webtest import TestApp as WebApp

from aws_xray_sdk import global_sdk_config
from aws_xray_sdk.ext.bottle.middleware import XRayMiddleware
from aws_xray_sdk.core.context import Context
from aws_xray_sdk.core import lambda_launcher
from aws_xray_sdk.core.models import http, facade_segment, segment as segment_model
from tests.util import get_new_stubbed_recorder
import os


# define Bottle app for testing purpose
TEMPLATE_PATH.insert(0, os.path.dirname(__file__) + '/views')
app = Bottle()


@app.route('/ok')
def ok():
    response_data = 'ok'
    # Bottle not always set Content-Length header
    response.content_length = len(response_data)
    return response_data


@app.route('/error')
def error():
    response.status = 404
    return 'Not Found'


@app.route('/client_error')
def faulty_client():
    class CustomError(Exception):
        def __init__(self, description=None, status_code=None):
            self.description = description
            self.status_code = status_code

    raise CustomError(description='Bad request', status_code=400)


@app.route('/server_error')
def faulty_server():
    raise HTTPError(status=503, body='Service Unavailable')


@app.route('/fault')
def fault():
    return {}['key']


@app.route('/template')
def template_():
    return template('Hello {{name}}!', name='World')


@app.route('/view')
@view('index')
def view_(name='bottle'):
    return dict(name=name)


# add X-Ray plugin to Bottle app
recorder = get_new_stubbed_recorder()
recorder.configure(service='test', sampling=False, context=Context())
app.install(XRayMiddleware(recorder))

app = WebApp(app)

BASE_URL = 'http://localhost:80{}'


@pytest.fixture(autouse=True)
def cleanup():
    """
    Clean up context storage before and after each test run
    """
    recorder.clear_trace_entities()
    yield
    recorder.clear_trace_entities()
    global_sdk_config.set_sdk_enabled(True)


def test_ok():
    path = '/ok'
    app.get(path, extra_environ={'REMOTE_ADDR': '127.0.0.1'})
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
    try:
        app.get(path, extra_environ={'HTTP_X_FORWARDED_FOR': '192.168.0.0'})
    except Exception:
        pass
    segment = recorder.emitter.pop()
    assert not segment.in_progress
    assert segment.error

    request = segment.http['request']
    response = segment.http['response']
    assert request['method'] == 'GET'
    assert request['url'] == BASE_URL.format(path)
    assert request['client_ip'] == '192.168.0.0'
    assert response['status'] == 404


def test_custom_client_error():
    path = '/client_error'
    try:
        app.get(path)
    except Exception:
        pass
    segment = recorder.emitter.pop()
    assert not segment.in_progress
    assert segment.error

    response = segment.http['response']
    assert response['status'] == 400
    exception = segment.cause['exceptions'][0]
    assert exception.type == 'CustomError'

    request = segment.http['request']
    assert request['method'] == 'GET'
    assert request['url'] == BASE_URL.format(path)


def test_server_error():
    path = '/server_error'
    try:
        app.get(path)
    except Exception as e:
        pass
    segment = recorder.emitter.pop()
    assert not segment.in_progress
    assert segment.fault

    response = segment.http['response']
    assert response['status'] == 503

    exception = segment.cause['exceptions'][0]
    assert exception.type == 'HTTPError'


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


def test_render_view():
    path = '/view'
    response = app.get(path)
    assert response.text == "<h1>Hello Bottle!</h1>\n<p>How are you?</p>\n"
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
    # resp = app.get(path, headers={http.XRAY_HEADER: 'Sampled=0'})
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
    app.get(path, headers={http.XRAY_HEADER: 'Sampled=?;k1=v1'})
    segment = recorder.emitter.pop()

    resp_header = response.headers.get(http.XRAY_HEADER)
    assert segment.trace_id in resp_header
    assert 'Sampled=1' in resp_header


def test_disabled_sdk():
    global_sdk_config.set_sdk_enabled(False)
    path = '/ok'
    app.get(path)
    segment = recorder.emitter.pop()
    assert not segment


def test_lambda_serverless():
    TRACE_ID = '1-5759e988-bd862e3fe1be46a994272793'
    PARENT_ID = '53995c3f42cd8ad8'
    HEADER_VAR = 'Root=%s;Parent=%s;Sampled=1' % (TRACE_ID, PARENT_ID)

    os.environ[lambda_launcher.LAMBDA_TRACE_HEADER_KEY] = HEADER_VAR
    lambda_context = lambda_launcher.LambdaContext()

    new_recorder = get_new_stubbed_recorder()
    new_recorder.configure(service='test', sampling=False, context=lambda_context)
    new_app = Bottle()

    @new_app.route('/subsegment')
    def subsegment_():
        # Test in between request and make sure Serverless creates a subsegment instead of a segment.
        # Ensure that the parent segment is a facade segment.
        assert new_recorder.current_subsegment()
        assert type(new_recorder.current_segment()) == facade_segment.FacadeSegment
        return 'ok'

    @new_app.route('/trace_header')
    def trace_header():
        # Ensure trace header is preserved.
        subsegment = new_recorder.current_subsegment()
        header = subsegment.get_origin_trace_header()
        assert header.data['k1'] == 'v1'
        return 'ok'

    plugin = XRayMiddleware(new_recorder)
    plugin._in_lambda_ctx = True
    new_app.install(plugin)

    app_client = WebApp(new_app)

    path = '/subsegment'
    app_client.get(path)
    new_app.get(path)
    segment = recorder.emitter.pop()
    assert not segment  # Segment should be none because it's created and ended by the plugin

    path2 = '/trace_header'
    app_client.get(path2, headers={http.XRAY_HEADER: 'k1=v1'})


def test_lambda_default_ctx():
    # Track to make sure that Bottle will default to generating segments if context is not the lambda context
    new_recorder = get_new_stubbed_recorder()
    new_recorder.configure(service='test', sampling=False)
    new_app = Bottle()

    @new_app.route('/segment')
    def segment_():
        # Test in between request and make sure Lambda that uses default context generates a segment.
        assert new_recorder.current_segment()
        assert type(new_recorder.current_segment()) == segment_model.Segment
        return 'ok'

    new_app.install(XRayMiddleware(new_recorder))
    app_client = WebApp(new_app)

    path = '/segment'
    app_client.get(path)
    segment = recorder.emitter.pop()
    assert not segment  # Segment should be none because it's created and ended by the plugin
