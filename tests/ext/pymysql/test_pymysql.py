import pymysql

import pytest

from aws_xray_sdk.core import patch
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core.context import Context
from aws_xray_sdk.ext.pymysql import unpatch

MYSQL_USER = "root"
MYSQL_PASSWORD = "root"
MYSQL_HOST = "localhost"
MYSQL_PORT = 3306
MYSQL_DB_NAME = "test_db"

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
    conn = pymysql.connect(database=MYSQL_DB_NAME,
                          user=MYSQL_USER,
                          password=MYSQL_PASSWORD,
                          host=MYSQL_HOST,
                          port=MYSQL_PORT)
    cur = conn.cursor()
    cur.execute(q)

    subsegment = xray_recorder.current_segment().subsegments[-1]
    assert subsegment.name == 'execute'
    sql = subsegment.sql
    assert sql['database_type'] == 'MySQL'
    assert sql['user'] == MYSQL_USER
    assert sql['driver_version'] == 'PyMySQL'
    assert sql['database_version']


def test_execute_bad_query():
    q = "SELECT blarg"
    conn = pymysql.connect(database=MYSQL_DB_NAME,
                          user=MYSQL_USER,
                          password=MYSQL_PASSWORD,
                          host=MYSQL_HOST,
                          port=MYSQL_PORT)
    cur = conn.cursor()
    try:
        cur.execute(q)
    except Exception:
        pass
    
    subsegment = xray_recorder.current_segment().subsegments[-1]
    assert subsegment.name == "execute"
    sql = subsegment.sql
    assert sql['database_type'] == 'MySQL'
    assert sql['user'] == MYSQL_USER
    assert sql['driver_version'] == 'PyMySQL'
    assert sql['database_version']

    exception = subsegment.cause['exceptions'][0]
    assert exception.type is not None
