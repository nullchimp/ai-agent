variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "memgraph_username" {
  description = "Memgraph username"
  type        = string
  sensitive   = true
}

variable "memgraph_password" {
  description = "Memgraph password"
  type        = string
  sensitive   = true
}

variable "subscription_id" {
  description = "The Azure subscription ID"
  type        = string
}