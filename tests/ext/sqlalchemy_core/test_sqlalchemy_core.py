from .test_base import User, session, db_url, engine, connection
from sqlalchemy.sql.expression import Insert, Delete
from aws_xray_sdk.core import xray_recorder

def test_all(session):
    """ Test calling all() on get all records.
    Verify we run the query and return the SQL as metdata"""
    session.query(User).all()
    assert len(xray_recorder.current_segment().subsegments) == 1
    sql_meta = xray_recorder.current_segment().subsegments[0].sql
    assert sql_meta['url'] == 'sqlite:///:memory:'
    assert sql_meta['sanitized_query'].startswith('SELECT')
    assert sql_meta['sanitized_query'].endswith('FROM users')


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
