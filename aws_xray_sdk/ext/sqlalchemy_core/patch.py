import logging
import sys
if sys.version_info >= (3, 0, 0):
    from urllib.parse import urlparse, uses_netloc
else:
    from urlparse import urlparse, uses_netloc

import wrapt

from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core.patcher import _PATCHED_MODULES
from aws_xray_sdk.core.utils import stacktrace
from aws_xray_sdk.ext.util import unwrap


def _sql_meta(instance, args):
    try:
        metadata = {}
        url = urlparse(str(instance.engine.url))
        # Add Scheme to uses_netloc or // will be missing from url.
        uses_netloc.append(url.scheme)
        if url.password is None:
            metadata['url'] = url.geturl()
            name = url.netloc
        else:
            # Strip password from URL
            host_info = url.netloc.rpartition('@')[-1]
            parts = url._replace(netloc='{}@{}'.format(url.username, host_info))
            metadata['url'] = parts.geturl()
            name = host_info
        metadata['user'] = url.username
        metadata['database_type'] = instance.engine.name
        try:
            version = getattr(instance.dialect, '{}_version'.format(instance.engine.driver))
            version_str = '.'.join(map(str, version))
            metadata['driver_version'] = "{}-{}".format(instance.engine.driver, version_str)
        except AttributeError:
            metadata['driver_version'] = instance.engine.driver
        if instance.dialect.server_version_info is not None:
            metadata['database_version'] = '.'.join(map(str, instance.dialect.server_version_info))
        if xray_recorder.stream_sql:
            metadata['sanitized_query'] = str(args[0])
    except Exception:
        metadata = None
        name = None
        logging.getLogger(__name__).exception('Error parsing sql metadata.')
    return name, metadata


def _xray_traced_sqlalchemy_execute(wrapped, instance, args, kwargs):
    name, sql = _sql_meta(instance, args)
    if sql is not None:
        subsegment = xray_recorder.begin_subsegment(name, namespace='remote')
    else:
        subsegment = None
    try:
        res = wrapped(*args, **kwargs)
    except Exception:
        if subsegment is not None:
            exception = sys.exc_info()[1]
            stack = stacktrace.get_stacktrace(limit=xray_recorder._max_trace_back)
            subsegment.add_exception(exception, stack)
        raise
    finally:
        if subsegment is not None:
            subsegment.set_sql(sql)
            xray_recorder.end_subsegment()
    return res


def patch():
    wrapt.wrap_function_wrapper(
        'sqlalchemy.engine.base',
        'Connection.execute',
        _xray_traced_sqlalchemy_execute
    )


def unpatch():
    """
    Unpatch any previously patched modules.
    This operation is idempotent.
    """
    _PATCHED_MODULES.discard('sqlalchemy_core')
    import sqlalchemy
    unwrap(sqlalchemy.engine.base.Connection, 'execute')
