from __future__ import print_function
from builtins import super
from flask_sqlalchemy import BaseQuery
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.ext.sqlalchemy.query import XRayQuery

from functools import wraps

class XRayBaseQuery(BaseQuery):
    # Start Flask SqlAlchemy BaseQuery
    BaseQuery.__bases__ = (XRayQuery,)
    @xray_recorder.capture('FlaskSQLAlchemy-get_or_404')
    def get_or_404(self, ident):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().get_or_404(ident)
    
    @xray_recorder.capture('FlaskSQLAlchemy-first_or_404')
    def first_or_404(self):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().first_or_404()
    
    @xray_recorder.capture('FlaskSQLAlchemy-paginate')
    def paginate(self, page=None, per_page=None, error_out=True, max_per_page=None):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().paginate(page, per_page, error_out, max_per_page)
