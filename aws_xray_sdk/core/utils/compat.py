import sys


PY2 = sys.version_info < (3,)

if PY2:
    annotation_value_types = (int, long, float, bool, str)  # noqa: F821
    string_types = basestring  # noqa: F821
else:
    annotation_value_types = (int, float, bool, str)
    string_types = str
