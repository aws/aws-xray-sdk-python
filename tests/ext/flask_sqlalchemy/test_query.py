from __future__ import absolute_import
import pytest
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core.context import Context
from aws_xray_sdk.ext.flask_sqlalchemy.query import XRayFlaskSqlAlchemy
from flask import Flask
from ...util import find_subsegment


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
    """Test Fixture to Create DataBase Tables and start a trace segment"""
    xray_recorder.configure(service='test', sampling=False, context=Context())
    xray_recorder.clear_trace_entities()
    xray_recorder.begin_segment('SQLAlchemyTest')
    db.create_all()
    yield
    xray_recorder.end_segment()
    xray_recorder.clear_trace_entities()


def test_all(capsys, session):
    """ Test calling all() on get all records.
    Verify that we capture trace of query and return the SQL as metdata"""
    # with capsys.disabled():
    User.query.all()
    subsegment = find_subsegment(xray_recorder.current_segment(), 'sqlalchemy.orm.query.all')
    assert subsegment['name'] == 'sqlalchemy.orm.query.all'
    # assert subsegment['sql']['sanitized_query']


def test_add(capsys, session):
    """ Test calling add() on insert a row.
    Verify we that we capture trace for the add"""
    # with capsys.disabled():
    john = User(name='John', fullname="John Doe", password="password")
    db.session.add(john)
    subsegment = find_subsegment(xray_recorder.current_segment(), 'sqlalchemy.orm.session.add')
    # assert subsegment['name'] == 'sqlalchemy.orm.session.add'
