terraform {
  required_version = ">= 1.5.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.107"
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}

############################
#  VARIABLES
############################
variable "subscription_id" { type = string }
variable "location"        { type = string }
variable "environment"     { type = string }
variable "node_vm_size" {
  type        = string
  description = "VM size of the default AKS node-pool"
  default     = "Standard_B2ms"
}

locals {
  rg_name  = "rg-aks-memgraph-${var.environment}"
  aks_name = "aks-memgraph-${var.environment}"
}

############################
#  RESOURCE GROUP
############################
resource "azurerm_resource_group" "this" {
  name     = local.rg_name
  location = var.location
}

############################
#  AKS CLUSTER
############################
resource "azurerm_kubernetes_cluster" "this" {
  name                = local.aks_name
  location            = azurerm_resource_group.this.location
  resource_group_name = azurerm_resource_group.this.name
  dns_prefix          = "memgraph-${var.environment}"

  default_node_pool {
    name       = "default"
    node_count = 1
    vm_size    = var.node_vm_size
  }

  identity { type = "SystemAssigned" }
}

############################
#  OUTPUTS (handy in logs)
############################
output "resource_group" { value = azurerm_resource_group.this.name }
output "aks_cluster"    { value = azurerm_kubernetes_cluster.this.name }
