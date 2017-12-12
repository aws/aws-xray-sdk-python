import aws_xray_sdk
from aws_xray_sdk.core import xray_recorder


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
        c = xray_recorder._context
        if getattr(c._local, 'entities', None) is not None:
            trace = xray_recorder.begin_subsegment(class_name+'.'+func.__name__)
        else:
            trace = None
        res = func(*args, **kw)
        if trace is not None:
            if class_name == 'sqlalchemy.orm.query':
                for arg in args:
                    if isinstance(arg, aws_xray_sdk.ext.sqlalchemy.query.XRayQuery):
                        trace.put_metadata("sql", str(arg))
            xray_recorder.end_subsegment()
        return res
    return wrapper
