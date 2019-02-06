.. _configurations:

Configure Global Recorder
=========================

Sampling
--------
Sampling is enabled by default.
Whenever the global recorder creates a segment,
it decides whether to sample this segment.
If it does not sample this segment, it is discarded and not sent to the
X-Ray daemon.

To turn off sampling, use code like the following::

    from aws_xray_sdk.core import xray_recorder
    xray_recorder.configure(sampling=False)

You can also configure the sampling rules::

    xray_recorder.configure(sampling_rules=your_rules)

The input can either be an absolute path to your sampling rule
*.json* file or a dictionary.

The following code is an example of a rule configuration::

    {
    "version": 1,
    "rules": [
        {
        "description": "Player moves.",
        "service_name": "*",
        "http_method": "*",
        "url_path": "/api/move/*",
        "fixed_target": 0,
        "rate": 0.05
        }
    ],
    "default": {
        "fixed_target": 1,
        "rate": 0.1
        }
    }

This example defines one custom rule and a default rule.
The custom rule applies a five-percent sampling rate
with no minimum number of requests to trace for paths under */api/move/*.
The default rule traces the first request each second and 10 percent of
additional requests.
The SDK applies custom rules in the order in which they are defined.
If a request matches multiple custom rules, the SDK applies only the first rule.
You can use wildcard character "*" and "?" in service_name, http_method and
url_path.
"*" represents any combination of characters. "?" represents a single character.

Note that sampling configurations have no effect if the application runs in AWS Lambda.

Plugins
-------
The plugin adds extra metadata for each segment if the app is running on that environment.
The SDK provides three plugins:

* Amazon EC2 – EC2Plugin adds the instance ID and Availability Zone.
* Elastic Beanstalk – ElasticBeanstalkPlugin adds the environment name, version label, and deployment ID.
* Amazon ECS – ECSPlugin adds the container host name

To use plugins, use code like the following::

    # a tuple of strings
    plugins = ('elasticbeanstalk_plugin', 'ec2_plugin', 'ecs_plugin')
    # alternatively you can use 
    plugins = ('ElasticBeanstalkPlugin', 'EC2Plugin', 'ECSPlugin')

    xray_recorder.configure(plugins=plugins)

Order matters in the tuple and the origin of the segment is set from the last plugin.
Therefore, in the previous example, if the program runs on ECS, the segment origin is
'AWS::ECS::CONTAINER'.
Plugins must be configured before patching any third party libraries to
avoid unexpected behavior.
Plugins are employed after they are specified.

Context Missing Strategy
------------------------
Defines the recorder behavior when your instrumented code attempts to record data when no segment is open.
Configure like the following::

    xray_recorder.configure(context_missing='Your Strategy Name Here')

Supported strategies are:

* RUNTIME_ERROR: throw an SegmentNotFoundException
* LOG_ERROR: log an error and continue
* IGNORE: do nothing

Segment Dynamic Naming
----------------------
For a web application you might want to name the segment using host names. You can pass in a pattern
with wildcard character "*" and "?". "*" represents any combination of characters.
"?" represents a single character. If the host name from incoming request's header matches the pattern,
the host name will be used as the segment name, otherwise it uses fallback name defined in ``AWS_XRAY_TRACING_NAME``.
To configure dynamic naming, use code like the following::
    
    xray_recorder.configure(dynamic_naming='*.example.com')

Environment Variables
---------------------
There are three supported environment variables to configure the global
recorder:

* AWS_XRAY_CONTEXT_MISSING: configure context missing strategy
* AWS_XRAY_TRACING_NAME: default segment name
* AWS_XRAY_DAEMON_ADDRESS: where the recorder sends data to over UDP

Environment variables has higher precedence over ``xray_recorder.configure()``

Logging
-------
The SDK uses Python's built-in ``logging`` module to perform logging.
You can configure the SDK logging just like how you configure other
python libraries. An example of set the SDK log level is like the following::

    logging.basicConfig(level='DEBUG')
    logging.getLogger('aws_xray_sdk').setLevel(logging.WARNING)

Context Storage
---------------
The global recorder uses threadlocal to store active segments/subsegments.
You can override the default context class to implement your own context storage::
    
    from aws_xray_sdk.core.context import Context

    class MyOwnContext(Context):

        def put_segment(self, segment):
        # store the segment created by ``xray_recorder`` to the context.
        pass

        def end_segment(self, end_time=None):
        # end the segment in the current context.
        pass

        def put_subsegment(self, subsegment):
        # store the subsegment created by ``xray_recorder`` to the context.
        pass

        def end_subsegment(self, end_time=None):
        # end the subsegment in the current context.
        pass

        def get_trace_entity(self):
        # get the current active trace entity(segment or subsegment).
        pass

        def set_trace_entity(self, trace_entity):
        # manually inject a trace entity to the context storage.
        pass

        def clear_trace_entities(self):
        # clean up context storage.
        pass

        def handle_context_missing(self):
        # behavior on no trace entity to access or mutate.
        pass

The function ``current_segment`` and ``current_subsegment`` on recorder level uses
``context.get_trace_entity()`` and dynamically return the expected type by using internal
references inside segment/subsegment objects.

Then you can pass your own context::

    my_context=MyOwnContext()
    xray_recorder.configure(context=my_context)

Emitter
-------
The default emitter uses non-blocking socket to send data to the X-Ray daemon.
It doesn't retry on IOError. To override the default emitter::

    from aws_xray_sdk.core.emitters.udp_emitter import UDPEmitter

    class MyOwnEmitter(UDPEmitter):

        def send_entity(self, entity):
        # send the input segment/subsegment to the X-Ray daemon.
        # Return True on success and False on failure.
        pass

        def set_daemon_address(self, address):
        # parse input full address like 127.0.0.1:8000 to ip and port and
        # store them to the local emitter properties.
        pass

Then you can pass your own emitter::

    my_emitter = MyOwnEmitter()
    xray_recorder.configure(emitter=my_emitter)
