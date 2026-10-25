variable "project_name" {
  description = "Project name used as a prefix for all resources"
  type        = string
  default     = "devops-infra"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be one of: dev, staging, prod."
  }
}

variable "docker_host" {
  description = "Docker daemon address"
  type        = string
  default     = "unix:///var/run/docker.sock"
}

variable "image_name" {
  description = "Name of the application image"
  type        = string
  default     = "devops-app"
}

variable "image_tag" {
  description = "Tag of the application image"
  type        = string
  default     = "1.0.0"
}

variable "app_port" {
  description = "First host port to publish the application on"
  type        = number
  default     = 8080

  validation {
    condition     = var.app_port >= 1024 && var.app_port <= 65000
    error_message = "app_port must be between 1024 and 65000."
  }
}

variable "replicas" {
  description = "Number of application containers"
  type        = number
  default     = 1

  validation {
    condition     = var.replicas >= 1 && var.replicas <= 5
    error_message = "replicas must be between 1 and 5."
  }
}
