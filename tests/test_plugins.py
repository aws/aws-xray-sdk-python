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
    mock_do_request.side_effect = ['token', 'i-0a1d026d92d4709cd', 'us-west-2b']

    ec2_plugin = get_plugin_modules(('ec2_plugin',))[0]
    ec2_plugin.initialize()
    assert hasattr(ec2_plugin, 'runtime_context')
    r_c = getattr(ec2_plugin, 'runtime_context')
    assert r_c['instance_id'] == 'i-0a1d026d92d4709cd'
    assert r_c['availability_zone'] == 'us-west-2b'


@patch('aws_xray_sdk.core.plugins.ec2_plugin.do_request')
def test_ec2_plugin_v2_fail_v1_success(mock_do_request):
    mock_do_request.side_effect = [Exception("Boom!"), 'i-0a1d026d92d4709ab', 'us-west-2a']

    ec2_plugin = get_plugin_modules(('ec2_plugin',))[0]
    ec2_plugin.initialize()
    assert hasattr(ec2_plugin, 'runtime_context')
    r_c = getattr(ec2_plugin, 'runtime_context')
    assert r_c['instance_id'] == 'i-0a1d026d92d4709ab'
    assert r_c['availability_zone'] == 'us-west-2a'


@patch('aws_xray_sdk.core.plugins.ec2_plugin.do_request')
def test_ec2_plugin_v2_fail_v1_fail(mock_do_request):
    mock_do_request.side_effect = [Exception("Boom v2!"), Exception("Boom v1!")]

    ec2_plugin = get_plugin_modules(('ec2_plugin',))[0]
    ec2_plugin.initialize()
    assert hasattr(ec2_plugin, 'runtime_context')
    r_c = getattr(ec2_plugin, 'runtime_context')
    assert r_c is None
