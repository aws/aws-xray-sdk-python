import pymysql

import pytest
import testing.mysqld

from aws_xray_sdk.core import patch
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core.context import Context
from aws_xray_sdk.ext.pymysql import unpatch


@pytest.fixture(scope='module', autouse=True)
def patch_module():
    patch(('pymysql',))
    yield
    unpatch()


@pytest.fixture(autouse=True)
def construct_ctx():
    """
    Clean up context storage on each test run and begin a segment
    so that later subsegment can be attached. After each test run
    it cleans up context storage again.
    """
    xray_recorder.configure(service='test', sampling=False, context=Context())
    xray_recorder.clear_trace_entities()
    xray_recorder.begin_segment('name')
    yield
    xray_recorder.clear_trace_entities()


def test_execute_dsn_kwargs():
    q = 'SELECT 1'
    with testing.mysqld.Mysqld() as mysqld:
        dsn = mysqld.dsn()
        conn = pymysql.connect(database=dsn['db'],
                              user=dsn['user'],
                              password='',
                              host=dsn['host'],
                              port=dsn['port'])
        cur = conn.cursor()
        cur.execute(q)

    subsegment = xray_recorder.current_segment().subsegments[-1]
    assert subsegment.name == 'execute'
    sql = subsegment.sql
    assert sql['database_type'] == 'MySQL'
    assert sql['user'] == dsn['user']
    assert sql['driver_version'] == 'PyMySQL'
    assert sql['database_version']


def test_execute_bad_query():
    q = "SELECT blarg"
    with testing.mysqld.Mysqld() as mysqld:
        dsn = mysqld.dsn()
        conn = pymysql.connect(database=dsn['db'],
                              user=dsn['user'],
                              password='',
                              host=dsn['host'],
                              port=dsn['port'])

        cur = conn.cursor()
        try:
            cur.execute(q)
        except Exception:
            pass

    subsegment = xray_recorder.current_segment().subsegments[-1]
    assert subsegment.name == "execute"
    sql = subsegment.sql
    assert sql['database_type'] == 'MySQL'
    assert sql['user'] == dsn['user']
    assert sql['driver_version'] == 'PyMySQL'
    assert sql['database_version']

    exception = subsegment.cause['exceptions'][0]
    assert exception.type == 'InternalError'
