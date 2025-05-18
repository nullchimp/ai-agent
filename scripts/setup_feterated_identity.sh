#!/bin/zsh

# Check if AZURE_CLIENT_ID was provided as a parameter
if [ -z "$1" ]; then
    echo "Error: AZURE_CLIENT_ID is required as a parameter."
    echo "Usage: $0 <AZURE_CLIENT_ID>"
    exit 1
fi

AZURE_CLIENT_ID=$1
CREDENTIAL_NAME="GitHubActionsFederatedCredential"

# Check if the federated credential already exists
echo "Checking if federated credential '$CREDENTIAL_NAME' already exists..."
EXISTING_CREDENTIAL=$(az ad app federated-credential list --id $AZURE_CLIENT_ID --query "[?name=='$CREDENTIAL_NAME']" -o json)

if [ "$(echo $EXISTING_CREDENTIAL | jq 'length')" -gt "0" ]; then
    echo "Federated credential '$CREDENTIAL_NAME' already exists. Skipping creation."
else
    echo "Creating federated credential '$CREDENTIAL_NAME'..."
    az ad app federated-credential create --id $AZURE_CLIENT_ID \
      --parameters '{
        "name": "GitHubActionsFederatedCredential",
        "issuer": "https://token.actions.githubusercontent.com",
        "subject": "repo:nullchimp/ai-agent:ref:refs/heads/RAG",
        "audiences": [
          "api://AzureADTokenExchange"
        ]
      }'
    
    if [ $? -eq 0 ]; then
        echo "Federated credential created successfully."
    else
        echo "Failed to create federated credential."
        exit 1
    fi
fi