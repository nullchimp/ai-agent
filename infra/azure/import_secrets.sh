#!/bin/bash
# Specialized script to import existing Key Vault secrets into Terraform state
# Usage: ./import_secrets.sh [environment]

set -e

# Check if environment variable is set, default to dev
ENVIRONMENT=${1:-dev}
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
RESOURCE_GROUP="GitHub"
KV_NAME="kv-ai-agent-$ENVIRONMENT"

terraform init

# Import Key Vault Secrets with their full URIs
if az keyvault show --name "$KV_NAME" --resource-group "$RESOURCE_GROUP" &>/dev/null; then
  # For memgraph-username, get the secret ID including version
  if az keyvault secret show --name "memgraph-username" --vault-name "$KV_NAME" &>/dev/null; then
    SECRET_URI=$(az keyvault secret show --name "memgraph-username" --vault-name "$KV_NAME" --query id -o tsv)
    terraform import azurerm_key_vault_secret.memgraph_username "$SECRET_URI"
  fi
  
  # For memgraph-password, get the secret ID including version
  if az keyvault secret show --name "memgraph-password" --vault-name "$KV_NAME" &>/dev/null; then
    SECRET_URI=$(az keyvault secret show --name "memgraph-password" --vault-name "$KV_NAME" --query id -o tsv)
    terraform import azurerm_key_vault_secret.memgraph_password "$SECRET_URI"
  fi
else
  exit 1
fi
