terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "3.5.0"
    }
  }
}

provider "aws" {
  profile = "default"
  region  = var.region
}

resource "aws_s3_bucket_public_access_block" "bucket_access" {
  bucket = aws_s3_bucket.eb_app_bucket.id

  restrict_public_buckets   = true
}

resource "aws_s3_bucket" "eb_app_bucket" {
  bucket = "${var.resource_prefix}.eb.app.applicationversion"

  versioning {
    enabled = true
  }

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm     = "AES256"
      }
    }
  }
}

resource "aws_s3_bucket_object" "eb_app_package" {
  bucket = aws_s3_bucket.eb_app_bucket.id
  key    = var.bucket_key
  source = var.source_path
}

resource "aws_elastic_beanstalk_application" "eb_app" {
  name        = "${var.resource_prefix}-EB-App"
  description = "Deployment of EB App for integration testing"
}

resource "aws_elastic_beanstalk_application_version" "eb_app_version" {
  name        = "${var.resource_prefix}-EB-App-1"
  application = aws_elastic_beanstalk_application.eb_app.name
  bucket      = aws_s3_bucket.eb_app_bucket.id
  key         = aws_s3_bucket_object.eb_app_package.id
}

resource "aws_elastic_beanstalk_environment" "eb_env" {
  name                = "${var.resource_prefix}-EB-App-Env"
  application         = aws_elastic_beanstalk_application.eb_app.name
  solution_stack_name = "64bit Amazon Linux 2 v3.5.10 running Python 3.8"
  tier = "WebServer"
  version_label = aws_elastic_beanstalk_application_version.eb_app_version.name
  cname_prefix = "${var.resource_prefix}-Eb-app-env"

  setting {
    namespace = "aws:autoscaling:launchconfiguration"
    name = "IamInstanceProfile"
    value = "aws-elasticbeanstalk-ec2-role"
  }

  setting {
    namespace = "aws:elasticbeanstalk:xray"
    name = "XRayEnabled"
    value = "true"
  }
  
  setting {
    namespace = "aws:autoscaling:launchconfiguration"
    name = "DisableIMDSv1"
    value = "true"
  }
}
