import wrapt
import botocore.client
from botocore.exceptions import ClientError

from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core.models import http
from aws_xray_sdk.ext.util import inject_trace_header
from aws_xray_sdk.ext.util import to_snake_case
from .resources import whitelist


def patch():
    """
    Patch botocore client so it generates subsegments
    when calling AWS services.
    """
    if hasattr(botocore.client, '_xray_enabled'):
        return
    setattr(botocore.client, '_xray_enabled', True)

    wrapt.wrap_function_wrapper(
        'botocore.client',
        'BaseClient._make_api_call',
        _xray_traced_botocore,
    )

    wrapt.wrap_function_wrapper(
        'botocore.endpoint',
        'Endpoint._encode_headers',
        _inject_header,
    )


def _xray_traced_botocore(wrapped, instance, args, kwargs):

    service = instance._service_model.metadata["endpointPrefix"]
    return xray_recorder.record_subsegment(
        wrapped, instance, args, kwargs,
        name=service,
        namespace='aws',
        meta_processor=aws_meta_processor,
    )


def _inject_header(wrapped, instance, args, kwargs):
    headers = args[0]
    inject_trace_header(headers, xray_recorder.current_subsegment())
    return wrapped(*args, **kwargs)


def aws_meta_processor(wrapped, instance, args, kwargs,
                       return_value, exception, subsegment, stack):

    region = instance.meta.region_name

    if 'operation_name' in kwargs:
        operation_name = kwargs['operation_name']
    else:
        operation_name = args[0]

    aws_meta = {
        'operation': operation_name,
        'region': region,
    }

    if return_value:
        resp_meta = return_value.get('ResponseMetadata')
        if resp_meta:
            aws_meta['request_id'] = resp_meta.get('RequestId')
            subsegment.put_http_meta(http.STATUS,
                                     resp_meta.get('HTTPStatusCode'))
            # for service like S3 that returns special request id in response headers
            if 'HTTPHeaders' in resp_meta and resp_meta['HTTPHeaders'].get('x-amz-id-2'):
                aws_meta['id_2'] = resp_meta['HTTPHeaders']['x-amz-id-2']

    elif exception:
        _aws_error_handler(exception, stack, subsegment, aws_meta)

    _extract_whitelisted_params(subsegment.name, operation_name,
                                aws_meta, args, kwargs, return_value)

    subsegment.set_aws(aws_meta)


def _aws_error_handler(exception, stack, subsegment, aws_meta):

    if not exception or not isinstance(exception, ClientError):
        return

    response_metadata = exception.response.get('ResponseMetadata')

    if not response_metadata:
        return

    aws_meta['request_id'] = response_metadata.get('RequestId')

    status_code = response_metadata.get('HTTPStatusCode')

    subsegment.put_http_meta(http.STATUS, status_code)
    if(status_code == 429):
        subsegment.add_throttle_flag()
    if(status_code / 100 == 4):
        subsegment.add_error_flag()

    subsegment.add_exception(exception, stack, True)


def _extract_whitelisted_params(service, operation,
                                aws_meta, args, kwargs, response):

    # check if service is whitelisted
    if service not in whitelist['services']:
        return
    operations = whitelist['services'][service]['operations']

    # check if operation is whitelisted
    if operation not in operations:
        return
    params = operations[operation]

    # record whitelisted request/response parameters
    if 'request_parameters' in params:
        _record_params(params['request_parameters'], args[1], aws_meta)

    if 'request_descriptors' in params:
        _record_special_params(params['request_descriptors'],
                               args[1], aws_meta)

    if 'response_parameters' in params and response:
        _record_params(params['response_parameters'], response, aws_meta)

    if 'response_descriptors' in params and response:
        _record_special_params(params['response_descriptors'],
                               response, aws_meta)


def _record_params(whitelisted, actual, aws_meta):

    for key in whitelisted:
        if key in actual:
            snake_key = to_snake_case(key)
            aws_meta[snake_key] = actual[key]


def _record_special_params(whitelisted, actual, aws_meta):

    for key in whitelisted:
        if key in actual:
            _process_descriptor(whitelisted[key], actual[key], aws_meta)


def _process_descriptor(descriptor, value, aws_meta):

    # "get_count" = true
    if 'get_count' in descriptor and descriptor['get_count']:
        value = len(value)

    # "get_keys" = true
    if 'get_keys' in descriptor and descriptor['get_keys']:
        value = value.keys()

    aws_meta[descriptor['rename_to']] = value
