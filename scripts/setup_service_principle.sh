#!/bin/zsh

# Set up Azure credentials for GitHub Actions
# This script creates a service principal with Contributor access to the GitHub resource group
# If the service principal already exists, it will retrieve it instead of creating a new one

# Login to Azure
echo "Logging in to Azure..."
az login

# Service principal name
SP_NAME="ai-agent-github"
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
RESOURCE_GROUP="GitHub"

# Check if service principal already exists
echo "Checking if service principal '$SP_NAME' already exists..."
SP_ID=$(az ad sp list --display-name "$SP_NAME" --query "[0].appId" -o tsv)

if [ -n "$SP_ID" ]; then
    echo "Service principal '$SP_NAME' already exists."
    
    # Get existing service principal information without resetting credentials
    # Create JSON output in the format expected by GitHub Actions
    CLIENT_ID=$SP_ID
    TENANT_ID=$(az account show --query tenantId -o tsv)
    SUBSCRIPTION_ID=$(az account show --query id -o tsv)
    
    echo "Using existing service principal."
    echo "Important: To use this service principal, ensure your GitHub repository has"
    echo "the correct credentials already configured as AZURE_CREDENTIALS secret."
    echo "If you need to reset credentials, you can do so manually with:"
    echo "az ad sp credential reset --id $SP_ID --sdk-auth"
    
    # Display service principal information (without secret)
    echo "Service Principal Information:"
    echo "- Client ID: $CLIENT_ID"
    echo "- Tenant ID: $TENANT_ID"
    echo "- Subscription ID: $SUBSCRIPTION_ID"
    
    # Set SERVICE_PRINCIPAL to empty to avoid displaying sensitive info
    SERVICE_PRINCIPAL='{}'
else
    # Create service principal
    echo "Creating service principal for GitHub Actions..."
    SERVICE_PRINCIPAL=$(az ad sp create-for-rbac \
      --name "$SP_NAME" \
      --role contributor \
      --scopes /subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP \
      --sdk-auth)
    
    echo "Service principal created. Add the following secret to your GitHub repository as AZURE_CREDENTIALS:"
fi

echo $SERVICE_PRINCIPAL
