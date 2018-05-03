import pytest

import botocore.session
from botocore import UNSIGNED
from botocore.client import Config
from botocore.exceptions import ClientError
from pynamodb.attributes import UnicodeAttribute
from pynamodb.models import Model

from aws_xray_sdk.core import patch
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core.context import Context

patch(('pynamodb',))


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


def test_exception():
    class SampleModel(Model):
        class Meta:
            region = 'us-west-2'
            table_name = 'mytable'

        sample_attribute = UnicodeAttribute(hash_key=True)

    try:
        SampleModel.describe_table()
    except Exception:
        pass

    subsegments = xray_recorder.current_segment().subsegments
    assert len(subsegments) == 1
    subsegment = subsegments[0]
    assert subsegment.name == 'dynamodb'
    assert len(subsegment.subsegments) == 0
    assert subsegment.error

    aws_meta = subsegment.aws
    assert aws_meta['region'] == 'us-west-2'
    assert aws_meta['operation'] == 'DescribeTable'
    assert aws_meta['table_name'] == 'mytable'


def test_only_dynamodb_calls_are_traced():
    """Test only a single subsegment is created for other AWS services.

    As the pynamodb patch applies the botocore patch as well, we need
    to ensure that only one subsegment is created for all calls not
    made by PynamoDB. As PynamoDB calls botocore differently than the
    botocore patch expects we also just get a single subsegment per
    PynamoDB call.
    """
    session = botocore.session.get_session()
    s3 = session.create_client('s3', region_name='us-west-2',
                               config=Config(signature_version=UNSIGNED))
    try:
        s3.get_bucket_location(Bucket='mybucket')
    except ClientError:
        pass

    subsegments = xray_recorder.current_segment().subsegments
    assert len(subsegments) == 1
    assert subsegments[0].name == 's3'
    assert len(subsegments[0].subsegments) == 0
