from .test_base import User, session, engine, connection
from sqlalchemy.sql.expression import select
from aws_xray_sdk.core import xray_recorder

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
