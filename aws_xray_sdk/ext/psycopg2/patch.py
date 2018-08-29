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
        'database_type': 'postgresql',
        'database_host': kwargs['host'] if 'host' in kwargs else re.search(r'host=(\S+)\b', args[0]).groups()[0],
        'database_name': kwargs['dbname'] if 'dbname' in kwargs else re.search(r'dbname=(\S+)\b', args[0]).groups()[0],
        'database_user': kwargs['user'] if 'user' in kwargs else re.search(r'user=(\S+)\b', args[0]).groups()[0],
    }

    return XRayTracedConn(conn, meta)
