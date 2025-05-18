variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "memgraph_username" {
  description = "Memgraph username"
  type        = string
  sensitive   = true
  default     = "placeholder-for-import"  # Default placeholder for import operations
}

variable "memgraph_password" {
  description = "Memgraph password"
  type        = string
  sensitive   = true
  default     = "placeholder-for-import"  # Default placeholder for import operations
}

variable "subscription_id" {
  description = "The Azure subscription ID"
  type        = string
  default     = ""  # Will be populated from environment in import_resources.sh
}

variable "tenant_id" {
  description = "The Azure tenant ID"
  type        = string
  default     = ""  # Will be populated from environment in import_resources.sh
}

variable "object_id" {
  description = "The object ID of the service principal"
  type        = string
  default     = ""  # Will be populated from environment in import_resources.sh
}