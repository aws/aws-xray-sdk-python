import django

import pytest

from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core.context import Context
from aws_xray_sdk.ext.django.db import patch_db


@pytest.fixture(scope='module', autouse=True)
def setup():
    django.setup()
    xray_recorder.configure(context=Context())
    patch_db()


@pytest.fixture(scope='module')
def user_class(setup):
    from django.db import models
    from django_fake_model import models as f

    class User(f.FakeModel):
        name = models.CharField(max_length=255)
        password = models.CharField(max_length=255)

    return User


@pytest.fixture(
    autouse=True,
    params=[
        False,
        True,
    ]
)
@pytest.mark.django_db
def func_setup(request, user_class):
    xray_recorder.stream_sql = request.param
    xray_recorder.clear_trace_entities()
    xray_recorder.begin_segment('name')
    try:
        user_class.create_table()
        yield
    finally:
        xray_recorder.clear_trace_entities()
        try:
            user_class.delete_table()
        finally:
            xray_recorder.end_segment()


def _assert_query(sql_meta):
    if xray_recorder.stream_sql:
        assert 'sanitized_query' in sql_meta
        assert sql_meta['sanitized_query']
        assert sql_meta['sanitized_query'].startswith('SELECT')
    else:
        if 'sanitized_query' in sql_meta:
            assert sql_meta['sanitized_query']
            # Django internally executes queries for table checks, ignore those
            assert not sql_meta['sanitized_query'].startswith('SELECT')


def test_all(user_class):
    """ Test calling all() on get all records.
    Verify we run the query and return the SQL as metadata"""
    # Materialising the query executes the SQL
    list(user_class.objects.all())
    subsegment = xray_recorder.current_segment().subsegments[-1]
    sql = subsegment.sql
    assert sql['database_type'] == 'sqlite'
    _assert_query(sql)


def test_filter(user_class):
    """ Test calling filter() to get filtered records.
    Verify we run the query and return the SQL as metadata"""
    # Materialising the query executes the SQL
    list(user_class.objects.filter(password='mypassword!').all())
    subsegment = xray_recorder.current_segment().subsegments[-1]
    sql = subsegment.sql
    assert sql['database_type'] == 'sqlite'
    _assert_query(sql)
    if xray_recorder.stream_sql:
        assert 'mypassword!' not in sql['sanitized_query']
        assert '"password" = %s' in sql['sanitized_query']
