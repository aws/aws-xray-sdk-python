import inspect
import sys


PY2 = sys.version_info < (3,)
PY35 = sys.version_info >= (3, 5)

if PY2:
    annotation_value_types = (int, long, float, bool, str, unicode)  # noqa: F821
    string_types = basestring  # noqa: F821
else:
    annotation_value_types = (int, float, bool, str)
    string_types = str


def is_classmethod(func):
    return getattr(func, '__self__', None) is not None


def is_instance_method(parent_class, func_name, func):
    try:
        func_from_dict = parent_class.__dict__[func_name]
    except KeyError:
        for base in inspect.getmro(parent_class):
            if func_name in base.__dict__:
                func_from_dict = base.__dict__[func_name]
                break
        else:
            return True

    return not is_classmethod(func) and not isinstance(func_from_dict, staticmethod)
