![Build Status](https://github.com/aws/aws-xray-sdk-python/actions/workflows/IntegrationTesting.yaml/badge.svg)
[![codecov](https://codecov.io/gh/aws/aws-xray-sdk-python/branch/master/graph/badge.svg)](https://codecov.io/gh/aws/aws-xray-sdk-python)

### :mega: OpenTelemetry Python with AWS X-Ray

AWS X-Ray supports using OpenTelemetry Python and the AWS Distro for OpenTelemetry (ADOT) Collector to instrument your application and send trace data to X-Ray. The OpenTelemetry SDKs are an industry-wide standard for tracing instrumentation. They provide more instrumentations and have a larger community for support, but may not have complete feature parity with the X-Ray SDKs. See [choosing between the ADOT and X-Ray SDKs](https://docs.aws.amazon.com/xray/latest/devguide/xray-instrumenting-your-app.html#xray-instrumenting-choosing) for more help with choosing between the two.

If you want additional features when tracing your Python applications, please [open an issue on the OpenTelemetry Python Instrumentation repository](https://github.com/open-telemetry/opentelemetry-python-contrib/issues/new?labels=feature-request&template=feature_request.md&title=X-Ray%20Compatible%20Feature%20Request).

### :mega: Python Versions End-of-Support Notice

AWS X-Ray SDK for Python versions `>2.11.0` has dropped support for Python 2.7, 3.4, 3.5, and 3.6.

# AWS X-Ray SDK for Python

![Screenshot of the AWS X-Ray console](/images/example_servicemap.png?raw=true)

## Installing

The AWS X-Ray SDK for Python is compatible with Python 3.7, 3.8, 3.9, 3.10, and 3.11.

Install the SDK using the following command (the SDK's non-testing dependencies will be installed).

```
pip install aws-xray-sdk
```

To install the SDK's testing dependencies, use the following command.

```
pip install tox
```

## Getting Help

Use the following community resources for getting help with the SDK. We use the GitHub
issues for tracking bugs and feature requests.

* Ask a question in the [AWS X-Ray Forum](https://forums.aws.amazon.com/forum.jspa?forumID=241&start=0).
* Open a support ticket with [AWS Support](http://docs.aws.amazon.com/awssupport/latest/user/getting-started.html).
* If you think you may have found a bug, open an [issue](https://github.com/aws/aws-xray-sdk-python/issues/new).

## Opening Issues

If you encounter a bug with the AWS X-Ray SDK for Python, we want to hear about
it. Before opening a new issue, search the [existing issues](https://github.com/aws/aws-xray-sdk-python/issues)
to see if others are also experiencing the issue. Include the version of the AWS X-Ray
SDK for Python, Python language, and botocore/boto3 if applicable. In addition, 
include the repro case when appropriate.

The GitHub issues are intended for bug reports and feature requests. For help and
questions about using the AWS SDK for Python, use the resources listed
in the [Getting Help](https://github.com/aws/aws-xray-sdk-python#getting-help) section. Keeping the list of open issues lean helps us respond in a timely manner.

## Documentation

The [developer guide](https://docs.aws.amazon.com/xray/latest/devguide) provides in-depth
guidance about using the AWS X-Ray service.
The [API Reference](http://docs.aws.amazon.com/xray-sdk-for-python/latest/reference/)
provides guidance for using the SDK and module-level documentation.

## Quick Start

### Configuration

```python
from aws_xray_sdk.core import xray_recorder

xray_recorder.configure(
    sampling=False,
    context_missing='LOG_ERROR',
    plugins=('EC2Plugin', 'ECSPlugin', 'ElasticBeanstalkPlugin'),
    daemon_address='127.0.0.1:3000',
    dynamic_naming='*mysite.com*'
)
```

### Start a custom segment/subsegment

Using context managers for implicit exceptions recording:

```python
from aws_xray_sdk.core import xray_recorder

with xray_recorder.in_segment('segment_name') as segment:
    # Add metadata or annotation here if necessary
    segment.put_metadata('key', dict, 'namespace')
    with xray_recorder.in_subsegment('subsegment_name') as subsegment:
        subsegment.put_annotation('key', 'value')
        # Do something here
    with xray_recorder.in_subsegment('subsegment2') as subsegment:
        subsegment.put_annotation('key2', 'value2')
        # Do something else 
```

async versions of context managers:

```python
from aws_xray_sdk.core import xray_recorder

async with xray_recorder.in_segment_async('segment_name') as segment:
    # Add metadata or annotation here if necessary
    segment.put_metadata('key', dict, 'namespace')
    async with xray_recorder.in_subsegment_async('subsegment_name') as subsegment:
        subsegment.put_annotation('key', 'value')
        # Do something here
    async with xray_recorder.in_subsegment_async('subsegment2') as subsegment:
        subsegment.put_annotation('key2', 'value2')
        # Do something else 
```

Default begin/end functions:

```python
from aws_xray_sdk.core import xray_recorder

# Start a segment
segment = xray_recorder.begin_segment('segment_name')
# Start a subsegment
subsegment = xray_recorder.begin_subsegment('subsegment_name')

# Add metadata or annotation here if necessary
segment.put_metadata('key', dict, 'namespace')
subsegment.put_annotation('key', 'value')
xray_recorder.end_subsegment()

# Close the segment
xray_recorder.end_segment()
```

### Oversampling Mitigation
To modify the sampling decision at the subsegment level, subsegments that inherit the decision of their direct parent (segment or subsegment) can be created using `xray_recorder.begin_subsegment()` and unsampled subsegments can be created using
`xray_recorder.begin_subsegment_without_sampling()`.

The code snippet below demonstrates creating a sampled or unsampled subsegment based on the sampling decision of each SQS message processed by Lambda.

```python
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core.models.subsegment import Subsegment
from aws_xray_sdk.core.utils.sqs_message_helper import SqsMessageHelper

def lambda_handler(event, context):

    for message in event['Records']:
        if SqsMessageHelper.isSampled(message):
            subsegment = xray_recorder.begin_subsegment('sampled_subsegment')
            print('sampled - processing SQS message')

        else:
            subsegment = xray_recorder.begin_subsegment_without_sampling('unsampled_subsegment')
            print('unsampled - processing SQS message')
    
    xray_recorder.end_subsegment()   
```

The code snippet below demonstrates wrapping a downstream AWS SDK request with an unsampled subsegment.
```python
from aws_xray_sdk.core import xray_recorder, patch_all
import boto3

patch_all()

def lambda_handler(event, context):
    subsegment = xray_recorder.begin_subsegment_without_sampling('unsampled_subsegment')
    client = boto3.client('sqs')
    print(client.list_queues())
    
    xray_recorder.end_subsegment()
```

### Capture

As a decorator:

```python
from aws_xray_sdk.core import xray_recorder

@xray_recorder.capture('subsegment_name')
def myfunc():
    # Do something here

myfunc()
```

or as a context manager:

```python
from aws_xray_sdk.core import xray_recorder

with xray_recorder.capture('subsegment_name') as subsegment:
    # Do something here
    subsegment.put_annotation('mykey', val)
    # Do something more
```

Async capture as decorator:

```python
from aws_xray_sdk.core import xray_recorder

@xray_recorder.capture_async('subsegment_name')
async def myfunc():
    # Do something here

async def main():
    await myfunc()
```

or as context manager:

```python
from aws_xray_sdk.core import xray_recorder

async with xray_recorder.capture_async('subsegment_name') as subsegment:
    # Do something here
    subsegment.put_annotation('mykey', val)
    # Do something more
```

### Adding annotations/metadata using recorder

```python
from aws_xray_sdk.core import xray_recorder

# Start a segment if no segment exist
segment1 = xray_recorder.begin_segment('segment_name')

# This will add the key value pair to segment1 as it is active
xray_recorder.put_annotation('key', 'value')

# Start a subsegment so it becomes the active trace entity
subsegment1 = xray_recorder.begin_subsegment('subsegment_name')

# This will add the key value pair to subsegment1 as it is active
xray_recorder.put_metadata('key', 'value')

if xray_recorder.is_sampled():
    # some expensitve annotations/metadata generation code here
    val = compute_annotation_val()
    metadata = compute_metadata_body()
    xray_recorder.put_annotation('mykey', val)
    xray_recorder.put_metadata('mykey', metadata)
```

### Generate NoOp Trace and Entity Id
X-Ray Python SDK will by default generate no-op trace and entity id for unsampled requests and secure random trace and entity id for sampled requests. If customer wants to enable generating secure random trace and entity id for all the (sampled/unsampled) requests (this is applicable for trace id injection into logs use case) then they should set the `AWS_XRAY_NOOP_ID` environment variable as False.

### Disabling X-Ray
Often times, it may be useful to be able to disable X-Ray for specific use cases, whether to stop X-Ray from sending traces at any moment, or to test code functionality that originally depended on X-Ray instrumented packages to begin segments prior to the code call. For example, if your application relied on an XRayMiddleware to instrument incoming web requests, and you have a method which begins subsegments based on the segment generated by that middleware, it would be useful to be able to disable X-Ray for your unit tests so that `SegmentNotFound` exceptions are not thrown when you need to test your method.

There are two ways to disable X-Ray, one is through environment variables, and the other is through the SDKConfig module.

**Disabling through the environment variable:**

Prior to running your application, make sure to have the environment variable `AWS_XRAY_SDK_ENABLED` set to `false`. 

**Disabling through the SDKConfig module:**
```
from aws_xray_sdk import global_sdk_config

global_sdk_config.set_sdk_enabled(False)
```

**Important Notes:**
* Environment Variables always take precedence over the SDKConfig module when disabling/enabling. If your environment variable is set to `false` while your code calls `global_sdk_config.set_sdk_enabled(True)`, X-Ray will still be disabled.

* If you need to re-enable X-Ray again during runtime and acknowledge disabling/enabling through the SDKConfig module, you may run the following in your application:
```
import os
from aws_xray_sdk import global_sdk_config

del os.environ['AWS_XRAY_SDK_ENABLED']
global_sdk_config.set_sdk_enabled(True)
```

### Trace AWS Lambda functions

```python
from aws_xray_sdk.core import xray_recorder

def lambda_handler(event, context):
    # ... some code

    subsegment = xray_recorder.begin_subsegment('subsegment_name')
    # Code to record
    # Add metadata or annotation here, if necessary
    subsegment.put_metadata('key', dict, 'namespace')
    subsegment.put_annotation('key', 'value')

    xray_recorder.end_subsegment()

    # ... some other code
```

### Trace ThreadPoolExecutor

```python
import concurrent.futures

import requests

from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch

patch(('requests',))

URLS = ['http://www.amazon.com/',
        'http://aws.amazon.com/',
        'http://example.com/',
        'http://www.bilibili.com/',
        'http://invalid-domain.com/']

def load_url(url, trace_entity):
    # Set the parent X-Ray entity for the worker thread.
    xray_recorder.set_trace_entity(trace_entity)
    # Subsegment captured from the following HTTP GET will be
    # a child of parent entity passed from the main thread.
    resp = requests.get(url)
    # prevent thread pollution
    xray_recorder.clear_trace_entities()
    return resp

# Get the current active segment or subsegment from the main thread.
current_entity = xray_recorder.get_trace_entity()
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    # Pass the active entity from main thread to worker threads.
    future_to_url = {executor.submit(load_url, url, current_entity): url for url in URLS}
    for future in concurrent.futures.as_completed(future_to_url):
        url = future_to_url[future]
        try:
            data = future.result()
        except Exception:
            pass
```

### Trace SQL queries
By default, if no other value is provided to `.configure()`, SQL trace streaming is enabled
for all the supported DB engines. Those currently are:
- Any engine attached to the Django ORM.
- Any engine attached to SQLAlchemy.

The behaviour can be toggled by sending the appropriate `stream_sql` value, for example:
```python
from aws_xray_sdk.core import xray_recorder

xray_recorder.configure(service='fallback_name', stream_sql=True)
```

### Patch third-party libraries

```python
from aws_xray_sdk.core import patch

libs_to_patch = ('boto3', 'mysql', 'requests')
patch(libs_to_patch)
```

#### Automatic module patching

Full modules in the local codebase can be recursively patched by providing the module references
to the patch function.
```python
from aws_xray_sdk.core import patch

libs_to_patch = ('boto3', 'requests', 'local.module.ref', 'other_module')
patch(libs_to_patch)
```
An `xray_recorder.capture()` decorator will be applied to all functions and class methods in the
given module and all the modules inside them recursively. Some files/modules can be excluded by
providing to the `patch` function a regex that matches them.
```python
from aws_xray_sdk.core import patch

libs_to_patch = ('boto3', 'requests', 'local.module.ref', 'other_module')
ignore = ('local.module.ref.some_file', 'other_module.some_module\.*')
patch(libs_to_patch, ignore_module_patterns=ignore)
```

### Django
#### Add Django middleware

In django settings.py, use the following.

```python
INSTALLED_APPS = [
    # ... other apps
    'aws_xray_sdk.ext.django',
]

MIDDLEWARE = [
    'aws_xray_sdk.ext.django.middleware.XRayMiddleware',
    # ... other middlewares
]
```

You can configure the X-Ray recorder in a Django app under the ‘XRAY_RECORDER’ namespace. For a minimal configuration, the 'AWS_XRAY_TRACING_NAME' is required unless it is specified in an environment variable.
```
XRAY_RECORDER = {
    'AWS_XRAY_TRACING_NAME': 'My application', # Required - the segment name for segments generated from incoming requests
}
```
For more information about configuring Django with X-Ray read more about it in the [API reference](https://docs.aws.amazon.com/xray-sdk-for-python/latest/reference/frameworks.html)

#### SQL tracing
If Django's ORM is patched - either using the `AUTO_INSTRUMENT = True` in your settings file
or explicitly calling `patch_db()` - the SQL query trace streaming can then be enabled or 
disabled updating the `STREAM_SQL` variable in your settings file. It is enabled by default.

#### Automatic patching
The automatic module patching can also be configured through Django settings.
```python
XRAY_RECORDER = {
    'PATCH_MODULES': [
        'boto3',
        'requests',
        'local.module.ref',
        'other_module',
    ],
    'IGNORE_MODULE_PATTERNS': [
        'local.module.ref.some_file',
        'other_module.some_module\.*',
    ],
    ...
}
```
If `AUTO_PATCH_PARENT_SEGMENT_NAME` is also specified, then a segment parent will be created 
with the supplied name, wrapping the automatic patching so that it captures any dangling
subsegments created on the import patching.

### Django in Lambda
X-Ray can't search on http annotations in subsegments.   To enable searching the middleware adds the http values as annotations
This allows searching in the X-Ray console like so

This is configurable in settings with `URLS_AS_ANNOTATION` that has 3 valid values
`LAMBDA` - the default, which uses URLs as annotations by default if running in a lambda context
`ALL` - do this for every request (useful if running in a mixed lambda/other deployment)
`NONE` - don't do this for any (avoiding hitting the 50 annotation limit)

```
annotation.url BEGINSWITH "https://your.url.com/here"
```

### Add Flask middleware

```python
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.ext.flask.middleware import XRayMiddleware

app = Flask(__name__)

xray_recorder.configure(service='fallback_name', dynamic_naming='*mysite.com*')
XRayMiddleware(app, xray_recorder)
```

### Add Bottle middleware(plugin)

```python
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.ext.bottle.middleware import XRayMiddleware

app = Bottle()

xray_recorder.configure(service='fallback_name', dynamic_naming='*mysite.com*')
app.install(XRayMiddleware(xray_recorder))
```

### Serverless Support for Flask & Django & Bottle Using X-Ray
Serverless is an application model that enables you to shift more of your operational responsibilities to AWS. As a result, you can focus only on your applications and services, instead of the infrastructure management tasks such as server provisioning, patching, operating system maintenance, and capacity provisioning. With serverless, you can deploy your web application to [AWS Lambda](https://aws.amazon.com/lambda/) and have customers interact with it through a Lambda-invoking endpoint, such as [Amazon API Gateway](https://aws.amazon.com/api-gateway/). 

X-Ray supports the Serverless model out of the box and requires no extra configuration. The middlewares in Lambda generate `Subsegments` instead of `Segments` when an endpoint is reached. This is because `Segments` cannot be generated inside the Lambda function, but it is generated automatically by the Lambda container. Therefore, when using the middlewares with this model, it is important to make sure that your methods only generate `Subsegments`.

The following guide shows an example of setting up a Serverless application that utilizes API Gateway and Lambda:

[Instrumenting Web Frameworks in a Serverless Environment](https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-python-serverless.html)

### Working with aiohttp

Adding aiohttp middleware. Support aiohttp >= 2.3.

```python
from aiohttp import web

from aws_xray_sdk.ext.aiohttp.middleware import middleware
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core.async_context import AsyncContext

xray_recorder.configure(service='fallback_name', context=AsyncContext())

app = web.Application(middlewares=[middleware])
app.router.add_get("/", handler)

web.run_app(app)
```

Tracing aiohttp client. Support aiohttp >=3.

```python
from aws_xray_sdk.ext.aiohttp.client import aws_xray_trace_config

async def foo():
    trace_config = aws_xray_trace_config()
    async with ClientSession(loop=loop, trace_configs=[trace_config]) as session:
        async with session.get(url) as resp
            await resp.read()
```

### Use SQLAlchemy ORM
The SQLAlchemy integration requires you to override the Session and Query Classes for SQL Alchemy

SQLAlchemy integration uses subsegments so you need to have a segment started before you make a query.

```python
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.ext.sqlalchemy.query import XRaySessionMaker

xray_recorder.begin_segment('SQLAlchemyTest')

Session = XRaySessionMaker(bind=engine)
session = Session()

xray_recorder.end_segment()
app = Flask(__name__)

xray_recorder.configure(service='fallback_name', dynamic_naming='*mysite.com*')
XRayMiddleware(app, xray_recorder)
```

### Add Flask-SQLAlchemy

```python
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.ext.flask.middleware import XRayMiddleware
from aws_xray_sdk.ext.flask_sqlalchemy.query import XRayFlaskSqlAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

XRayMiddleware(app, xray_recorder)
db = XRayFlaskSqlAlchemy(app)

```

### Ignoring httplib requests

If you want to ignore certain httplib requests you can do so based on the hostname or URL that is being requsted. The hostname is matched using the Python [fnmatch library](https://docs.python.org/3/library/fnmatch.html) which does Unix glob style matching.

```python
from aws_xray_sdk.ext.httplib import add_ignored as xray_add_ignored

# ignore requests to test.myapp.com
xray_add_ignored(hostname='test.myapp.com')

# ignore requests to a subdomain of myapp.com with a glob pattern
xray_add_ignored(hostname='*.myapp.com')

# ignore requests to /test-url and /other-test-url
xray_add_ignored(urls=['/test-path', '/other-test-path'])

# ignore requests to myapp.com for /test-url
xray_add_ignored(hostname='myapp.com', urls=['/test-url'])
```

If you use a subclass of httplib to make your requests, you can also filter on the class name that initiates the request. This must use the complete package name to do the match.

```python
from aws_xray_sdk.ext.httplib import add_ignored as xray_add_ignored

# ignore all requests made by botocore
xray_add_ignored(subclass='botocore.awsrequest.AWSHTTPConnection')
```

## License

The AWS X-Ray SDK for Python is licensed under the Apache 2.0 License. See LICENSE and NOTICE.txt for more information.
