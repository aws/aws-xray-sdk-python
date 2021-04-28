import pytest

from .test_base import connection, User, session, Base

from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import insert as pg_insert

from aws_xray_sdk.core import xray_recorder, patch
from aws_xray_sdk.core.context import Context

import testing.postgresql


@pytest.fixture()
def postgres_db():
    with testing.postgresql.Postgresql() as postgresql:
        yield postgresql


@pytest.fixture()
def sanitized_db_url(postgres_db):
    dsn = postgres_db.dsn()
    return 'postgresql://{user}@{host}:{port}/{db}'.format(
        user=dsn['user'],
        host=dsn['host'],
        port=dsn['port'],
        db=dsn['database'],
    )


@pytest.fixture()
def engine(postgres_db):
    """
    Clean up context storage on each test run and begin a segment
    so that later subsegment can be attached. After each test run
    it cleans up context storage again.
    """
    from aws_xray_sdk.ext.sqlalchemy_core import unpatch
    patch(('sqlalchemy_core',))
    engine = create_engine(postgres_db.url())
    xray_recorder.configure(service='test', sampling=False, context=Context())
    xray_recorder.begin_segment('name')
    Base.metadata.create_all(engine)
    xray_recorder.clear_trace_entities()
    xray_recorder.begin_segment('name')
    yield engine
    xray_recorder.clear_trace_entities()
    unpatch()


def test_all(session, sanitized_db_url):
    """ Test calling all() on get all records.
    Verify we run the query and return the SQL as metdata"""
    session.query(User).all()
    assert len(xray_recorder.current_segment().subsegments) == 1
    sql_meta = xray_recorder.current_segment().subsegments[0].sql
    assert sql_meta['url'] == sanitized_db_url
    assert sql_meta['sanitized_query'].startswith('SELECT')
    assert sql_meta['sanitized_query'].endswith('FROM users')


def test_insert_on_conflict_renders(connection):
    statement = pg_insert(User).values(name='John', fullname="John Doe", password='123456')
    statement = statement.on_conflict_do_nothing()

    connection.execute(statement)

    assert len(xray_recorder.current_segment().subsegments) == 1
    sql_meta = xray_recorder.current_segment().subsegments[0].sql

    assert sql_meta['sanitized_query'].startswith('INSERT INTO users')
    assert 'ON CONFLICT DO NOTHING' in sql_meta['sanitized_query']
