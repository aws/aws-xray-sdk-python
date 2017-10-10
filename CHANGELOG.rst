=========
CHANGELOG
=========

0.93
====
* The X-Ray SDK for Python is now an open source project. You can follow the project and submit issues and pull requests on GitHub: https://github.com/aws/aws-xray-sdk-python

0.92.2
======
* bugfix: Fixed an issue that caused the X-Ray recorder to omit the origin when recording segments with a service plugin. This caused the service's type to not appear on the service map in the X-Ray console.

0.92.1
======
* bugfix: Fixed an issue that caused all calls to Amazon DynamoDB tables to be grouped under a single node in the service map. With this update, each table gets a separate node.

0.92
====

* feature: Add Flask support
* feature: Add dynamic naming on segment name

0.91.1
======

* bugfix: The SDK has been released as a universal wheel
