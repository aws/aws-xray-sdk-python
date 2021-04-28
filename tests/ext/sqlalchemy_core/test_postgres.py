import pytest

from .test_base import connection, engine, session, User

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
def db_url(postgres_db):
    return postgres_db.url()


@pytest.fixture()
def sanitized_db_url(postgres_db):
    dsn = postgres_db.dsn()
    return 'postgresql://{user}@{host}:{port}/{db}'.format(
        user=dsn['user'],
        host=dsn['host'],
        port=dsn['port'],
        db=dsn['database'],
    )


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
