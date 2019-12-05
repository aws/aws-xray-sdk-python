from aws_xray_sdk.ext.util import to_snake_case, get_hostname


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
    assert s5 == "INVALID_URL"

    s6 = get_hostname("")
    assert s6 == ""

    s7 = get_hostname(None)
    assert not s7
