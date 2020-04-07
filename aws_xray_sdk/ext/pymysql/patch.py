import wrapt
import pymysql

from aws_xray_sdk.ext.dbapi2 import XRayTracedConn


MYSQL_ATTR = {
    '_host': 'name',
    '_user': 'user',
}


def patch():

    wrapt.wrap_function_wrapper(
        'pymysql',
        'connect',
        _xray_traced_connect
    )

    # patch alias
    if hasattr(pymysql, 'Connect'):
        pymysql.Connect = pymysql.connect


def _xray_traced_connect(wrapped, instance, args, kwargs):

    conn = wrapped(*args, **kwargs)
    meta = {}

    for attr, key in MYSQL_ATTR.items():
        if hasattr(conn, attr):
            meta[key] = getattr(conn, attr)

    if hasattr(conn, '_server_version'):
        version = sanitize_db_ver(getattr(conn, '_server_version'))
        if version:
            meta['database_version'] = version

    return XRayTracedConn(conn, meta)


def sanitize_db_ver(raw):

    if not raw or not isinstance(raw, tuple):
        return raw

    return '.'.join(str(num) for num in raw)
