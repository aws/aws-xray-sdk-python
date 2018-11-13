import sys


PY2 = sys.version_info < (3,)
PY35 = sys.version_info >= (3, 5)

if PY2:
    annotation_value_types = (int, long, float, bool, str)  # noqa: F821
    string_types = basestring  # noqa: F821
else:
    annotation_value_types = (int, float, bool, str)
    string_types = str


def is_instance_method(parent_class, func_name, func):
    return getattr(func, '__self__', None) is None and not isinstance(parent_class.__dict__[func_name], staticmethod)
