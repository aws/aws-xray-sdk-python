from __future__ import absolute_import
import pytest
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core.context import Context
from aws_xray_sdk.ext.sqlalchemy.query import XRaySessionMaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import *
# from sqlalchemy.orm import sessionmaker



Base = declarative_base()

class User(Base):
        __tablename__ = 'users'

        id = Column(Integer, primary_key=True)
        name = Column(String)
        fullname = Column(String)
        password = Column(String)
        
@pytest.fixture()
def session():
    engine = create_engine('sqlite:///:memory:')
    xray_recorder.configure(service='test', sampling=False, context=Context())
    xray_recorder.clear_trace_entities()
    xray_recorder.begin_segment('SQLAlchemyTest')
    Session = XRaySessionMaker(bind=engine)
    # Session.configure(bind=engine)
    # Session.configure()
    Base.metadata.create_all(engine)
    session = Session()
    yield session
    xray_recorder.end_segment()
    xray_recorder.clear_trace_entities()
    

def test_all(capsys, session):
    with capsys.disabled():
        try:
            session.query(User).all()
        except Exception:
            pass
        # print(xray_recorder.current_segment().subsegments[0].__dict__)
        # for sub in xray_recorder.current_segment().subsegments:
        #     print(sub.__dict__)
        subsegment = xray_recorder.current_segment().subsegments[-1]
        assert subsegment.name == 'sqlalchemy.orm.query.all'
        assert subsegment.metadata['default']['sql']
    # print(xray_recorder.current_segment().subsegments[0].__dict__)


def test_add(capsys, session):
    with capsys.disabled():
        john = User(name='John', fullname = "John Doe", password="password")
        session.add(john)
        # for sub in xray_recorder.current_segment().subsegments:
        #     print(sub.__dict__)
        subsegment = xray_recorder.current_segment().subsegments[-1]
        assert subsegment.name == 'sqlalchemy.orm.session.add'
        # assert subsegment.metadata['default']['sql']
        
        