#!/bin/bash
# filepath: /Users/nullchimp/Projects/ai-agent/infra/azure/import_resources.sh
# This script imports existing Azure resources into Terraform state
#
# Usage in CI workflows:
#   CI_MODE=true ENVIRONMENT=dev ./import_resources.sh
#
# This will prevent the script from prompting for variable values during import

set -e

# Check if environment variable is set, default to dev
ENVIRONMENT=${ENVIRONMENT:-dev}
SUBSCRIPTION_ID=${SUBSCRIPTION_ID:-$(az account show --query id -o tsv)}
RESOURCE_GROUP="GitHub"
CI_MODE=${CI_MODE:-false}
TENANT_ID=${TENANT_ID:-$(az account show --query tenantId -o tsv)}
OBJECT_ID=${OBJECT_ID:-$(az ad signed-in-user show --query id -o tsv 2>/dev/null || echo "00000000-0000-0000-0000-000000000000")}

# Remove color output and echos for CI environments

# Create a temporary terraform.tfvars file for imports with placeholders
# when running in CI mode, we don't need real values for imports
if [ "$CI_MODE" = "true" ]; then
  cat > terraform.tfvars.tmp << EOF
environment = "$ENVIRONMENT"
subscription_id = "$SUBSCRIPTION_ID"
tenant_id = "$TENANT_ID"
object_id = "$OBJECT_ID"
memgraph_username = "placeholder-for-import"
memgraph_password = "placeholder-for-import"
EOF
  
  # Use the temporary file
  mv terraform.tfvars.tmp terraform.tfvars
fi

# Initialize Terraform (required for importing)
terraform init

# Import Key Vault if it exists
KV_NAME="kv-ai-agent-$ENVIRONMENT"
if az keyvault show --name "$KV_NAME" --resource-group "$RESOURCE_GROUP" &>/dev/null; then
  terraform import azurerm_key_vault.ai_agent "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.KeyVault/vaults/$KV_NAME" || true
fi

# Import Container Registry if it exists
ACR_NAME="craiagentreg$ENVIRONMENT"
if az acr show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" &>/dev/null; then
  terraform import azurerm_container_registry.ai_agent "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.ContainerRegistry/registries/$ACR_NAME" || true
fi

# Import AKS Cluster if it exists
AKS_NAME="aks-ai-agent-$ENVIRONMENT"
if az aks show --name "$AKS_NAME" --resource-group "$RESOURCE_GROUP" &>/dev/null; then
  terraform import azurerm_kubernetes_cluster.ai_agent "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.ContainerService/managedClusters/$AKS_NAME" || true
fi

# Import Key Vault Secrets if they exist
if az keyvault show --name "$KV_NAME" --resource-group "$RESOURCE_GROUP" &>/dev/null; then
  # Check for memgraph-username secret - get specific version
  if az keyvault secret show --name "memgraph-username" --vault-name "$KV_NAME" &>/dev/null; then
    SECRET_ID=$(az keyvault secret show --name "memgraph-username" --vault-name "$KV_NAME" --query id -o tsv)
    terraform import azurerm_key_vault_secret.memgraph_username "$SECRET_ID" || true
  fi
  
  # Check for memgraph-password secret - get specific version
  if az keyvault secret show --name "memgraph-password" --vault-name "$KV_NAME" &>/dev/null; then
    SECRET_ID=$(az keyvault secret show --name "memgraph-password" --vault-name "$KV_NAME" --query id -o tsv)
    terraform import azurerm_key_vault_secret.memgraph_password "$SECRET_ID" || true
  fi
fi

# Import AKS Node Pool if it exists
if az aks show --name "$AKS_NAME" --resource-group "$RESOURCE_GROUP" &>/dev/null; then
  # Check if the node pool named "agentpool" exists
  if az aks nodepool show --name "agentpool" --cluster-name "$AKS_NAME" --resource-group "$RESOURCE_GROUP" &>/dev/null; then
    terraform import azurerm_kubernetes_cluster_node_pool.ai_agent_pool "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.ContainerService/managedClusters/$AKS_NAME/agentPools/agentpool" || true
  fi
fi

# Try to import Key Vault Access Policy for AKS if both resources exist
if az keyvault show --name "$KV_NAME" --resource-group "$RESOURCE_GROUP" &>/dev/null && \
   az aks show --name "$AKS_NAME" --resource-group "$RESOURCE_GROUP" &>/dev/null; then
  
  # Get AKS principal ID
  AKS_PRINCIPAL_ID=$(az aks show --name "$AKS_NAME" --resource-group "$RESOURCE_GROUP" --query "identity.principalId" -o tsv)
  
  if [ -n "$AKS_PRINCIPAL_ID" ]; then
    # Check if the access policy actually exists before trying to import it
    if az keyvault show --name "$KV_NAME" --resource-group "$RESOURCE_GROUP" --query "properties.accessPolicies[?objectId=='$AKS_PRINCIPAL_ID']" -o tsv | grep -q .; then
      terraform import azurerm_key_vault_access_policy.aks "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.KeyVault/vaults/$KV_NAME/objectId/$AKS_PRINCIPAL_ID" || true
    fi
  fi
fi

# Clean up the temporary tfvars file if in CI mode
if [ "$CI_MODE" = "true" ]; then
  rm -f terraform.tfvars
fi

echo "Resource import completed!"