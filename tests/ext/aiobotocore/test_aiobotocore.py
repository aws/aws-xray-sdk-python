import pytest

from aiobotocore.session import get_session
from botocore.stub import Stubber, ANY
from botocore.exceptions import ClientError

from aws_xray_sdk.core import patch
from aws_xray_sdk.core.async_context import AsyncContext
from aws_xray_sdk.core import xray_recorder

patch(('aiobotocore',))


@pytest.fixture(scope='function')
def recorder(loop):
    """
    Clean up before and after each test run
    """
    xray_recorder.configure(service='test', sampling=False, context=AsyncContext(loop=loop))
    xray_recorder.clear_trace_entities()
    yield xray_recorder
    xray_recorder.clear_trace_entities()


async def test_describe_table(loop, recorder):
    segment = recorder.begin_segment('name')

    req_id = '1234'
    response = {'ResponseMetadata': {'RequestId': req_id, 'HTTPStatusCode': 403}}

    session = get_session()
    async with session.create_client('dynamodb', region_name='eu-west-2') as client:
        with Stubber(client) as stubber:
            stubber.add_response('describe_table', response, {'TableName': 'mytable'})
            await client.describe_table(TableName='mytable')

    subsegment = segment.subsegments[0]
    assert subsegment.error
    assert subsegment.http['response']['status'] == 403

    aws_meta = subsegment.aws
    assert aws_meta['table_name'] == 'mytable'
    assert aws_meta['request_id'] == req_id
    assert aws_meta['region'] == 'eu-west-2'
    assert aws_meta['operation'] == 'DescribeTable'


async def test_s3_parameter_capture(loop, recorder):
    segment = recorder.begin_segment('name')

    bucket_name = 'mybucket'
    key = 'mykey'
    version_id = 'myversionid'
    response = {'ResponseMetadata': {'RequestId': '1234', 'HTTPStatusCode': 200}}

    session = get_session()
    async with session.create_client('s3', region_name='eu-west-2') as client:
        with Stubber(client) as stubber:
            stubber.add_response('get_object', response,
                                 {'Bucket': bucket_name, 'Key': key, 'VersionId': version_id})
            await client.get_object(Bucket=bucket_name, Key=key,
                                    VersionId=version_id)

    subsegment = segment.subsegments[0]
    aws_meta = subsegment.aws

    assert aws_meta['bucket_name'] == bucket_name
    assert aws_meta['key'] == key
    assert aws_meta['version_id'] == version_id
    assert aws_meta['operation'] == 'GetObject'


async def test_list_parameter_counting(loop, recorder):
    """
    Test special parameters that have shape of list are recorded
    as count based on `para_whitelist.json`
    """
    segment = recorder.begin_segment('name')

    queue_urls = ['url1', 'url2']
    queue_name_prefix = 'url'
    response = {
        'QueueUrls': queue_urls,
        'ResponseMetadata': {
            'RequestId': '1234',
            'HTTPStatusCode': 200,
        }
    }

    session = get_session()
    async with session.create_client('sqs', region_name='eu-west-2') as client:
        with Stubber(client) as stubber:
            stubber.add_response('list_queues', response, {'QueueNamePrefix': queue_name_prefix})
            await client.list_queues(QueueNamePrefix='url')

    subsegment = segment.subsegments[0]
    assert subsegment.http['response']['status'] == 200

    aws_meta = subsegment.aws
    assert aws_meta['queue_count'] == len(queue_urls)
    # all whitelisted input parameters will be converted to snake case
    # unless there is an explicit 'rename_to' attribute in json key
    assert aws_meta['queue_name_prefix'] == queue_name_prefix


async def test_map_parameter_grouping(loop, recorder):
    """
    Test special parameters that have shape of map are recorded
    as a list of keys based on `para_whitelist.json`
    """
    segment = recorder.begin_segment('name')

    response = {
        'ResponseMetadata': {
            'RequestId': '1234',
            'HTTPStatusCode': 500,
        }
    }

    session = get_session()
    async with session.create_client('dynamodb', region_name='eu-west-2') as client:
        with Stubber(client) as stubber:
            stubber.add_response('batch_write_item', response, {'RequestItems': ANY})
            await client.batch_write_item(RequestItems={'table1': [{}], 'table2': [{}]})

    subsegment = segment.subsegments[0]
    assert subsegment.fault
    assert subsegment.http['response']['status'] == 500

    aws_meta = subsegment.aws
    assert sorted(aws_meta['table_names']) == ['table1', 'table2']


async def test_context_missing_not_swallow_return(loop, recorder):
    xray_recorder.configure(service='test', sampling=False,
                            context=AsyncContext(loop=loop), context_missing='LOG_ERROR')

    response = {'ResponseMetadata': {'RequestId': '1234', 'HTTPStatusCode': 403}}

    session = get_session()
    async with session.create_client('dynamodb', region_name='eu-west-2') as client:
        with Stubber(client) as stubber:
            stubber.add_response('describe_table', response, {'TableName': 'mytable'})
            actual_resp = await client.describe_table(TableName='mytable')

    assert actual_resp == response


async def test_context_missing_not_suppress_exception(loop, recorder):
    xray_recorder.configure(service='test', sampling=False,
                            context=AsyncContext(loop=loop), context_missing='LOG_ERROR')

    session = get_session()
    async with session.create_client('dynamodb', region_name='eu-west-2') as client:
        with Stubber(client) as stubber:
            stubber.add_client_error('describe_table', expected_params={'TableName': ANY})
            with pytest.raises(ClientError):
                await client.describe_table(TableName='mytable')
