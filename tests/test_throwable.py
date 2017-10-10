from aws_xray_sdk.core.models.throwable import Throwable


def test_message_and_type():

    e = TypeError('msg')
    throwable = Throwable(e, None, True)
    assert throwable.message == 'msg'
    assert throwable.type == type(e).__name__
    assert throwable.remote


def test_stack_trace_parsing():
    # sample output using `traceback.extract_stack()`
    stack = [
        ('/path/to/test.py', 10, 'module', 'another_function()'),
        ('/path/to/test.py', 3, 'another_function', 'wrong syntax'),
    ]

    throwable = Throwable(TypeError(), stack)

    entry1 = throwable.stack[0]
    assert entry1['path'] == 'test.py'
    assert entry1['line'] == 10
    assert entry1['label'] == 'module'

    entry2 = throwable.stack[1]
    assert entry2['path'] == 'test.py'
    assert entry2['line'] == 3
    assert entry2['label'] == 'another_function'
