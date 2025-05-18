#!/bin/bash
# filepath: /Users/nullchimp/Projects/ai-agent/infra/azure/import_resources.sh
# This script imports existing Azure resources into Terraform state

set -e

# Check if environment variable is set, default to dev
ENVIRONMENT=${ENVIRONMENT:-dev}
SUBSCRIPTION_ID=${SUBSCRIPTION_ID:-$(az account show --query id -o tsv)}
RESOURCE_GROUP="GitHub"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Checking for existing resources to import into Terraform state...${NC}"
echo -e "${YELLOW}Using environment: $ENVIRONMENT${NC}"
echo -e "${YELLOW}Resource group: $RESOURCE_GROUP${NC}"

# Initialize Terraform (required for importing)
terraform init

# Import Key Vault if it exists
KV_NAME="kv-ai-agent-$ENVIRONMENT"
if az keyvault show --name "$KV_NAME" --resource-group "$RESOURCE_GROUP" &>/dev/null; then
  echo -e "${YELLOW}Importing Key Vault: $KV_NAME${NC}"
  terraform import azurerm_key_vault.ai_agent "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.KeyVault/vaults/$KV_NAME" || \
    echo -e "${RED}Failed to import Key Vault. It may already be in state or doesn't exist.${NC}"
else
  echo -e "${GREEN}Key Vault $KV_NAME doesn't exist yet. Will be created by Terraform.${NC}"
fi

# Import Container Registry if it exists
ACR_NAME="craiagentreg$ENVIRONMENT"
if az acr show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" &>/dev/null; then
  echo -e "${YELLOW}Importing Container Registry: $ACR_NAME${NC}"
  terraform import azurerm_container_registry.ai_agent "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.ContainerRegistry/registries/$ACR_NAME" || \
    echo -e "${RED}Failed to import Container Registry. It may already be in state or doesn't exist.${NC}"
else
  echo -e "${GREEN}Container Registry $ACR_NAME doesn't exist yet. Will be created by Terraform.${NC}"
fi

# Import AKS Cluster if it exists
AKS_NAME="aks-ai-agent-$ENVIRONMENT"
if az aks show --name "$AKS_NAME" --resource-group "$RESOURCE_GROUP" &>/dev/null; then
  echo -e "${YELLOW}Importing AKS Cluster: $AKS_NAME${NC}"
  terraform import azurerm_kubernetes_cluster.ai_agent "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.ContainerService/managedClusters/$AKS_NAME" || \
    echo -e "${RED}Failed to import AKS Cluster. It may already be in state or doesn't exist.${NC}"
else
  echo -e "${GREEN}AKS Cluster $AKS_NAME doesn't exist yet. Will be created by Terraform.${NC}"
fi

# Import Key Vault Secrets if they exist
if az keyvault show --name "$KV_NAME" --resource-group "$RESOURCE_GROUP" &>/dev/null; then
  # Check for memgraph-username secret
  if az keyvault secret show --name "memgraph-username" --vault-name "$KV_NAME" &>/dev/null; then
    echo -e "${YELLOW}Importing Key Vault Secret: memgraph-username${NC}"
    terraform import azurerm_key_vault_secret.memgraph_username "$KV_NAME/memgraph-username" || \
      echo -e "${RED}Failed to import memgraph-username secret.${NC}"
  fi
  
  # Check for memgraph-password secret
  if az keyvault secret show --name "memgraph-password" --vault-name "$KV_NAME" &>/dev/null; then
    echo -e "${YELLOW}Importing Key Vault Secret: memgraph-password${NC}"
    terraform import azurerm_key_vault_secret.memgraph_password "$KV_NAME/memgraph-password" || \
      echo -e "${RED}Failed to import memgraph-password secret.${NC}"
  fi
fi

# Try to import Key Vault Access Policy for AKS if both resources exist
if az keyvault show --name "$KV_NAME" --resource-group "$RESOURCE_GROUP" &>/dev/null && \
   az aks show --name "$AKS_NAME" --resource-group "$RESOURCE_GROUP" &>/dev/null; then
  
  # Get AKS principal ID
  AKS_PRINCIPAL_ID=$(az aks show --name "$AKS_NAME" --resource-group "$RESOURCE_GROUP" --query "identity.principalId" -o tsv)
  
  if [ -n "$AKS_PRINCIPAL_ID" ]; then
    echo -e "${YELLOW}Importing Key Vault Access Policy for AKS${NC}"
    terraform import azurerm_key_vault_access_policy.aks "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.KeyVault/vaults/$KV_NAME/objectId/$AKS_PRINCIPAL_ID" || \
      echo -e "${RED}Failed to import Key Vault Access Policy. It may already be in state or doesn't exist.${NC}"
  fi
fi

echo -e "${GREEN}Resource import completed. Now you can run 'terraform plan' and 'terraform apply'${NC}"

# Run terraform plan to show changes (optional)
if [ "${RUN_PLAN:-false}" == "true" ]; then
  echo -e "${YELLOW}Running terraform plan to show pending changes...${NC}"
  terraform plan
fi
