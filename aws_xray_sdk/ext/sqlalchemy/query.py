from __future__ import print_function
from builtins import super
import aws_xray_sdk
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core.context import Context
from sqlalchemy.orm.base import _generative
from sqlalchemy.orm.query import Query
from sqlalchemy.orm.session import Session, sessionmaker
from functools import wraps


def decorate_all_functions(function_decorator):
    def decorator(cls):
        for c in cls.__bases__:
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
        if xray_recorder.current_segment is None:
            trace = xray_recorder.begin_segment(class_name+'.'+func.__name__)
        else:
             trace = xray_recorder.begin_subsegment(class_name+'.'+func.__name__)
        res = func(*args, **kw)
        if class_name == 'sqlalchemy.orm.query':
            for arg in args:
                if isinstance(arg, aws_xray_sdk.ext.sqlalchemy.query.XRayQuery):
                    trace.put_metadata("sql", str(arg));
        c = Context()
        if c._is_subsegment(trace):
            xray_recorder.end_subsegment()
        else:
            xray_recorder.end_segment()
        return res
    return wrapper
    
@decorate_all_functions(xray_on_call)   
class XRaySession(Session):
    pass

@decorate_all_functions(xray_on_call)   
class XRayQuery(Query):
    pass

@decorate_all_functions(xray_on_call)
class XRaySessionMaker(sessionmaker):
    def __init__(self, bind=None, class_=XRaySession, autoflush=True,
                 autocommit=False,
                 expire_on_commit=True,
                 info=None, **kw):
        kw['query_cls'] = XRayQuery
        super().__init__(bind, class_, autoflush, autocommit, expire_on_commit,
                         info, **kw)