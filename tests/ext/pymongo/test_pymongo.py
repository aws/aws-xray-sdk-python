from types import SimpleNamespace

import pytest
from bson import encode
from bson.raw_bson import RawBSONDocument
from pymongo import monitoring
from pymongo.errors import BulkWriteError, DuplicateKeyError, OperationFailure, WriteError

from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core.context import Context
from aws_xray_sdk.core.models import throwable
from aws_xray_sdk.ext.pymongo.patch import XrayCommandListener, patch

SECRET = 'stored-secret-value'

# $jsonSchema validation failure echoes the stored value in consideredValue
VALIDATION_FAILURE = {
    'ok': 0.0,
    'errmsg': 'Document failed validation',
    'code': 121,
    'codeName': 'DocumentValidationFailure',
    'errInfo': {
        'details': {
            'operatorName': '$jsonSchema',
            'schemaRulesNotSatisfied': [{
                'operatorName': 'properties',
                'propertiesNotSatisfied': [{
                    'propertyName': 'api_token',
                    'details': [{
                        'operatorName': 'pattern',
                        'specifiedAs': {'pattern': '^vaulted:'},
                        'reason': 'regular expression did not match',
                        'consideredValue': SECRET,
                    }],
                }],
            }],
        },
    },
}

DUPLICATE_KEY_FAILURE = {
    'ok': 0.0,
    'errmsg': 'E11000 duplicate key error collection: db.users index: '
              'token_1 dup key: { token: "%s" }' % SECRET,
    'code': 11000,
    'codeName': 'DuplicateKey',
    'keyPattern': {'token': 1},
    'keyValue': {'token': SECRET},
}

TRANSACTION_FAILURE = {
    'ok': 0.0,
    'errmsg': 'Caused by :: Write conflict during plan execution',
    'code': 112,
    'codeName': 'WriteConflict',
    'errorLabels': ['TransientTransactionError'],
}

# write concern errors have no `ok` field
WRITE_CONCERN_FAILURE = {
    'code': 64,
    'codeName': 'WriteConcernFailed',
    'errmsg': 'waiting for replication timed out',
    'errInfo': {'wtimeout': True},
    'errorLabels': ['RetryableWriteError'],
}

# failure document pymongo builds for client side errors
CLIENT_FAILURE = {
    'errmsg': 'localhost:27017: connection closed',
    'errtype': 'AutoReconnect',
}


@pytest.fixture(autouse=True)
def redact_exception_messages(monkeypatch):
    # listeners that record full documents record exception messages in full in the whole process
    monkeypatch.setattr(throwable, '_REDACTION_RULES', throwable._REDACTION_RULES)


@pytest.fixture(autouse=True)
def construct_ctx():
    """
    Clean up context storage on each test run and begin a segment
    so that later subsegment can be attached. After each test run
    it cleans up context storage again.
    """
    xray_recorder.configure(service='test', sampling=False, context=Context())
    xray_recorder.clear_trace_entities()
    xray_recorder.begin_segment('name')
    yield
    xray_recorder.clear_trace_entities()


def _started_event():
    return SimpleNamespace(
        connection_id=('localhost', 27017),
        database_name='db',
        command_name='findAndModify',
        operation_id=1,
        request_id=2,
        command={'findAndModify': 'users', 'update': {'$set': {'token': SECRET}}},
    )


def _run_failed(listener, failure):
    listener.started(_started_event())
    listener.failed(SimpleNamespace(duration_micros=10, failure=failure))
    return xray_recorder.current_segment().subsegments[0]


@pytest.mark.parametrize('failure', [VALIDATION_FAILURE, DUPLICATE_KEY_FAILURE])
def test_failed_does_not_record_document_values(failure):
    subsegment = _run_failed(XrayCommandListener(record_full_documents=False), failure)

    assert subsegment.fault
    assert subsegment.metadata['default']['failure'] == {
        'ok': 0.0,
        'code': failure['code'],
        'codeName': failure['codeName'],
    }
    assert SECRET not in subsegment.serialize()


def test_failed_keeps_error_labels():
    subsegment = _run_failed(XrayCommandListener(record_full_documents=False), TRANSACTION_FAILURE)

    assert subsegment.metadata['default']['failure'] == {
        'ok': 0.0,
        'code': 112,
        'codeName': 'WriteConflict',
        'errorLabels': ['TransientTransactionError'],
    }


def test_failed_write_concern_error():
    subsegment = _run_failed(XrayCommandListener(record_full_documents=False), WRITE_CONCERN_FAILURE)

    assert subsegment.metadata['default']['failure'] == {
        'code': 64,
        'codeName': 'WriteConcernFailed',
        'errorLabels': ['RetryableWriteError'],
    }


def test_failed_raw_bson_document():
    failure = RawBSONDocument(encode(DUPLICATE_KEY_FAILURE))
    subsegment = _run_failed(XrayCommandListener(record_full_documents=False), failure)

    assert subsegment.metadata['default']['failure'] == {
        'ok': 0.0,
        'code': 11000,
        'codeName': 'DuplicateKey',
    }
    assert SECRET not in subsegment.serialize()


@pytest.mark.parametrize('failure', [None, ['code']])
def test_failed_without_failure_document(failure):
    subsegment = _run_failed(XrayCommandListener(record_full_documents=False), failure)

    assert subsegment.metadata['default']['failure'] == {}
    assert not subsegment.in_progress


def test_failed_client_error_records_error_type():
    subsegment = _run_failed(XrayCommandListener(record_full_documents=False), CLIENT_FAILURE)

    assert subsegment.metadata['default']['failure'] == {'errtype': 'AutoReconnect'}


def test_failed_records_full_document_when_enabled():
    subsegment = _run_failed(XrayCommandListener(record_full_documents=True), VALIDATION_FAILURE)

    assert subsegment.metadata['default']['failure'] == VALIDATION_FAILURE


@pytest.mark.parametrize('record_full_documents', [False, True])
def test_succeeded(record_full_documents):
    listener = XrayCommandListener(record_full_documents=record_full_documents)
    listener.started(_started_event())
    listener.succeeded(SimpleNamespace(duration_micros=10, reply={'ok': 1.0, 'value': {'token': SECRET}}))
    subsegment = xray_recorder.current_segment().subsegments[0]

    assert subsegment.annotations['mongodb_command_name'] == 'findAndModify'
    metadata = subsegment.metadata.get('default', {})
    assert ('mongodb_command' in metadata) is record_full_documents
    assert ('mongodb_reply' in metadata) is record_full_documents


def test_patch_does_not_record_full_documents_by_default(monkeypatch):
    registered = []
    monkeypatch.setattr(monitoring, 'register', registered.append)
    monkeypatch.delattr(monitoring, '_xray_enabled', raising=False)
    try:
        patch()
    finally:
        vars(monitoring).pop('_xray_enabled', None)

    assert [listener.record_full_documents for listener in registered] == [False]


@pytest.mark.parametrize('new_error', [
    lambda: OperationFailure('Document failed validation', 121, VALIDATION_FAILURE),
    lambda: DuplicateKeyError(DUPLICATE_KEY_FAILURE['errmsg'], 11000, DUPLICATE_KEY_FAILURE),
    # insert and update commands report validation failures as write errors
    lambda: WriteError('Document failed validation', 121,
                       {'index': 0, 'code': 121, 'errInfo': VALIDATION_FAILURE['errInfo']}),
    lambda: BulkWriteError({'writeErrors': [{'index': 0, 'code': 121, 'errInfo': VALIDATION_FAILURE['errInfo'],
                                             'op': {'token': SECRET}}]}),
], ids=['OperationFailure', 'DuplicateKeyError', 'WriteError', 'BulkWriteError'])
def test_exception_message_does_not_record_document_values(new_error):
    error = new_error()
    with pytest.raises(type(error)):
        with xray_recorder.in_subsegment('app'):
            raise error
    subsegment = xray_recorder.current_segment().subsegments[0]

    message = subsegment.cause['exceptions'][0].message
    assert ", full error: {" in message and "'REDACTED'" in message
    assert SECRET not in subsegment.serialize()


def test_exception_message_records_document_values_with_full_documents():
    XrayCommandListener(record_full_documents=True)
    with pytest.raises(OperationFailure):
        with xray_recorder.in_subsegment('app'):
            raise OperationFailure('Document failed validation', 121, VALIDATION_FAILURE)
    subsegment = xray_recorder.current_segment().subsegments[0]

    assert SECRET in subsegment.cause['exceptions'][0].message
