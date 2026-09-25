from aws_xray_sdk.ext.util import to_snake_case, get_hostname, strip_url, inject_trace_header
from aws_xray_sdk.core.models.segment import Segment
from aws_xray_sdk.core.models.subsegment import Subsegment
from aws_xray_sdk.core.models.dummy_entities import DummySegment, DummySubsegment
from .util import get_new_stubbed_recorder

xray_recorder = get_new_stubbed_recorder()

UNKNOWN_HOST = "UNKNOWN HOST"


def test_to_snake_case():
    s1 = to_snake_case('Bucket')
    assert s1 == 'bucket'

    s2 = to_snake_case('TableName')
    assert s2 == 'table_name'

    s3 = to_snake_case('ACLName')
    assert s3 == 'acl_name'

    s4 = to_snake_case('getHTTPResponse')
    assert s4 == 'get_http_response'


def test_get_hostname():
    s1 = get_hostname("https://amazon.com/")
    assert s1 == "amazon.com"

    s2 = get_hostname("https://amazon.com/avery_long/path/and/stuff")
    assert s2 == "amazon.com"

    s3 = get_hostname("http://aws.amazon.com/should_get/sub/domains")
    assert s3 == "aws.amazon.com"

    s4 = get_hostname("https://amazon.com/somestuff?get=request&data=chiem")
    assert s4 == "amazon.com"

    s5 = get_hostname("INVALID_URL")
    assert s5 == UNKNOWN_HOST

    s6 = get_hostname("")
    assert s6 == UNKNOWN_HOST

    s7 = get_hostname(None)
    assert s7 == UNKNOWN_HOST


def test_strip_url():
    s1 = strip_url("https://amazon.com/page?getdata=response&stuff=morestuff")
    assert s1 == "https://amazon.com/page"

    s2 = strip_url("aws.google.com/index.html?field=data&suchcool=data")
    assert s2 == "aws.google.com/index.html"

    s3 = strip_url("INVALID_URL")
    assert s3 == "INVALID_URL"

    assert strip_url("") == ""
    assert not strip_url(None)


def test_inject_trace_header_unsampled():
    headers = {'host': 'test', 'accept': '*/*', 'connection': 'keep-alive', 'X-Amzn-Trace-Id': 'Root=1-6369739a-7d8bb07e519b795eb24d382d;Parent=089e3de743fb9e79;Sampled=1'}
    xray_recorder = get_new_stubbed_recorder()
    xray_recorder.configure(sampling=True)
    segment = xray_recorder.begin_segment('name', sampling=True)
    subsegment = xray_recorder.begin_subsegment_without_sampling('unsampled')

    inject_trace_header(headers, subsegment)

    assert 'Sampled=0' in headers['X-Amzn-Trace-Id']

def test_inject_trace_header_respects_parent_subsegment():
    headers = {'host': 'test', 'accept': '*/*', 'connection': 'keep-alive', 'X-Amzn-Trace-Id': 'Root=1-6369739a-7d8bb07e519b795eb24d382d;Parent=089e3de743fb9e79;Sampled=1'}

    xray_recorder = get_new_stubbed_recorder()
    xray_recorder.configure(sampling=True)
    segment = xray_recorder.begin_segment('name', sampling=True)
    subsegment = xray_recorder.begin_subsegment_without_sampling('unsampled')
    subsegment2 = xray_recorder.begin_subsegment('unsampled2')
    inject_trace_header(headers, subsegment2)

    assert 'Sampled=0' in headers['X-Amzn-Trace-Id']

def test_inject_trace_header_sampled():
    headers = {'host': 'test', 'accept': '*/*', 'connection': 'keep-alive', 'X-Amzn-Trace-Id': 'Root=1-6369739a-7d8bb07e519b795eb24d382d;Parent=089e3de743fb9e79;Sampled=1'}
    xray_recorder = get_new_stubbed_recorder()
    xray_recorder.configure(sampling=True)
    segment = xray_recorder.begin_segment('name')
    subsegment = xray_recorder.begin_subsegment('unsampled')

    inject_trace_header(headers, subsegment)

    assert 'Sampled=1' in headers['X-Amzn-Trace-Id']

def test_metadata_to_dict_non_iterable_object():
    from aws_xray_sdk.core.utils.conversion import metadata_to_dict

    class MockMySQLConnection:
        __iter__ = None

        def __init__(self):
            self.host = "localhost"
            self.port = 3306
            self._secret = "hidden"

    conn = MockMySQLConnection()
    result = metadata_to_dict(conn)
    assert result == {"host": "localhost", "port": 3306}


def test_metadata_to_dict_broken_iterable():
    from aws_xray_sdk.core.utils.conversion import metadata_to_dict

    class BrokenIterable:
        def __iter__(self):
            raise TypeError("iteration failed")

        def __init__(self):
            self.status = "active"
            self._private = 123

    obj = BrokenIterable()
    result = metadata_to_dict(obj)
    assert result == {"status": "active"}


def test_metadata_to_dict_collection_types():
    from aws_xray_sdk.core.utils.conversion import metadata_to_dict

    assert metadata_to_dict({"k": "v"}) == {"k": "v"}
    assert metadata_to_dict([1, "a", True]) == [1, "a", True]
    assert metadata_to_dict((1, 2)) == [1, 2]
    assert metadata_to_dict("text") == "text"
    assert metadata_to_dict(42) == 42
    assert metadata_to_dict(None) is None
