from sqlalchemy import create_engine
import urllib
import pytest

from aws_xray_sdk.core import xray_recorder, patch
from aws_xray_sdk.ext.sqlalchemy_core import unpatch
from aws_xray_sdk.core.context import Context

MYSQL_USER = "test_dburl_user"
MYSQL_PASSWORD = "test]password"
MYSQL_HOST = "localhost"
MYSQL_PORT = 3306
MYSQL_DB_NAME = "test_dburl"

patch(('sqlalchemy_core',))

@pytest.fixture(autouse=True)
def construct_ctx():
    """
    Clean up context storage on each test run and begin a segment
    so that later subsegment can be attached. After each test run
    it cleans up context storage again.
    """
    xray_recorder.configure(service='test', sampling=False, context=Context())
    xray_recorder.clear_trace_entities()
    xray_recorder.begin_segment('name')
    yield
    xray_recorder.clear_trace_entities()


def test_db_url_with_special_char():
    password = urllib.parse.quote_plus(MYSQL_PASSWORD)
    db_url = f"mysql+pymysql://{MYSQL_USER}:{password}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB_NAME}"

    engine = create_engine(db_url)

    conn = engine.connect()

    conn.execute("select 1")

    subsegment = xray_recorder.current_segment().subsegments[-1]

    assert subsegment.name == f"{MYSQL_HOST}:{MYSQL_PORT}"
    sql = subsegment.sql
    assert sql['database_type'] == 'mysql'
    assert sql['user'] == MYSQL_USER
    assert sql['driver_version'] == 'pymysql'
    assert sql['database_version']
