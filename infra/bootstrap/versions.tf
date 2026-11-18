terraform {
  required_version = ">= 1.11"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.90, < 6.0"
    }
  }

  # Estado local a proposito (NFR5.6): lo respalda la persona fuera del repositorio y, si se
  # pierde, se reconstruye con `terraform import` de los pocos recursos del arranque.
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      project = "business-analyst-agent"
      unit    = "u6-infrastructure-bootstrap"
    }
  }
}
