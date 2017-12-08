from __future__ import absolute_import
import pytest
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core.context import Context
from aws_xray_sdk.ext.sqlalchemy.query import XRayQuery, XRaySession
from aws_xray_sdk.ext.flask_sqlalchemy.query import XRayFlaskSqlAlchemy
from flask import Flask
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
db = XRayFlaskSqlAlchemy(app)
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    fullname = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)


@pytest.fixture()
def session():

    xray_recorder.configure(service='test', sampling=False, context=Context())
    xray_recorder.clear_trace_entities()
    xray_recorder.begin_segment('SQLAlchemyTest')


    db.create_all()
    yield
    xray_recorder.end_segment()
    xray_recorder.clear_trace_entities()
    

def test_all(capsys, session):
    with capsys.disabled():
        try:
            User.query.all()
        except Exception:
            raise
        # print(xray_recorder.current_segment().subsegments[0].__dict__)
        # for sub in xray_recorder.current_segment().subsegments:
        #     print(sub.__dict__)
        subsegment = xray_recorder.current_segment().subsegments[-1]
        assert subsegment.name == 'sqlalchemy.orm.query.all'
        assert subsegment.metadata['default']['sql']
    # print(xray_recorder.current_segment().subsegments[0].__dict__)


# def test_add(capsys, session):
#     with capsys.disabled():
#         john = User(name='John', fullname = "John Doe", password="password")
#         session.add(john)
#         for sub in xray_recorder.current_segment().subsegments:
#             print(sub.__dict__)
#         subsegment = xray_recorder.current_segment().subsegments[-1]
#         assert subsegment.name == 'sqlalchemy.orm.session.add'
#         # assert subsegment.metadata['default']['sql']
        
        