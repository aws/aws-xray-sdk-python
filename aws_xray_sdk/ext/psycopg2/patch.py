import re
import wrapt

from aws_xray_sdk.ext.dbapi2 import XRayTracedConn


def patch():

    wrapt.wrap_function_wrapper(
        'psycopg2',
        'connect',
        _xray_traced_connect
    )


def _xray_traced_connect(wrapped, instance, args, kwargs):

    conn = wrapped(*args, **kwargs)

    meta = {
        'dbname': kwargs['dbname'] if 'dbname' in kwargs else re.match(r'dbname=(\S+)\b', args[0]).groups()[0],
        'database_type': 'postgresql'
    }

    return XRayTracedConn(conn, meta)
