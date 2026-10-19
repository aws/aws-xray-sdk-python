import re

# the placeholder of masked data
REDACTED = 'REDACTED'

# url query parameters with sensitive values, e.g. of presigned urls
_SENSITIVE_QUERY_PARAMETERS = (
    'AWSAccessKeyId', 'Signature', 'sig', 'X-Amz-Credential', 'X-Amz-Security-Token', 'X-Amz-Signature',
    'X-Goog-Signature', 'token',
)

# patterns of sensitive data that is masked in exception messages, each a text that messages matching the pattern
# contain, to skip other messages quickly, a regular expression and its replacement. Messages can include data sent
# by clients, so patterns must not backtrack.
_PATTERNS = (
    # values of sensitive url query parameters, keeping the keys, e.g. 'X-Amz-Signature=REDACTED'
    ('=', re.compile(r'([?&](?:%s)=)[^&\s#]*' % '|'.join(map(re.escape, _SENSITIVE_QUERY_PARAMETERS)), re.IGNORECASE),
     r'\g<1>' + REDACTED),
)


def mask(text):
    """Return the text with the data that matches the patterns masked."""
    for hint, pattern, replacement in _PATTERNS:
        if hint in text:
            text = pattern.sub(replacement, text)
    return text
