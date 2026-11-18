variable "github_repository" {
  description = "Repositorio de GitHub con formato <organizacion>/<repositorio>; entra en el sub exacto de la confianza OIDC de los dos roles (NFR5.2). Lo informa la persona al ejecutar el arranque."
  type        = string

  validation {
    condition     = can(regex("^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$", var.github_repository))
    error_message = "github_repository debe ser <organizacion>/<repositorio>, sin comodines ni segmentos extra."
  }
}

variable "state_bucket_name" {
  description = "Nombre del deposito de S3 del estado remoto de infra/ (unico en el mundo). Lo informa la persona."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$", var.state_bucket_name))
    error_message = "state_bucket_name debe tener de 3 a 63 caracteres: minusculas, digitos, puntos y guiones."
  }
}

variable "name_prefix" {
  description = "Prefijo de los nombres de los recursos y de los roles de la aplicacion; acota los permisos del rol de aplicacion."
  type        = string
  default     = "business-analyst-agent"
}

variable "region" {
  description = "Region de AWS (fija: us-east-1, igual que infra/variables.tf; las politicas y los ARN la usan)."
  type        = string
  default     = "us-east-1"

  validation {
    condition     = var.region == "us-east-1"
    error_message = "region debe ser us-east-1."
  }
}
