terraform {
  # NFR5.7: 1.11 o superior (el bloqueo nativo de S3 con use_lockfile es estable desde esa version).
  required_version = ">= 1.11"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.90, < 6.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }

  # NFR5.6: estado remoto en el deposito de S3 que crea infra/bootstrap/. Configuracion parcial:
  # el nombre del deposito llega por `terraform init -backend-config="bucket=<deposito>"`; no hay
  # alternativa local (si el deposito no existe, `init` falla y la canalizacion se detiene).
  # La clave coincide con el prefijo de s3:ListBucket del rol de la canalizacion (infra/bootstrap).
  backend "s3" {
    key          = "business-analyst-agent/terraform.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      project = "business-analyst-agent"
      unit    = "u6-infrastructure"
    }
  }
}
