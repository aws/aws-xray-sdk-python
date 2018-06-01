import wrapt
import traceback
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core.models import http
from aws_xray_sdk.ext.util import prepare_response_header
from chalice.app import Chalice


def aws_xray_wrapper(wrapped, instance, args, kwargs):
    app = instance
    request = app.current_request
    headers = request.headers
    method = request.method
    path = request.context['resourcePath']
    # name e.g. Razor GET /measurements
    name = f'{app.app_name} {method} {path}'

    subsegment = xray_recorder.begin_subsegment(name)
    if subsegment is None:
        # no context, maybe not in Lambda
        # directly pass to the wrapped
        return wrapped(*args, **kwargs)

    subsegment.put_http_meta(http.URL, path)
    subsegment.put_http_meta(http.METHOD, method)
    subsegment.put_http_meta(http.USER_AGENT, headers.get('User-Agent'))
    client_ip = headers.get(
        'X-Forwarded-For') or headers.get('HTTP_X_FORWARDED_FOR')
    if client_ip:
        subsegment.put_http_meta(http.CLIENT_IP, client_ip)
        subsegment.put_http_meta(http.X_FORWARDED_FOR, True)

    # start request
    response = None
    try:
        response = wrapped(*args, **kwargs)
    except Exception as exception:
        # actually according to code, this method does not throw.
        # Chalice._get_view_function_response
        print(exception)
        subsegment.put_http_meta(http.STATUS, 500)
        stack = traceback.extract_stack(limit=xray_recorder._max_trace_back)
        subsegment.add_exception(exception, stack)
        xray_recorder.end_subsegment()
        raise
    else:
        subsegment.put_http_meta(http.STATUS, response.status_code)

        segment = xray_recorder.current_segment()
        origin_header = segment.get_origin_trace_header()
        resp_header_str = prepare_response_header(origin_header, segment)
        response.headers[http.XRAY_HEADER] = resp_header_str

        cont_len = response.headers.get('Content-Length')
        if cont_len:
            subsegment.put_http_meta(http.CONTENT_LENGTH, int(cont_len))

        xray_recorder.end_subsegment()
        return response


def patch():
    # ensure `patch()` is idempotent
    if hasattr(Chalice, '_xray_enabled'):
        return
    setattr(Chalice, '_xray_enabled', True)
    wrapt.wrap_function_wrapper(
        'chalice.app',
        'Chalice._get_view_function_response',
        aws_xray_wrapper)
