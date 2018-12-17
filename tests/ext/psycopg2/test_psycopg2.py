import psycopg2
import psycopg2.extras
import psycopg2.pool

import pytest
import testing.postgresql

from aws_xray_sdk.core import patch
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core.context import Context

patch(('psycopg2',))


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
    with testing.postgresql.Postgresql() as postgresql:
        url = postgresql.url()
        dsn = postgresql.dsn()
        conn = psycopg2.connect(dbname=dsn['database'],
                                user=dsn['user'],
                                password='',
                                host=dsn['host'],
                                port=dsn['port'])
        cur = conn.cursor()
        cur.execute(q)

    subsegment = xray_recorder.current_segment().subsegments[-1]
    assert subsegment.name == 'execute'
    sql = subsegment.sql
    assert sql['database_type'] == 'PostgreSQL'
    assert sql['user'] == dsn['user']
    assert sql['url'] == url
    assert sql['database_version']


def test_execute_dsn_kwargs_alt_dbname():
    """
    Psycopg supports database to be passed as `database` or `dbname`
    """
    q = 'SELECT 1'

    with testing.postgresql.Postgresql() as postgresql:
        url = postgresql.url()
        dsn = postgresql.dsn()
        conn = psycopg2.connect(database=dsn['database'],
                                user=dsn['user'],
                                password='',
                                host=dsn['host'],
                                port=dsn['port'])
        cur = conn.cursor()
        cur.execute(q)

    subsegment = xray_recorder.current_segment().subsegments[-1]
    assert subsegment.name == 'execute'
    sql = subsegment.sql
    assert sql['database_type'] == 'PostgreSQL'
    assert sql['user'] == dsn['user']
    assert sql['url'] == url
    assert sql['database_version']


def test_execute_dsn_string():
    q = 'SELECT 1'
    with testing.postgresql.Postgresql() as postgresql:
        url = postgresql.url()
        dsn = postgresql.dsn()
        conn = psycopg2.connect('dbname=' + dsn['database'] +
                                ' password=mypassword' +
                                ' host=' + dsn['host'] +
                                ' port=' + str(dsn['port']) +
                                ' user=' + dsn['user'])
        cur = conn.cursor()
        cur.execute(q)

    subsegment = xray_recorder.current_segment().subsegments[-1]
    assert subsegment.name == 'execute'
    sql = subsegment.sql
    assert sql['database_type'] == 'PostgreSQL'
    assert sql['user'] == dsn['user']
    assert sql['url'] == url
    assert sql['database_version']


def test_execute_in_pool():
    q = 'SELECT 1'
    with testing.postgresql.Postgresql() as postgresql:
        url = postgresql.url()
        dsn = postgresql.dsn()
        pool = psycopg2.pool.SimpleConnectionPool(1, 1,
                                                  dbname=dsn['database'],
                                                  user=dsn['user'],
                                                  password='',
                                                  host=dsn['host'],
                                                  port=dsn['port'])
        cur = pool.getconn(key=dsn['user']).cursor()
        cur.execute(q)

    subsegment = xray_recorder.current_segment().subsegments[-1]
    assert subsegment.name == 'execute'
    sql = subsegment.sql
    assert sql['database_type'] == 'PostgreSQL'
    assert sql['user'] == dsn['user']
    assert sql['url'] == url
    assert sql['database_version']


def test_execute_bad_query():
    q = 'SELECT blarg'
    with testing.postgresql.Postgresql() as postgresql:
        url = postgresql.url()
        dsn = postgresql.dsn()
        conn = psycopg2.connect(dbname=dsn['database'],
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
    assert subsegment.name == 'execute'
    sql = subsegment.sql
    assert sql['database_type'] == 'PostgreSQL'
    assert sql['user'] == dsn['user']
    assert sql['url'] == url
    assert sql['database_version']

    exception = subsegment.cause['exceptions'][0]
    assert exception.type == 'ProgrammingError'


def test_register_extensions():
    with testing.postgresql.Postgresql() as postgresql:
        url = postgresql.url()
        dsn = postgresql.dsn()
        conn = psycopg2.connect('dbname=' + dsn['database'] +
                                ' password=mypassword' +
                                ' host=' + dsn['host'] +
                                ' port=' + str(dsn['port']) +
                                ' user=' + dsn['user'])
        assert psycopg2.extras.register_uuid(None, conn)
        assert psycopg2.extras.register_uuid(None, conn.cursor())
