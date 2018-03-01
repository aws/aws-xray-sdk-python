import pytest
import botocore.session
from botocore.stub import Stubber, ANY

from aws_xray_sdk.core import patch
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core.context import Context

patch(('botocore',))
session = botocore.session.get_session()

REQUEST_ID = '1234'


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


def test_ddb_table_name():
    ddb = session.create_client('dynamodb', region_name='us-west-2')
    response = {
        'ResponseMetadata': {
            'RequestId': REQUEST_ID,
            'HTTPStatusCode': 403,
        }
    }

    with Stubber(ddb) as stubber:
        stubber.add_response('describe_table', response, {'TableName': 'mytable'})
        ddb.describe_table(TableName='mytable')

    subsegment = xray_recorder.current_segment().subsegments[0]
    assert subsegment.error
    assert subsegment.http['response']['status'] == 403

    aws_meta = subsegment.aws
    assert aws_meta['table_name'] == 'mytable'
    assert aws_meta['request_id'] == REQUEST_ID
    assert aws_meta['region'] == 'us-west-2'
    assert aws_meta['operation'] == 'DescribeTable'


def test_list_parameter_counting():
    """
    Test special parameters that have shape of list are recorded
    as count based on `para_whitelist.json`
    """
    sqs = session.create_client('sqs', region_name='us-west-2')
    queue_urls = ['url1', 'url2']
    queue_name_prefix = 'url'
    response = {
        'QueueUrls': queue_urls,
        'ResponseMetadata': {
            'RequestId': '1234',
            'HTTPStatusCode': 200,
        }
    }

    with Stubber(sqs) as stubber:
        stubber.add_response('list_queues', response, {'QueueNamePrefix': queue_name_prefix})
        sqs.list_queues(QueueNamePrefix='url')

    subsegment = xray_recorder.current_segment().subsegments[0]
    assert subsegment.http['response']['status'] == 200

    aws_meta = subsegment.aws
    assert aws_meta['queue_count'] == len(queue_urls)
    # all whitelisted input parameters will be converted to snake case
    # unless there is an explicit 'rename_to' attribute in json key
    assert aws_meta['queue_name_prefix'] == queue_name_prefix


def test_map_parameter_grouping():
    """
    Test special parameters that have shape of map are recorded
    as a list of keys based on `para_whitelist.json`
    """
    ddb = session.create_client('dynamodb', region_name='us-west-2')
    response = {
        'ResponseMetadata': {
            'RequestId': REQUEST_ID,
            'HTTPStatusCode': 500,
        }
    }

    with Stubber(ddb) as stubber:
        stubber.add_response('batch_write_item', response, {'RequestItems': ANY})
        ddb.batch_write_item(RequestItems={'table1': [{}], 'table2': [{}]})

    subsegment = xray_recorder.current_segment().subsegments[0]
    assert subsegment.fault
    assert subsegment.http['response']['status'] == 500

    aws_meta = subsegment.aws
    assert sorted(aws_meta['table_names']) == ['table1', 'table2']

def test_pass_through_on_context_missing():
    """
    The built-in patcher or subsegment capture logic should not throw
    any error when a `None` subsegment created from `LOG_ERROR` missing context.
    """
    xray_recorder.configure(context_missing='LOG_ERROR')
    xray_recorder.clear_trace_entities()

    ddb = session.create_client('dynamodb', region_name='us-west-2')
    response = {
        'ResponseMetadata': {
            'RequestId': REQUEST_ID,
            'HTTPStatusCode': 200,
        }
    }

    with Stubber(ddb) as stubber:
        stubber.add_response('describe_table', response, {'TableName': 'mytable'})
        ddb.describe_table(TableName='mytable')

    xray_recorder.configure(context_missing='RUNTIME_ERROR')
