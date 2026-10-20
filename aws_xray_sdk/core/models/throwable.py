import copy
import os
import binascii
import logging
from collections.abc import Mapping

from ..utils.redaction import REDACTED, mask

log = logging.getLogger(__name__)


# fields of pymongo error documents that never contain document values, as in the failure metadata
_SAFE_FAILURE_FIELDS = ('ok', 'code', 'codeName', 'errorLabels', 'errtype')

# and the position of a write error in a bulk write
_SAFE_WRITE_ERROR_FIELDS = _SAFE_FAILURE_FIELDS + ('index', 'idx')

# errors in an error document, and their fields that never contain document values
_ERRORS = {
    'writeErrors': _SAFE_WRITE_ERROR_FIELDS,
    'writeConcernErrors': _SAFE_FAILURE_FIELDS,
    'writeConcernError': _SAFE_FAILURE_FIELDS,
}


def _redact_error_document(document, safe_fields=_SAFE_FAILURE_FIELDS):
    redacted = {}
    for key, value in document.items():
        if key in safe_fields:
            redacted[key] = value
        elif key in _ERRORS:
            redacted[key] = _redact_errors(value, _ERRORS[key])
        else:
            redacted[key] = REDACTED
    return redacted


def _redact_errors(value, safe_fields):
    if isinstance(value, Mapping):
        return _redact_error_document(value, safe_fields)
    if isinstance(value, (list, tuple)):
        return [_redact_error_document(error, safe_fields) if isinstance(error, Mapping) else REDACTED
                for error in value]
    return REDACTED


def _redact_dup_key(message):
    # duplicate key error messages end with the key values, e.g. 'dup key: { email: "..." }'
    i = message.find('dup key: ')
    return message if i < 0 else message[:i] + 'dup key: ' + REDACTED


def _redact_pymongo_error_document(exception, message):
    if not any(str(getattr(cls, '__module__', '')).startswith('pymongo.') for cls in type(exception).__mro__):
        return message
    # pymongo errors include the server error document, and errors such as EncryptionError the document of the
    # error that caused them
    head, separator, _ = message.partition(', full error: ')
    details = getattr(exception, 'details', None)
    for name in ('__cause__', 'cause', '__context__'):
        if isinstance(details, Mapping):
            break
        details = getattr(getattr(exception, name, None), 'details', None)
    if not separator or not isinstance(details, Mapping):
        return _redact_dup_key(message)
    # the server message is kept, except duplicate key values
    return _redact_dup_key(head) + separator + str(_redact_error_document(details))


def _mask_message(exception, message):
    return mask(message)


# rules that redact sensitive data in exception messages, each a function of the exception and its message
_REDACTION_RULES = (_redact_pymongo_error_document, _mask_message)


def _record_full_pymongo_documents():
    # pymongo exception messages are recorded in full, in the whole process, once a pymongo listener records
    # full documents, see aws_xray_sdk.ext.pymongo.patch.XrayCommandListener
    global _REDACTION_RULES
    _REDACTION_RULES = tuple(rule for rule in _REDACTION_RULES if rule is not _redact_pymongo_error_document)


def _redact(exception, message):
    for rule in _REDACTION_RULES:
        message = rule(exception, message)
    return message


class Throwable:
    """
    An object recording exception infomation under trace entity
    `cause` section. The information includes the stack trace,
    working directory and message from the original exception.
    """
    def __init__(self, exception, stack, remote=False):
        """
        :param Exception exception: the catched exception.
        :param list stack: the formatted stack trace gathered
            through `traceback` module.
        :param bool remote: If False it means it's a client error
            instead of a downstream service.
        """
        self.id = binascii.b2a_hex(os.urandom(8)).decode('utf-8')

        try:
            message = _redact(exception, str(exception))
            # in case there is an exception cannot be converted to str or redacted
        except Exception:
            message = None

        # do not record non-string exception message
        if isinstance(message, str):
            self.message = message

        self.type = type(exception).__name__
        self.remote = remote

        try:
            self._normalize_stack_trace(stack)
        except Exception:
            self.stack = None
            log.warning("can not parse stack trace string, ignore stack field.")

        if exception:
            setattr(exception, '_recorded', True)
            setattr(exception, '_cause_id', self.id)
			
    def to_dict(self):  
        """
        Convert Throwable object to dict with required properties that
        have non-empty values. 
        """  
        throwable_dict = {}
        
        for key, value in vars(self).items():  
            if isinstance(value, bool) or value:
                throwable_dict[key] = value       
        
        return throwable_dict

    def _normalize_stack_trace(self, stack):
        if stack is None:
            return None

        self.stack = []

        for entry in stack:
            path = entry[0]
            line = entry[1]
            label = entry[2]
            if 'aws_xray_sdk/' in path:
                continue

            normalized = {}
            normalized['path'] = os.path.basename(path).replace('\"', ' ').strip()
            normalized['line'] = line
            normalized['label'] = label.strip()

            self.stack.append(normalized)
