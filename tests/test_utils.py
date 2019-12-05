from aws_xray_sdk.ext.util import to_snake_case, get_hostname, strip_url


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


def test_strip_url():
    s1 = strip_url("https://amazon.com/page?getdata=response&stuff=morestuff")
    assert s1 == "https://amazon.com/page"

    s2 = strip_url("aws.google.com/index.html?field=data&suchcool=data")
    assert s2 == "aws.google.com/index.html"

    s3 = strip_url("INVALID_URL")
    assert s3 == "INVALID_URL"

    assert strip_url("") == ""
    assert not strip_url(None)
