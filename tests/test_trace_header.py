from aws_xray_sdk.core.models.trace_header import TraceHeader


TRACE_ID = '1-5759e988-bd862e3fe1be46a994272793'
PARENT_ID = '53995c3f42cd8ad8'


def test_no_sample():
    header = TraceHeader(root=TRACE_ID, parent=PARENT_ID)
    assert header.sampled is None
    assert header.root == TRACE_ID
    assert header.parent == PARENT_ID
    assert header.to_header_str() == 'Root=%s;Parent=%s' % (TRACE_ID, PARENT_ID)


def test_no_parent():
    header = TraceHeader(root=TRACE_ID, sampled=1)
    assert header.parent is None
    assert header.to_header_str() == 'Root=%s;Sampled=1' % TRACE_ID


def test_from_str():
    # a full header string that has all fields present
    header_str1 = 'Root=%s;Parent=%s;Sampled=1' % (TRACE_ID, PARENT_ID)
    header1 = TraceHeader.from_header_str(header_str1)
    assert header1.root == TRACE_ID
    assert header1.parent == PARENT_ID
    assert header1.sampled == 1

    # missing parent id
    header_str2 = 'Root=%s;Sampled=?' % TRACE_ID
    header2 = TraceHeader.from_header_str(header_str2)
    assert header2.root == TRACE_ID
    assert header2.parent is None
    assert header2.sampled == '?'

    # missing sampled
    header_str3 = 'Root=%s;Parent=%s' % (TRACE_ID, PARENT_ID)
    header3 = TraceHeader.from_header_str(header_str3)
    assert header3.root == TRACE_ID
    assert header3.parent == PARENT_ID
    assert header3.sampled is None


def test_arbitrary_fields():
    origin_header_str = 'Root=%s;k1=v1;k2=v2' % TRACE_ID
    header = TraceHeader.from_header_str(origin_header_str)
    header_str = header.to_header_str()

    assert 'k1=v1' in header_str
    assert 'k2=v2' in header_str


def test_invalid_str():
    header = TraceHeader.from_header_str('some invalid string')
    assert header.root is None
    assert header.parent is None
    assert header.sampled is None
