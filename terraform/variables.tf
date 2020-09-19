variable "region" {
  type        = string
  description = "AWS region for deployment of resources"
}

variable "bucket_name" {
  type        = string
  description = "AWS s3 bucket name"
}

variable "bucket_key" {
  type        = string
  description = "AWS s3 object key"
}

variable "source_path" {
  type        = string
  description = "local source zip path to upload on AWS s3 bucket"
}

variable "eb_app_name" {
  type        = string
  description = "Elastic Beanstalk application name"
}

variable "eb_app_version_label" {
  type        = string
  description = "Elastic Beanstalk application version label"
}

variable "eb_env_name" {
  type        = string
  description = "Elastic Beanstalk environment name"
}

variable "eb_env_cname_prefix" {
  type = string
  description = "Elastic Beanstalk environment CNAME prefix"
}

variable "resource_prefix" {
  type = string
  description = "constant variable to create unique resource name"
}