from aws_xray_sdk.core.plugins.utils import get_plugin_modules
from mock import patch

supported_plugins = (
    'ec2_plugin',
    'ecs_plugin',
    'elasticbeanstalk_plugin',
)


def test_runtime_context_available():
    plugins = get_plugin_modules(supported_plugins)

    for plugin in plugins:
        plugin.initialize()
        assert hasattr(plugin, 'runtime_context')


@patch('aws_xray_sdk.core.plugins.ec2_plugin.do_request')
def test_ec2_plugin_imdsv2_success(mock_do_request):
    v2_json_str = "{\"availabilityZone\" : \"us-east-2a\", \"imageId\" : \"ami-03cca83dd001d4666\"," \
               " \"instanceId\" : \"i-07a181803de94c666\", \"instanceType\" : \"t3.xlarge\"}"

    mock_do_request.side_effect = ['token', v2_json_str]

    ec2_plugin = get_plugin_modules(('ec2_plugin',))[0]
    ec2_plugin.initialize()
    assert hasattr(ec2_plugin, 'runtime_context')
    r_c = getattr(ec2_plugin, 'runtime_context')
    assert r_c['instance_id'] == 'i-07a181803de94c666'
    assert r_c['availability_zone'] == 'us-east-2a'
    assert r_c['instance_type'] == 't3.xlarge_FAIL_THIS'
    assert r_c['ami_id'] == 'ami-03cca83dd001d4666'


@patch('aws_xray_sdk.core.plugins.ec2_plugin.do_request')
def test_ec2_plugin_v2_fail_v1_success(mock_do_request):
    v1_json_str = "{\"availabilityZone\" : \"cn-north-1a\", \"imageId\" : \"ami-03cca83dd001d4111\"," \
                  " \"instanceId\" : \"i-07a181803de94c111\", \"instanceType\" : \"t2.xlarge\"}"

    mock_do_request.side_effect = [Exception("Boom!"), v1_json_str]

    ec2_plugin = get_plugin_modules(('ec2_plugin',))[0]
    ec2_plugin.initialize()
    assert hasattr(ec2_plugin, 'runtime_context')
    r_c = getattr(ec2_plugin, 'runtime_context')
    assert r_c['instance_id'] == 'i-07a181803de94c111'
    assert r_c['availability_zone'] == 'cn-north-1a'
    assert r_c['instance_type'] == 't2.xlarge'
    assert r_c['ami_id'] == 'ami-03cca83dd001d4111'


@patch('aws_xray_sdk.core.plugins.ec2_plugin.do_request')
def test_ec2_plugin_v2_fail_v1_fail(mock_do_request):
    mock_do_request.side_effect = [Exception("Boom v2!"), Exception("Boom v1!")]

    ec2_plugin = get_plugin_modules(('ec2_plugin',))[0]
    ec2_plugin.initialize()
    assert hasattr(ec2_plugin, 'runtime_context')
    r_c = getattr(ec2_plugin, 'runtime_context')
    assert r_c == {}
