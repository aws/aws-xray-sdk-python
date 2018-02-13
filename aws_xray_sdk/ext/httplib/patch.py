import wrapt
from collections import namedtuple

from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core.models import http
from aws_xray_sdk.ext.util import inject_trace_header

import ssl


_XRAY_PROP = '_xray_prop'
_XRay_Data = namedtuple('xray_data', ['method', 'host', 'url'])


def http_response_processor(wrapped, instance, args, kwargs, return_value,
                            exception, subsegment, stack):
    xray_data = getattr(instance, _XRAY_PROP)

    subsegment.put_http_meta(http.METHOD, xray_data.method)
    subsegment.put_http_meta(http.URL, xray_data.url)

    if return_value:
        subsegment.put_http_meta(http.STATUS, return_value.code)

        # propagate to response object
        xray_data = _XRay_Data('READ', xray_data.host, xray_data.url)
        setattr(return_value, _XRAY_PROP, xray_data)

    if exception:
        subsegment.add_exception(exception, stack)


def _xray_traced_http_client(wrapped, instance, args, kwargs):
    if kwargs.get('buffering', False):
        return wrapped(*args, **kwargs)  # ignore py2 calls that fail as 'buffering` only exists in py2.

    xray_data = getattr(instance, _XRAY_PROP)

    return xray_recorder.record_subsegment(
        wrapped, instance, args, kwargs,
        name=xray_data.url,
        namespace='remote',
        meta_processor=http_response_processor,
    )


def http_request_processor(wrapped, instance, args, kwargs, return_value,
                        exception, subsegment, stack):
    xray_data = getattr(instance, _XRAY_PROP)

    # we don't delete the attr as we can have multiple reads
    subsegment.put_http_meta(http.METHOD, xray_data.method)
    subsegment.put_http_meta(http.URL, xray_data.url)

    if exception:
        subsegment.add_exception(exception, stack)


def _prep_request(wrapped, instance, args, kwargs):
    def decompose_args(method, url, body, headers, encode_chunked):
        inject_trace_header(headers, xray_recorder.current_subsegment())

        # we have to check against sock because urllib3's HTTPSConnection inherit's from http.client.HTTPConnection
        scheme = 'https' if isinstance(instance.sock, ssl.SSLSocket) else 'http'
        xray_url = '{}://{}{}'.format(scheme, instance.host, url)
        xray_data = _XRay_Data(method, instance.host, xray_url)
        setattr(instance, _XRAY_PROP, xray_data)

        return xray_recorder.record_subsegment(
            wrapped, instance, args, kwargs,
            name=xray_data.url,
            namespace='remote',
            meta_processor=http_request_processor
        )

    return decompose_args(*args, **kwargs)


def http_read_processor(wrapped, instance, args, kwargs, return_value,
                        exception, subsegment, stack):
    xray_data = getattr(instance, _XRAY_PROP)

    # we don't delete the attr as we can have multiple reads
    subsegment.put_http_meta(http.METHOD, xray_data.method)
    subsegment.put_http_meta(http.URL, xray_data.url)
    subsegment.put_http_meta(http.STATUS, instance.status)
    subsegment.apply_status_code(instance.status)

    if exception:
        subsegment.add_exception(exception, stack)


def _xray_traced_http_client_read(wrapped, instance, args, kwargs):
    xray_data = getattr(instance, _XRAY_PROP)

    return xray_recorder.record_subsegment(
        wrapped, instance, args, kwargs,
        name=xray_data.url,
        namespace='remote',
        meta_processor=http_read_processor
    )


def patch():
    wrapt.wrap_function_wrapper(
        'http.client',
        'HTTPConnection._send_request',
        _prep_request
    )

    wrapt.wrap_function_wrapper(
        'http.client',
        'HTTPConnection.getresponse',
        _xray_traced_http_client
    )

    wrapt.wrap_function_wrapper(
        'http.client',
        'HTTPResponse.read',
        _xray_traced_http_client_read
    )
