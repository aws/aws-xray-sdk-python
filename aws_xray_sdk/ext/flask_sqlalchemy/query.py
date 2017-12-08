from __future__ import print_function
from builtins import super
import aws_xray_sdk
from aws_xray_sdk.core import xray_recorder
from sqlalchemy.orm.base import _generative
from sqlalchemy.orm.query import Query
from flask_sqlalchemy.model import Model
from sqlalchemy.orm.session import Session, sessionmaker
from functools import wraps
from flask_sqlalchemy import SQLAlchemy, BaseQuery, _SessionSignalEvents, get_state
from aws_xray_sdk.ext.sqlalchemy.query import XRaySession, XRayQuery

def decorate_all_functions(function_decorator):
    def decorator(cls):
        parent = cls.__bases__
        method_list = []
        for c in cls.__bases__:
            # method_list = [func for func in dir(c) if callable(getattr(c, func))]
            for name, obj in vars(c).items():
                if name.startswith("_"):
                    continue
                if callable(obj):
                    try:
                        obj = obj.__func__  # unwrap Python 2 unbound method
                    except AttributeError:
                        pass  # not needed in Python 3
                    setattr(c, name, function_decorator(c, obj))
        return cls
    return decorator

def xray_on_call(cls, func):
    def wrapper(*args, **kw):
        class_name = str(cls.__module__)
        sub = xray_recorder.begin_subsegment(class_name+'.'+func.__name__)
        res = func(*args, **kw)
        if class_name == 'sqlalchemy.orm.query':
            for arg in args:
                if isinstance(arg, aws_xray_sdk.ext.sqlalchemy.query.XRayQuery):
                    sub.put_metadata("sql", str(arg));
        xray_recorder.end_subsegment()
        return res
    return wrapper
    
@decorate_all_functions(xray_on_call)   
class XRayBaseQuery(BaseQuery):
    BaseQuery.__bases__ = (XRayQuery,)

class XRaySignallingSession(XRaySession):
    """The signalling session is the default session that Flask-SQLAlchemy
    uses.  It extends the default session system with bind selection and
    modification tracking.
    If you want to use a different session you can override the
    :meth:`SQLAlchemy.create_session` function.
    .. versionadded:: 2.0
    .. versionadded:: 2.1
        The `binds` option was added, which allows a session to be joined
        to an external transaction.
    """

    def __init__(self, db, autocommit=False, autoflush=True, **options):
        #: The application that this session belongs to.
        self.app = app = db.get_app()
        track_modifications = app.config['SQLALCHEMY_TRACK_MODIFICATIONS']
        bind = options.pop('bind', None) or db.engine
        binds = options.pop('binds', db.get_binds(app))

        if track_modifications is None or track_modifications:
            _SessionSignalEvents.register(self)

        XRaySession.__init__(
            self, autocommit=autocommit, autoflush=autoflush,
            bind=bind, binds=binds, **options
        )

    def get_bind(self, mapper=None, clause=None):
        # mapper is None if someone tries to just get a connection
        if mapper is not None:
            info = getattr(mapper.mapped_table, 'info', {})
            bind_key = info.get('bind_key')
            if bind_key is not None:
                state = get_state(self.app)
                return state.db.get_engine(self.app, bind=bind_key)
        return XRaySession.get_bind(self, mapper, clause)

class XRayFlaskSqlAlchemy(SQLAlchemy):
    def __init__(self, app=None, use_native_unicode=True, session_options=None,
                 metadata=None, query_class=XRayBaseQuery, model_class=Model):
        super().__init__(app, use_native_unicode, session_options,
              metadata, query_class, model_class)
                     
    def create_session(self, options):
         return sessionmaker(class_=XRaySignallingSession, db=self, **options)

# class XRayBaseQuery2(BaseQuery):
#     # Start Flask SqlAlchemy BaseQuery
#     BaseQuery.__bases__ = (XRayQuery,)
#     @xray_recorder.capture('FlaskSQLAlchemy-get_or_404')
#     def get_or_404(self, ident):
#         xray_recorder.current_subsegment().put_metadata("sql", str(self));
#         return super().get_or_404(ident)
    
#     @xray_recorder.capture('FlaskSQLAlchemy-first_or_404')
#     def first_or_404(self):
#         xray_recorder.current_subsegment().put_metadata("sql", str(self));
#         return super().first_or_404()
    
#     @xray_recorder.capture('FlaskSQLAlchemy-paginate')
#     def paginate(self, page=None, per_page=None, error_out=True, max_per_page=None):
#         xray_recorder.current_subsegment().put_metadata("sql", str(self));
#         return super().paginate(page, per_page, error_out, max_per_page)
