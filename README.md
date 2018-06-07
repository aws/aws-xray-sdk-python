[![Build Status](https://travis-ci.org/aws/aws-xray-sdk-python.svg?branch=master)](https://travis-ci.org/aws/aws-xray-sdk-python)

# AWS X-Ray SDK for Python

![Screenshot of the AWS X-Ray console](/images/example_servicemap.png?raw=true)

## Installing

The AWS X-Ray SDK for Python is compatible with Python 2.7, 3.4, 3.5, and 3.6.

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

### Capture

```python
from aws_xray_sdk.core import xray_recorder

@xray_recorder.capture('subsegment_name')
def myfunc():
    # Do something here

myfunc()
```

```python
from aws_xray_sdk.core import xray_recorder

@xray_recorder.capture_async('subsegment_name')
async def myfunc():
    # Do something here

async def main():
    await myfunc()
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

### Patch third-party libraries

```python
from aws_xray_sdk.core import patch

libs_to_patch = ('boto3', 'mysql', 'requests')
patch(libs_to_patch)
```

### Add Django middleware

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

### Add Flask middleware

```python
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.ext.flask.middleware import XRayMiddleware

app = Flask(__name__)

xray_recorder.configure(service='fallback_name', dynamic_naming='*mysite.com*')
XRayMiddleware(app, xray_recorder)
```

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
## License

The AWS X-Ray SDK for Python is licensed under the Apache 2.0 License. See LICENSE and NOTICE.txt for more information.
