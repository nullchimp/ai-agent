provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}

# Use existing GitHub resource group
data "azurerm_resource_group" "github" {
  name = "GitHub"
}

# Key Vault for secret management
resource "azurerm_key_vault" "ai_agent" {
  name                = "kv-ai-agent-${var.environment}"
  location            = data.azurerm_resource_group.github.location
  resource_group_name = data.azurerm_resource_group.github.name
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = "standard"
  
  purge_protection_enabled = true

  access_policy {
    tenant_id = var.tenant_id
    object_id = var.object_id

    secret_permissions = [
      "Get",
      "List",
      "Set",
    ]
  }
}

# Add secrets to Key Vault
resource "azurerm_key_vault_secret" "memgraph_username" {
  name         = "memgraph-username"
  value        = var.memgraph_username
  key_vault_id = azurerm_key_vault.ai_agent.id
}

resource "azurerm_key_vault_secret" "memgraph_password" {
  name         = "memgraph-password"
  value        = var.memgraph_password
  key_vault_id = azurerm_key_vault.ai_agent.id
}

# Container Registry for storing images
resource "azurerm_container_registry" "ai_agent" {
  name                = "craiagentreg${var.environment}"
  resource_group_name = data.azurerm_resource_group.github.name
  location            = data.azurerm_resource_group.github.location
  sku                 = "Basic"
  admin_enabled       = true
}

# For AKS deployment
resource "azurerm_kubernetes_cluster" "ai_agent" {
  name                = "aks-ai-agent-${var.environment}"
  location            = data.azurerm_resource_group.github.location
  resource_group_name = data.azurerm_resource_group.github.name
  dns_prefix          = "aiagent"

  default_node_pool {
    name       = "default"
    node_count = 1
    vm_size    = "Standard_D4_v2"
  }

  identity {
    type = "SystemAssigned"
  }
}

# Define a separate node pool with auto-scaling enabled
resource "azurerm_kubernetes_cluster_node_pool" "ai_agent_pool" {
  name                  = "agentpool"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.ai_agent.id
  vm_size               = "Standard_D4_v2"
  enable_auto_scaling   = true
  min_count             = 1
  max_count             = 3
}

# For access to Key Vault from AKS
resource "azurerm_key_vault_access_policy" "aks" {
  key_vault_id = azurerm_key_vault.ai_agent.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = azurerm_kubernetes_cluster.ai_agent.identity[0].principal_id

  secret_permissions = [
    "Get", "List"
  ]
}

# Output the AKS cluster name
output "kubernetes_cluster_name" {
  value = azurerm_kubernetes_cluster.ai_agent.name
}

# Output the AKS resource group name
output "resource_group_name" {
  value = data.azurerm_resource_group.github.name
}

data "azurerm_client_config" "current" {}
