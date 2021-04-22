from __future__ import absolute_import

import pytest
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.expression import Insert, Delete, select

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


# 2.0 style execution test. see https://docs.sqlalchemy.org/en/14/changelog/migration_14.html#orm-query-is-internally
# -unified-with-select-update-delete-2-0-style-execution-available
def test_orm_style_select_execution(session):
    statement = select(User).where(
        User.name == 'John'
    )
    session.execute(statement)
    assert len(xray_recorder.current_segment().subsegments) == 1
    sql_meta = xray_recorder.current_segment().subsegments[0].sql
    assert sql_meta['sanitized_query'].startswith('SELECT')
    assert 'FROM users' in sql_meta['sanitized_query']
