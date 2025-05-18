#!/bin/zsh

# Set up Azure credentials for GitHub Actions
# This script creates a service principal with Contributor access to the GitHub resource group

# Login to Azure
echo "Logging in to Azure..."
az login

# Create service principal
echo "Creating service principal for GitHub Actions..."
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
SERVICE_PRINCIPAL=$(az ad sp create-for-rbac \
  --name "ai-agent-github" \
  --role contributor \
  --scopes /subscriptions/$SUBSCRIPTION_ID/resourceGroups/GitHub \
  --sdk-auth)

# Output the service principal credentials
echo "Service principal created. Add the following secret to your GitHub repository as AZURE_CREDENTIALS:"
echo $SERVICE_PRINCIPAL
