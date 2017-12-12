from __future__ import absolute_import
import pytest
import json
import jsonpickle
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core.context import Context
from aws_xray_sdk.ext.sqlalchemy.query import XRaySessionMaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Column, Integer, String
# from sqlalchemy.orm import sessionmaker


Base = declarative_base()


class User(Base):
        __tablename__ = 'users'

        id = Column(Integer, primary_key=True)
        name = Column(String)
        fullname = Column(String)
        password = Column(String)


def _search_entity(entity, name):
    """Helper function to that recursivly looks at subentities
    Returns a serialized entity that matches the name given or None"""
    if 'name' in entity:
        my_name = entity['name']
        if my_name == name:
            return entity
        else:
            if "subsegments" in entity:
                for s in entity['subsegments']:
                    result = _search_entity(s, name)
                    if result is not None:
                        return result
    return None


def find_sub(segment, name):
    """Helper function to find a subsegment by name in the entity tree"""
    segment = jsonpickle.encode(segment, unpicklable=False)
    segment = json.loads(segment)
    for entity in segment['subsegments']:
        result = _search_entity(entity, name)
        if result is not None:
            return result
    return None


@pytest.fixture()
def session():
    """Test Fixture to Create DataBase Tables and start a trace segment"""
    engine = create_engine('sqlite:///:memory:')
    xray_recorder.configure(service='test', sampling=False, context=Context())
    xray_recorder.clear_trace_entities()
    xray_recorder.begin_segment('SQLAlchemyTest')
    Session = XRaySessionMaker(bind=engine)
    Base.metadata.create_all(engine)
    session = Session()
    yield session
    xray_recorder.end_segment()
    xray_recorder.clear_trace_entities()


def test_all(capsys, session):
    """ Test calling all() on get all records.
    Verify we run the query and return the SQL as metdata"""
    # with capsys.disabled():
    session.query(User).all()
    sub = find_sub(xray_recorder.current_segment(), 'sqlalchemy.orm.query.all')
    assert sub['name'] == 'sqlalchemy.orm.query.all'
    assert sub['metadata']['default']['sql']


def test_add(capsys, session):
    """ Test calling add() on insert a row.
    Verify we that we capture trace for the add"""
    # with capsys.disabled():
    john = User(name='John', fullname="John Doe", password="password")
    session.add(john)
    sub = find_sub(xray_recorder.current_segment(), 'sqlalchemy.orm.session.add')
    assert sub['name'] == 'sqlalchemy.orm.session.add'
