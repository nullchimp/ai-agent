provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
  }
  subscription_id = var.subscription_id
}

# Use existing GitHub resource group
data "azurerm_resource_group" "github" {
  name = "GitHub"
}

# Get a list of all resources in the resource group
data "azurerm_resources" "all" {
  resource_group_name = data.azurerm_resource_group.github.name
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
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = var.object_id

    secret_permissions = [
      "Get",
      "List",
      "Set",
    ]
  }
  
  # Add the current user/service principal
  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = data.azurerm_client_config.current.object_id

    secret_permissions = [
      "Get",
      "List",
      "Set",
      "Delete",
      "Recover",
      "Backup",
      "Restore"
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
    name                   = "default"
    node_count             = 1
    vm_size                = "Standard_E2a_v4"
    temporary_name_for_rotation = "tempnodepool"
  }

  identity {
    type = "SystemAssigned"
  }
}

# Define a separate node pool with auto-scaling enabled
resource "azurerm_kubernetes_cluster_node_pool" "ai_agent_pool" {
  name                  = "agentpool"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.ai_agent.id
  vm_size               = "Standard_E2a_v4"
  auto_scaling_enabled  = true
  min_count             = 1
  max_count             = 3
  temporary_name_for_rotation = "tmppool"
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

# Define the managed resources to exclude from cleanup
locals {
  managed_resource_ids = [
    azurerm_key_vault.ai_agent.id,
    azurerm_container_registry.ai_agent.id,
    azurerm_kubernetes_cluster.ai_agent.id,
    # Include node pool explicitly
    "${azurerm_kubernetes_cluster.ai_agent.id}/agentPools/agentpool"
  ]
  
  # Resource prefixes to always keep (partial matching)
  keep_resource_prefixes = [
    "Microsoft.ContainerService/managedClusters/aks-ai-agent-${var.environment}",
    "Microsoft.KeyVault/vaults/kv-ai-agent-${var.environment}",
    "Microsoft.ContainerRegistry/registries/craiagentreg${var.environment}"
  ]
}

# Resource to clean up unmanaged resources
resource "null_resource" "cleanup_unmanaged_resources" {
  triggers = {
    resource_group = data.azurerm_resource_group.github.name
    environment = var.environment
  }

  provisioner "local-exec" {
    command = <<EOT
#!/bin/bash
set -e
echo "Starting cleanup of unmanaged resources in ${data.azurerm_resource_group.github.name} resource group..."

# Get all resources in the resource group
ALL_RESOURCES=$(az resource list --resource-group ${data.azurerm_resource_group.github.name} --query "[].id" -o tsv)

# List of managed resource IDs (populated from the Terraform state)
MANAGED_RESOURCES="${join(" ", local.managed_resource_ids)}"

# List of resource prefixes to keep
KEEP_PREFIXES="${join(" ", local.keep_resource_prefixes)}"

# Clean up unmanaged resources
for RESOURCE_ID in $ALL_RESOURCES; do
  # Skip resources with 'Microsoft.Resources/deployments' type
  RESOURCE_TYPE=$(az resource show --ids $RESOURCE_ID --query "type" -o tsv)
  if [[ "$RESOURCE_TYPE" == "Microsoft.Resources/deployments" ]]; then
    echo "Skipping deployment resource: $RESOURCE_ID"
    continue
  fi
  
  # Skip resource groups (they're managed separately)
  if [[ "$RESOURCE_TYPE" == "Microsoft.Resources/resourceGroups" ]]; then
    echo "Skipping resource group: $RESOURCE_ID"
    continue
  fi
  
  # Check if this resource is exactly managed by Terraform
  IS_MANAGED=false
  for MANAGED_ID in $MANAGED_RESOURCES; do
    if [[ "$RESOURCE_ID" == "$MANAGED_ID" ]]; then
      IS_MANAGED=true
      echo "Keeping exactly managed resource: $RESOURCE_ID"
      break
    fi
  done
  
  # If not exactly managed, check if it's a child resource we should keep
  if [[ "$IS_MANAGED" == "false" ]]; then
    # Check prefixes
    for PREFIX in $KEEP_PREFIXES; do
      if [[ "$RESOURCE_ID" == *"$PREFIX"* ]]; then
        IS_MANAGED=true
        echo "Keeping resource by prefix match: $RESOURCE_ID"
        break
      fi
    done
  fi
  
  # If not managed and not a prefix match, delete it
  if [[ "$IS_MANAGED" == "false" ]]; then
    echo "Deleting unmanaged resource: $RESOURCE_ID"
    # Use --no-wait for faster processing of many resources
    az resource delete --ids $RESOURCE_ID --verbose --no-wait || {
      echo "Failed to delete: $RESOURCE_ID, trying again without --no-wait"
      az resource delete --ids $RESOURCE_ID --verbose
    }
  fi
done

echo "Resource cleanup completed."
EOT
  }

  depends_on = [
    azurerm_kubernetes_cluster.ai_agent,
    azurerm_container_registry.ai_agent,
    azurerm_key_vault.ai_agent
  ]
}
