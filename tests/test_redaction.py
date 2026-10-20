import time

import pytest

from aws_xray_sdk.core.utils.redaction import mask

SECRET = 'stored-secret-value'


@pytest.mark.parametrize('text, masked', [
    # a presigned url in a requests error
    ("HTTPSConnectionPool(host='bucket.s3.amazonaws.com', port=443): Max retries exceeded with url: "
     "/private/object.txt?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAIOSFODNN7EXAMPLE%2F20261020"
     "&X-Amz-Security-Token={0}&X-Amz-Signature={0} (Caused by ConnectTimeoutError())".format(SECRET),
     "HTTPSConnectionPool(host='bucket.s3.amazonaws.com', port=443): Max retries exceeded with url: "
     "/private/object.txt?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=REDACTED"
     "&X-Amz-Security-Token=REDACTED&X-Amz-Signature=REDACTED (Caused by ConnectTimeoutError())"),
    # Signature Version 2
    ('/key?AWSAccessKeyId=AKIAIOSFODNN7EXAMPLE&Expires=1&Signature=%s&x-amz-security-token=%s' % (SECRET, SECRET),
     '/key?AWSAccessKeyId=REDACTED&Expires=1&Signature=REDACTED&x-amz-security-token=REDACTED'),
    ("Client error '404 Not Found' for url 'https://host/key?page=2&token=%s#top'" % SECRET,
     "Client error '404 Not Found' for url 'https://host/key?page=2&token=REDACTED#top'"),
    # values end at a space, '&' or '#', so the quote after a url is masked too
    ("404, message='Not Found', url='https://host/key?token=public'%s'" % SECRET,
     "404, message='Not Found', url='https://host/key?token=REDACTED"),
    # other parameters and text are recorded as is
    ('https://host/key?access_token=a&page=2', 'https://host/key?access_token=a&page=2'),
    ('Did you mean this? yes', 'Did you mean this? yes'),
])
def test_sensitive_query_values(text, masked):
    assert mask(text) == masked


@pytest.mark.parametrize('text', [
    '?token=' * 20000,
    '&X-Amz-Signature' * 10000 + '=',
    '?' + 'a' * 80000 + '=',
], ids=['values', 'keys', 'long key'])
def test_masking_time_is_linear(text):
    # messages can include data sent by clients
    start = time.perf_counter()
    mask(text)

    assert time.perf_counter() - start < 0.5
