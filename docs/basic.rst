.. _basic:

Basic Usage
===========

The SDK provides a global recorder, ``xray_recorder``, to generate segments and subsegments.

Manually create segment/subsegment
----------------------------------
If you're using a web framework or library that is not supported, or you want to define
your own structure on segments/subsegments, you can manually create 
segments and subsegments by using code like the following::

    from aws_xray_sdk.core import xray_recorder
    
    xray_recorder.begin_segment('name')

    # your code here

    xray_recorder.begin_subsegment('name')
    # some code block you want to record
    xray_recorder.end_subsegment()

    xray_recorder.end_segment()

The ``xray_recorder`` keeps one segment per thread.
Therefore, in manual mode, call ``xray_recorder.end_segment()`` before creating a new segment,
otherwise the new segment overwrites the existing one.
To trace a particular code block inside a segment, use a subsegment.
If you open a new subsegment while there is already an open subsegment,
the new subsegment becomes the child of the existing subsegment.

Decorator for function auto-capture
-----------------------------------
A decorator is provided to easily capture basic information as a subsegment on
user defined functions. You can use the decorator like the following::
    
    @xray_recorder.capture('name')
    def my_func():
        #do something

``xray_recorder`` generates a subsegment for the decorated function, where the name is optional.
If the name argument is not provided, the function name is used as the subsegment name.
If the function is called without an open segment in the context storage, the subsegment is discarded.
Currently the decorator only works with synchronous functions.

Set annotation or metadata
--------------------------
You can add annotations and metadata to an active segment/subsegment.

Annotations are simple key-value pairs that are indexed for use with
`filter expressions <http://docs.aws.amazon.com/xray/latest/devguide/xray-console-filters.html>`_.
Use annotations to record data that you want to use to group traces in the console,
or when calling the GetTraceSummaries API.

Metadata are key-value pairs with values of any type, including objects and lists, but that are not indexed.
Use metadata to record data you want to store in the trace but don't need to use for searching traces.

You can add annotations/metadata like the following::

    from aws_xray_sdk.core import xray_recorder

    segment = xray_recorder.current_segment()
    # value can be string, number or bool
    segment.put_annotation('key', value)
    # namespace and key must be string and value is an object
    # that can be serialized to json
    segment.put_metadata('key', json, 'namespace')

The ``current_segment`` and ``current_subsegment`` functions get the current
open segment or subsegment, respectively, from context storage.
Put these calls between segment or subsegment begin and end statements.

AWS Lambda Integration
----------------------

To integrate with Lambda you must
first enable active tracing on a Lambda function.
See http://docs.aws.amazon.com/lambda/latest/dg/lambda-x-ray.html#using-x-ray for details.

In your Lambda function, you can only begin and end a subsegment.
The Lambda service emits a segment as the root.
This segment cannot be mutated.
Instrument the SDK as you would in any Python script.
Subsegments generated outside of the Lambda handler are discarded.
