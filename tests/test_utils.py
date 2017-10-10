from aws_xray_sdk.ext.util import to_snake_case


def test_to_snake_case():
    s1 = to_snake_case('Bucket')
    assert s1 == 'bucket'

    s2 = to_snake_case('TableName')
    assert s2 == 'table_name'

    s3 = to_snake_case('ACLName')
    assert s3 == 'acl_name'

    s4 = to_snake_case('getHTTPResponse')
    assert s4 == 'get_http_response'
