.. _frameworks:

Django
======

Configure X-Ray Recorder
------------------------
Make sure you add ``XRayMiddleWare`` as the first entry in your
Django *settings.py* file, as shown in the following example::

    MIDDLEWARE = [
        'aws_xray_sdk.ext.django.middleware.XRayMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
    ] 

The incoming requests to the Django app are then automatically recorded as
a segment.

To get the current segment and add annotations or metadata as needed,
use the following statement in your application code when processing request::

    segment = xray_recorder.current_segement()

For more configurations in your Django ``settings.py`` file,
add the following line::

    INSTALLED_APPS = [
        'django.contrib.admin',
        ...
        'django.contrib.sessions',
        'aws_xray_sdk.ext.django',
    ]

You can configure the X-Ray recorder in a Django app under the
'XRAY_RECORDER' namespace.
The default values are as follows::

    XRAY_RECORDER = {
        'AWS_XRAY_DAEMON_ADDRESS': '127.0.0.1:2000',
        'AUTO_INSTRUMENT': True,  # If turned on built-in database queries and template rendering will be recorded as subsegments
        'AWS_XRAY_CONTEXT_MISSING': 'RUNTIME_ERROR',
        'PLUGINS': (),
        'SAMPLING': True,
        'SAMPLING_RULES': None,
        'AWS_XRAY_TRACING_NAME': None, # the segment name for segments generated from incoming requests
        'DYNAMIC_NAMING': None, # defines a pattern that host names should match
        'STREAMING_THRESHOLD': None, # defines when a segment starts to stream out its children subsegments
    }

Environment variables have higher precedence over user settings.
If neither is set, the defaults values shown previously are used.
'AWS_XRAY_TRACING_NAME' is required unless specified as an environment variable.
All other keys are optional.
For further information on individual settings, see the :ref:`Configure Global Recorder <configurations>` section.

Local Development
-----------------
When doing Django app local development, if you configured Django built-in database with ``AUTO_INSTRUMENT`` turned-on,
the command ``manage.py runserver`` may fail if ``AWS_XRAY_CONTEXT_MISSING`` is set to ``RUNTIME_ERROR``. This is because
the command ``runserver`` performs migrations check which will generate a subsegment,
the ``xray_recorder`` will raise an error since there is no active segment. 

One solution is to set ``AWS_XRAY_CONTEXT_MISSING`` to ``LOG_ERROR`` so it only emits a error message on server startup. 
Alternatively if you have defined your own ``ready()`` function for code execution at startup you can manually create a segment
as a placeholder.

By Django official guide it's recommanded to deploy Django to other servers in production so this particular issue normally
doesn't exist in production.

Flask
=====

To generate segment based on incoming requests, you need to instantiate the X-Ray middleware for flask::

    from aws_xray_sdk.core import xray_recorder
    from aws_xray_sdk.ext.flask.middleware import XRayMiddleware

    app = Flask(__name__)

    xray_recorder.configure(service='my_app_name')
    XRayMiddleware(app, xray_recorder)

Flask built-in template rendering will be wrapped into subsegments.
You can configure the recorder, see :ref:`Configure Global Recorder <configurations>` for more details.

aiohttp Server
==============

For X-Ray to create a segment based on an incoming request, you need register some middleware with aiohttp. As aiohttp
is an asyncronous framework, X-Ray will also need to be configured with an ``AsyncContext`` compared to the default threaded
version.::

    import asyncio

    from aiohttp import web

    from aws_xray_sdk.ext.aiohttp.middleware import middleware
    from aws_xray_sdk.core.async_context import AsyncContext
    from aws_xray_sdk.core import xray_recorder
    # Configure X-Ray to use AsyncContext
    xray_recorder.configure(service='service_name', context=AsyncContext())


    async def handler(request):
        return web.Response(body='Hello World')

    loop = asyncio.get_event_loop()
    # Use X-Ray SDK middleware, its crucial the X-Ray middleware comes first
    app = web.Application(middlewares=[middleware])
    app.router.add_get("/", handler)

    web.run_app(app)

There are two things to note from the example above. Firstly a middleware corountine from aws-xray-sdk is provided during the creation
of an aiohttp server app. Lastly the ``xray_recorder`` has also been configured with a name and an ``AsyncContext``. See
:ref:`Configure Global Recorder <configurations>` for more information about configuring the ``xray_recorder``.
