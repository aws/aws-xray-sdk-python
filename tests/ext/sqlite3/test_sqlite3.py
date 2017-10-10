import sqlite3

import pytest

from aws_xray_sdk.core import patch
from aws_xray_sdk.core import xray_recorder

patch(('sqlite3',))
db = sqlite3.connect(":memory:")


@pytest.fixture(autouse=True)
def construct_ctx():
    """
    Clean up context storage on each test run and begin a segment
    so that later subsegment can be attached. After each test run
    it cleans up context storage again.
    """
    xray_recorder.clear_trace_entities()
    xray_recorder.begin_segment('name')
    yield
    xray_recorder.clear_trace_entities()


def test_execute():
    q = 'SELECT name FROM sqlite_master'
    db.execute(q)

    subsegment = xray_recorder.current_segment().subsegments[0]
    assert subsegment.name == ':memory:'
    sql = subsegment.sql
    assert sql['database_type'] == 'sqlite3'
    assert sql['database_version']


def test_invalid_syntax():
    q = 'some_query'
    try:
        db.execute(q)
    except Exception:
        pass

    subsegment = xray_recorder.current_segment().subsegments[0]
    assert subsegment.name == ':memory:'
    sql = subsegment.sql
    assert sql['database_type'] == 'sqlite3'
    assert sql['database_version']

    exception = subsegment.cause['exceptions'][0]
    assert exception.type == 'OperationalError'
