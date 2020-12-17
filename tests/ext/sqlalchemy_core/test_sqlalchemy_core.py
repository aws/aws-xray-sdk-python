from __future__ import absolute_import

import pytest
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.expression import Insert, Delete

from aws_xray_sdk.core import xray_recorder, patch
from aws_xray_sdk.core.context import Context

Base = declarative_base()


class User(Base):
        __tablename__ = 'users'

        id = Column(Integer, primary_key=True)
        name = Column(String)
        fullname = Column(String)
        password = Column(String)


@pytest.fixture()
def engine():
    """
    Clean up context storage on each test run and begin a segment
    so that later subsegment can be attached. After each test run
    it cleans up context storage again.
    """
    from aws_xray_sdk.ext.sqlalchemy_core import unpatch
    patch(('sqlalchemy_core',))
    engine = create_engine('sqlite:///:memory:')
    xray_recorder.configure(service='test', sampling=False, context=Context())
    xray_recorder.begin_segment('name')
    Base.metadata.create_all(engine)
    xray_recorder.clear_trace_entities()
    xray_recorder.begin_segment('name')
    yield engine
    xray_recorder.clear_trace_entities()
    unpatch()


@pytest.fixture()
def connection(engine):
    return engine.connect()


@pytest.fixture()
def session(engine):
    Session = sessionmaker(bind=engine)
    return Session()


def test_all(session):
    """ Test calling all() on get all records.
    Verify we run the query and return the SQL as metdata"""
    session.query(User).all()
    assert len(xray_recorder.current_segment().subsegments) == 1
    sql_meta = xray_recorder.current_segment().subsegments[0].sql
    assert sql_meta['url'] == 'sqlite:///:memory:'
    assert sql_meta['sanitized_query'].startswith('SELECT')
    assert sql_meta['sanitized_query'].endswith('FROM users')


def test_add(session):
    """ Test calling add() on insert a row.
    Verify we that we capture trace for the add"""
    password = "123456"
    john = User(name='John', fullname="John Doe", password=password)
    session.add(john)
    session.commit()
    assert len(xray_recorder.current_segment().subsegments) == 1
    sql_meta = xray_recorder.current_segment().subsegments[0].sql
    assert sql_meta['sanitized_query'].startswith('INSERT INTO users')
    assert password not in sql_meta['sanitized_query']


def test_filter_first(session):
    """ Test calling filter().first() on get first filtered records.
    Verify we run the query and return the SQL as metdata"""
    session.query(User).filter(User.password=="mypassword!").first()
    assert len(xray_recorder.current_segment().subsegments) == 1
    sql_meta = xray_recorder.current_segment().subsegments[0].sql
    assert sql_meta['sanitized_query'].startswith('SELECT')
    assert 'FROM users' in sql_meta['sanitized_query']
    assert "mypassword!" not in sql_meta['sanitized_query']


def test_connection_add(connection):
    password = "123456"
    statement = Insert(User).values(name='John', fullname="John Doe", password=password)
    connection.execute(statement)
    assert len(xray_recorder.current_segment().subsegments) == 1
    sql_meta = xray_recorder.current_segment().subsegments[0].sql
    assert sql_meta['sanitized_query'].startswith('INSERT INTO users')
    assert sql_meta['url'] == 'sqlite:///:memory:'
    assert password not in sql_meta['sanitized_query']

def test_connection_query(connection):
    password = "123456"
    statement = Delete(User).where(User.name == 'John').where(User.password == password)
    connection.execute(statement)
    assert len(xray_recorder.current_segment().subsegments) == 1
    sql_meta = xray_recorder.current_segment().subsegments[0].sql
    assert sql_meta['sanitized_query'].startswith('DELETE FROM users')
    assert sql_meta['url'] == 'sqlite:///:memory:'
    assert password not in sql_meta['sanitized_query']