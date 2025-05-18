#!/bin/zsh

# This script assigns Contributor role to a service principal for a specified subscription
# Usage: ./setup_service_principle_permissions.sh <service-principal-id> <subscription-id>

# Check if required parameters are provided
if [ $# -lt 2 ]; then
    echo "Error: Missing required parameters."
    echo "Usage: $0 <service-principal-id> <subscription-id>"
    echo ""
    echo "To find your service principal ID, use one of these commands:"
    echo "  az ad sp list --display-name \"YOUR_SP_NAME\" --query \"[].appId\" -o tsv"
    echo "  az ad sp list --all --query \"[].{name:displayName, id:appId}\" -o table"
    echo ""
    echo "To find your subscription ID:"
    echo "  az account show --query id -o tsv"
    exit 1
fi

SERVICE_PRINCIPAL_ID=$1
SUBSCRIPTION_ID=$2
ROLE="Contributor"

echo "Assigning '$ROLE' role to service principal ID '$SERVICE_PRINCIPAL_ID' for subscription '$SUBSCRIPTION_ID'..."

az role assignment create \
  --assignee "$SERVICE_PRINCIPAL_ID" \
  --role "$ROLE" \
  --scope "/subscriptions/$SUBSCRIPTION_ID"

if [ $? -eq 0 ]; then
    echo "Role assignment created successfully."
else
    echo "Failed to create role assignment."
    exit 1
fi