.. aws-xray-sdk documentation master file, created by
   sphinx-quickstart on Wed Aug  2 15:33:56 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to the AWS X-Ray SDK for Python!
========================================
This project is open sourced in Github. Please see: https://github.com/aws/aws-xray-sdk-python.

The AWS X-Ray service accepts application information in the form of trace segments.
A trace segment represents the work done by a single machine as a part of the entire task or request.
A set of trace segments which share the same trace ID form a trace.
A trace represents a full unit of work completed for a single task or request.
Learn more about AWS X-Ray service: https://aws.amazon.com/xray/.

The AWS X-Ray SDK for Python (the SDK) enables Python developers to record and emit
information from within their applications to the AWS X-Ray service.
You can get started in minutes using ``pip`` or by downloading a zip file.

Currently supported web frameworks and libraries:

* django >=1.10
* flask
* boto3
* botocore
* requests
* sqlite3 
* mysql-connector

You must have the X-Ray daemon running to use the SDK.
For information about installing and configuring the daemon see:
http://docs.aws.amazon.com/xray/latest/devguide/xray-daemon.html.


Contents:


.. toctree::
   :maxdepth: 2

   Basic Usage <basic>
   Recorder Configurations <configurations>
   Third Party Libraries <thirdparty>
   Working with Web Frameworks <frameworks>
   Change Log <changes>
   License <license>

Indices and tables
==================

* :ref:`modindex`
* :ref:`search`
