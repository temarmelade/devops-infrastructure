terraform {
  required_version = ">= 1.5.0"

  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {
  host = var.docker_host
}

locals {
  name_prefix = "${var.project_name}-${var.environment}"
  common_labels = {
    project     = var.project_name
    environment = var.environment
    managed_by  = "terraform"
  }
}

# Builds the application image from docker/Dockerfile (context = repository root)
resource "docker_image" "app" {
  name         = "${var.image_name}:${var.image_tag}"
  keep_locally = true

  build {
    context    = "${path.module}/.."
    dockerfile = "docker/Dockerfile"
    label      = local.common_labels
  }
}

resource "docker_network" "app" {
  name = "${local.name_prefix}-net"
}

resource "docker_container" "app" {
  count = var.replicas

  name    = "${local.name_prefix}-app-${count.index}"
  image   = docker_image.app.image_id
  restart = "unless-stopped"

  env = [
    "APP_ENV=${var.environment}",
    "APP_VERSION=${var.image_tag}",
    "APP_PORT=8080",
  ]

  ports {
    internal = 8080
    external = var.app_port + count.index
  }

  networks_advanced {
    name    = docker_network.app.name
    aliases = ["app"]
  }

  healthcheck {
    test         = ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=2)"]
    interval     = "30s"
    timeout      = "3s"
    retries      = 3
    start_period = "5s"
  }

  dynamic "labels" {
    for_each = local.common_labels
    content {
      label = labels.key
      value = labels.value
    }
  }
}

output "app_urls" {
  description = "URLs of the running application containers"
  value       = [for i in range(var.replicas) : "http://localhost:${var.app_port + i}"]
}

output "image_id" {
  description = "ID of the built application image"
  value       = docker_image.app.image_id
}
