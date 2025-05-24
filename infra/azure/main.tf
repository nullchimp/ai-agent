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
variable "resource_group"  { type = string }
variable "node_vm_size" {
  type        = string
  description = "VM size of the default AKS node-pool - must have 2+ cores and 4GB+ RAM for system pool"
  default     = "Standard_B2s"
}

locals {
  rg_name  = "${var.resource_group}-${var.environment}"
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
#  AKS CLUSTER - MINIMAL COST CONFIGURATION
############################
resource "azurerm_kubernetes_cluster" "this" {
  name                = local.aks_name
  location            = azurerm_resource_group.this.location
  resource_group_name = azurerm_resource_group.this.name
  dns_prefix          = "memgraph-${var.environment}"
  
  # Minimal cost settings
  sku_tier = "Free"
  
  default_node_pool {
    name                = "default"
    node_count          = 1
    min_count           = 1
    max_count           = 2
    vm_size             = var.node_vm_size
    enable_auto_scaling = true
    
    # Cost optimization
    os_disk_type = "Ephemeral"
    os_disk_size_gb = 30
    
    # Use spot instances for even lower cost (optional)
    # priority = "Spot"
    # eviction_policy = "Delete"
    # spot_max_price = 0.01
  }

  identity { 
    type = "SystemAssigned" 
  }
  
  network_profile {
    network_plugin = "azure"
    load_balancer_sku = "standard"
  }
  
  # Disable unnecessary features for cost
  private_cluster_enabled = false
  
  tags = {
    Environment = var.environment
    Purpose     = "memgraph-database"
    CostCenter  = "minimal"
  }
}

############################
#  OUTPUTS (handy in logs)
############################
output "resource_group" { value = azurerm_resource_group.this.name }
output "aks_cluster"    { value = azurerm_kubernetes_cluster.this.name }
