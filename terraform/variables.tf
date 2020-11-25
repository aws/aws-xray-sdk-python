variable "region" {
  type        = string
  description = "AWS region for deployment of resources"
}

variable "bucket_key" {
  type        = string
  description = "AWS s3 object key"
}

variable "source_path" {
  type        = string
  description = "local source zip path to upload on AWS s3 bucket"
}

variable "resource_prefix" {}

