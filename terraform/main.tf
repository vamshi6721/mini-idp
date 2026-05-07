terraform {

  required_providers {

    docker = {

      source = "kreuzwerker/docker"

      version = "3.0.2"
    }
  }
}

provider "docker" {

  host = "unix:///var/run/docker.sock"
}

variable "service_name" {

  type = string
}

variable "service_port" {

  type = number
}

resource "docker_image" "service_image" {

  name = var.service_name

  build {

    context = "../services/${var.service_name}"
  }
}

resource "docker_container" "service_container" {

  name  = var.service_name

  image = docker_image.service_image.image_id

  ports {

    internal = var.service_port
    external = var.service_port
  }
}
