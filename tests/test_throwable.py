import pytest

from aws_xray_sdk.core.models import throwable
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


SECRET = 'stored-secret-value'


class _OperationFailure(Exception):
    """A pymongo error with the server error document"""
    __module__ = 'pymongo.errors'

    def __init__(self, message, details):
        super().__init__(message if details is None else '{}, full error: {}'.format(message, details))
        self.details = details


def test_pymongo_error_document_values():
    errmsg = 'E11000 duplicate key error collection: db.users index: email_1 dup key: { email: "%s" }' % SECRET
    error = _OperationFailure(errmsg, {
        'ok': 0.0, 'errmsg': errmsg, 'code': 11000, 'codeName': 'DuplicateKey', 'errorLabels': ['label'],
        'keyPattern': {'email': 1}, 'keyValue': {'email': SECRET}, 'idx': SECRET,
        'writeErrors': [{'index': 0, 'code': 11000, 'op': {'email': SECRET}}, SECRET],
        'writeConcernError': {'code': 64, 'codeName': 'WriteConcernFailed', 'errInfo': {'wtimeout': True}},
        'writeConcernErrors': [{'code': 64, 'index': SECRET}],
    })

    # like the failure metadata, only fields that never contain document values are kept
    assert Throwable(error, None).message == (
        "E11000 duplicate key error collection: db.users index: email_1 dup key: REDACTED, full error: "
        "{'ok': 0.0, 'errmsg': 'REDACTED', 'code': 11000, 'codeName': 'DuplicateKey', 'errorLabels': ['label'], "
        "'keyPattern': 'REDACTED', 'keyValue': 'REDACTED', 'idx': 'REDACTED', "
        "'writeErrors': [{'index': 0, 'code': 11000, 'op': 'REDACTED'}, 'REDACTED'], "
        "'writeConcernError': {'code': 64, 'codeName': 'WriteConcernFailed', 'errInfo': 'REDACTED'}, "
        "'writeConcernErrors': [{'code': 64, 'index': 'REDACTED'}]}")


def test_pymongo_validation_error_values():
    error = _OperationFailure('Document failed validation', {
        'ok': 0.0, 'errmsg': 'Document failed validation', 'code': 121, 'codeName': 'DocumentValidationFailure',
        'errInfo': {'details': {'operatorName': '$jsonSchema', 'consideredValue': SECRET}},
    })

    assert Throwable(error, None).message == (
        "Document failed validation, full error: {'ok': 0.0, 'errmsg': 'REDACTED', 'code': 121, "
        "'codeName': 'DocumentValidationFailure', 'errInfo': 'REDACTED'}")


def test_pymongo_errors_caused_by_other_errors():
    class EncryptionError(Exception):
        """A pymongo error with the message of the error that caused it"""
        __module__ = 'pymongo.errors'

    try:
        try:
            raise _OperationFailure('Document failed validation', {'code': 121, 'errInfo': {'consideredValue': SECRET}})
        except _OperationFailure as e:
            raise EncryptionError(str(e)) from e
    except EncryptionError as error:
        assert Throwable(error, None).message == (
            "Document failed validation, full error: {'code': 121, 'errInfo': 'REDACTED'}")


def test_pymongo_errors_with_the_document_of_another_error():
    class NetworkTimeout(Exception):
        """A pymongo error with the message of another error, and errors as details"""
        __module__ = 'pymongo.errors'
        details = []

    class EncryptionError(Exception):
        """A pymongo error with the message of the error that caused it"""
        __module__ = 'pymongo.errors'

        def __init__(self, cause):
            super().__init__(str(cause))
            self.cause = cause

    cause = _OperationFailure('Write conflict', {'code': 112, 'keyValue': {'token': SECRET}})
    recorded = "Write conflict, full error: {'code': 112, 'keyValue': 'REDACTED'}"
    try:
        raise NetworkTimeout(str(cause)) from cause
    except NetworkTimeout as error:
        assert Throwable(error, None).message == recorded
    assert Throwable(EncryptionError(cause), None).message == recorded


def test_pymongo_errors_without_error_document():
    # e.g. a ServerSelectionTimeoutError with the errors of its servers
    message = 'No primary available, Topology: <NotPrimaryError("not primary, full error: {\'code\': 10107}")>, ...'
    error = _OperationFailure(message, None)
    duplicate_key_error = _OperationFailure('E11000 dup key: { email: "a, full error: %s" }' % SECRET, None)

    assert Throwable(error, None).message == message
    assert Throwable(duplicate_key_error, None).message == 'E11000 dup key: REDACTED'


def test_malformed_stack():
    throwable = Throwable(Exception('why'), 'a')

    assert throwable.stack is None and throwable.message == 'why'


def test_pymongo_error_subclasses():
    class TenantWriteError(_OperationFailure):
        __module__ = 'myapp.errors'

    class _Error(Exception):
        pass
    _Error.__module__ = None

    error = TenantWriteError('Document failed validation', {'code': 121, 'errInfo': {'consideredValue': SECRET}})

    assert Throwable(error, None).message == (
        "Document failed validation, full error: {'code': 121, 'errInfo': 'REDACTED'}")
    assert Throwable(_Error('why'), None).message == 'why'


def test_pymongo_errors_with_full_documents(monkeypatch):
    # e.g. with a pymongo listener that records full documents
    monkeypatch.setattr(throwable, '_REDACTION_RULES', throwable._REDACTION_RULES)
    throwable._record_full_pymongo_documents()
    error = _OperationFailure('Document failed validation', {'code': 121, 'errInfo': {'consideredValue': SECRET}})
    url_error = Exception('Max retries exceeded with url: /key?token=' + SECRET)

    assert SECRET in Throwable(error, None).message
    assert Throwable(url_error, None).message == 'Max retries exceeded with url: /key?token=REDACTED'


def test_url_query_values():
    assert Throwable(Exception('Max retries exceeded with url: /key?token=' + SECRET), None).message == (
        'Max retries exceeded with url: /key?token=REDACTED')


def test_details_of_other_errors():
    class _APIError(Exception):
        @property
        def details(self):
            raise KeyError('details')

    assert Throwable(_APIError('upstream failed with 503, full error: none'), None).message == (
        'upstream failed with 503, full error: none')


def test_redaction_rules(monkeypatch):
    def redact_token(exception, message):
        return message.replace(SECRET, 'REDACTED')

    monkeypatch.setattr(throwable, '_REDACTION_RULES', throwable._REDACTION_RULES + (redact_token,))

    assert Throwable(Exception('token ' + SECRET), None).message == 'token REDACTED'


def test_message_not_recorded_when_redaction_fails(monkeypatch):
    def fail(exception, message):
        raise ValueError()

    monkeypatch.setattr(throwable, '_REDACTION_RULES', (fail,))

    assert not hasattr(Throwable(Exception('token ' + SECRET), None), 'message')
