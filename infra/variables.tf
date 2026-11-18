variable "region" {
  description = "Region de AWS (fija: us-east-1)."
  type        = string
  default     = "us-east-1"

  # El arranque (infra/bootstrap) y los ARN de sus politicas estan fijos en us-east-1.
  validation {
    condition     = var.region == "us-east-1"
    error_message = "region debe ser us-east-1."
  }
}

variable "name_prefix" {
  description = "Prefijo de los nombres de los recursos."
  type        = string
  default     = "business-analyst-agent"
}

variable "bedrock_model_id" {
  description = "Identificador del modelo (o perfil de inferencia) de Bedrock; viene de configuracion, no del codigo."
  type        = string
  default     = "us.anthropic.claude-sonnet-4-6"

  # Mismo patron exacto que ModelProfile en backend/story_service/model_profile.py (NFR5.3).
  # Esta variable es la unica fuente del permiso del rol y de BEDROCK_MODEL_ID (NFR5.2).
  validation {
    condition = can(regex(
      "^((us\\.|global\\.)?anthropic\\.claude-|(us\\.)?amazon\\.titan-)[A-Za-z0-9][A-Za-z0-9._:-]*$",
      var.bedrock_model_id
    ))
    error_message = "bedrock_model_id debe ser anthropic.claude-* (con prefijo us. o global.) o amazon.titan-* (con prefijo us.)."
  }
}

variable "bedrock_model_arns" {
  description = "ARN del modelo y del perfil de inferencia que la funcion puede invocar (permiso minimo, solo el modelo configurado). Si es vacio se calcula a partir de bedrock_model_id."
  type        = list(string)
  default     = []
}

# ---------------------------------------------------------------------------
# Identidad (u4/u6). Ningun valor real vive en el repositorio (NFR5.1): llegan por TF_VAR_<nombre>
# desde secretos y variables de GitHub, y todas son sensibles.
# ---------------------------------------------------------------------------

variable "allowed_emails" {
  description = "Lista de correos permitidos (BR4.3), separados por comas, en minusculas, hasta 50. Dato personal de acceso restringido (NFR4.3): llega a la funcion como ALLOWED_EMAILS."
  type        = string
  sensitive   = true

  validation {
    condition = (
      length(var.allowed_emails) > 0 &&
      length(split(",", var.allowed_emails)) <= 50 &&
      alltrue([
        for entry in split(",", var.allowed_emails) :
        can(regex("^[a-z0-9._%+-]+@[a-z0-9.-]+\\.[a-z]{2,}$", entry))
      ])
    )
    error_message = "allowed_emails debe tener de 1 a 50 correos separados por comas, en minusculas, sin espacios ni entradas vacias."
  }
}

variable "google_client_id" {
  description = "Identificador de cliente OAuth de Google (secreto de GitHub TF_VAR_google_client_id)."
  type        = string
  sensitive   = true
}

variable "google_client_secret" {
  description = "Secreto de cliente OAuth de Google (secreto de GitHub TF_VAR_google_client_secret)."
  type        = string
  sensitive   = true
}

variable "microsoft_client_id" {
  description = "Identificador de cliente de la aplicacion de Microsoft Entra (secreto de GitHub TF_VAR_microsoft_client_id)."
  type        = string
  sensitive   = true
}

variable "microsoft_client_secret" {
  description = "Secreto de cliente de Microsoft Entra (secreto de GitHub TF_VAR_microsoft_client_secret)."
  type        = string
  sensitive   = true
}

variable "cognito_domain_prefix" {
  description = "Prefijo del dominio alojado de Cognito (https://<prefijo>.auth.us-east-1.amazoncognito.com). Es fijo para conocer de antemano la direccion de retorno de las federaciones; si ya esta tomado en la region, se cambia aqui antes del primer despliegue."
  type        = string
  default     = "business-analyst-agent-x7k2m9"

  validation {
    condition = (
      can(regex("^[a-z0-9]([a-z0-9-]{0,48}[a-z0-9])?$", var.cognito_domain_prefix)) &&
      !can(regex("aws|amazon|cognito", var.cognito_domain_prefix))
    )
    error_message = "cognito_domain_prefix: minusculas, digitos y guiones (1 a 50), y sin las palabras reservadas aws, amazon ni cognito."
  }
}

variable "reserved_concurrency" {
  description = "Concurrencia reservada de la funcion (NFR3.1). Sujeta a la cuota de la cuenta: si no se puede reservar 5, poner -1 y el tope lo da el limite de la pasarela."
  type        = number
  default     = 5
}

variable "live_version" {
  description = "Version numerada de la funcion a la que apunta el alias live. Vacio = la ultima publicada. Retroceder es volver a aplicar con la version anterior."
  type        = string
  default     = ""
}

variable "throttle_rate_limit" {
  description = "Solicitudes por segundo sostenidas permitidas por la pasarela (NFR3.2 parcial)."
  type        = number
  default     = 1
}

variable "throttle_burst_limit" {
  description = "Rafaga permitida por la pasarela."
  type        = number
  default     = 5
}

variable "integration_timeout_ms" {
  description = "Tiempo de espera de la integracion de la pasarela (58 s). Requiere ampliar la cuota de la cuenta (supuesto, ID Q3)."
  type        = number
  default     = 58000
}

variable "microsoft_tenant_id" {
  description = "Identificador (GUID) del inquilino de Microsoft Entra cuyo emisor valida Cognito (el emisor `common` no sirve: Cognito exige el mismo emisor que el token). Por defecto el de las cuentas personales de Microsoft; la persona lo confirma al crear la aplicacion de Entra. No es un secreto."
  type        = string
  default     = "9188040d-6c67-4c5b-b112-36a304b66dad"

  validation {
    condition     = can(regex("^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", var.microsoft_tenant_id))
    error_message = "microsoft_tenant_id debe ser un GUID en minusculas."
  }
}
