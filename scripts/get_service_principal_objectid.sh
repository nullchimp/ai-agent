#!/bin/zsh

# This script gets the object ID of a service principal by its display name or app ID
# Usage: ./get_service_principal_objectid.sh <service-principal-name-or-id>

# Check if required parameter is provided
if [ $# -lt 1 ]; then
    echo "Error: Missing required parameter."
    echo "Usage: $0 <service-principal-name-or-id>"
    echo ""
    echo "Provide either the display name or app ID of your service principal."
    echo "You can list all service principals with: az ad sp list --all --query \"[].{name:displayName, appId:appId}\" -o table"
    exit 1
fi

SP_IDENTIFIER="ai-agent-github"

# First try finding by display name
echo "Searching for service principal with display name '$SP_IDENTIFIER'..."
OBJECT_ID=$(az ad sp list --display-name "$SP_IDENTIFIER" --query "[0].id" -o tsv)

# If not found by display name, try as an app ID
if [ -z "$OBJECT_ID" ]; then
    echo "Not found by display name, trying as app ID..."
    OBJECT_ID=$(az ad sp show --id "$SP_IDENTIFIER" --query "id" -o tsv 2>/dev/null)
fi

if [ -z "$OBJECT_ID" ]; then
    echo "No service principal found with the provided identifier."
    echo "List all service principals with: az ad sp list --all --query \"[].{name:displayName, appId:appId}\" -o table"
    exit 1
else
    echo "Service Principal Object ID: $OBJECT_ID"
    echo ""
    echo "You can use this Object ID in your Terraform variables or Azure Key Vault access policies."
    echo "For Terraform, add it to your variables file as: object_id = \"$OBJECT_ID\""
fi