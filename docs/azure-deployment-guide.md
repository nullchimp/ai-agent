# Azure Deployment Guide for AI Agent

This guide provides a complete, step-by-step process for deploying the AI Agent's Memgraph database to Microsoft Azure using Kubernetes (AKS), with secure secret management and automated CI/CD.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Infrastructure Overview](#infrastructure-overview)
3. [Setup Process](#setup-process)
   - [Setting up Azure Credentials](#setting-up-azure-credentials)
   - [GitHub Repository Configuration](#github-repository-configuration)
   - [Infrastructure Deployment](#infrastructure-deployment)
4. [Understanding the Configuration Files](#understanding-the-configuration-files)
   - [Terraform Configuration](#terraform-configuration)
   - [Kubernetes Configuration](#kubernetes-configuration)
   - [GitHub Actions Workflow](#github-actions-workflow)
5. [Accessing Memgraph](#accessing-memgraph)
6. [Troubleshooting](#troubleshooting)
7. [Cleanup](#cleanup)

## Prerequisites

Before starting, ensure you have:

- Azure account with access to the "GitHub" resource group in Germany West Central
- GitHub repository set up and accessible
- Local development tools:
  - Azure CLI installed
  - Terraform installed (optional, as it runs in GitHub Actions)
  - kubectl installed (optional, for direct access to AKS)
  - Python 3.9+ installed

## Infrastructure Overview

The deployment creates these resources in your existing "GitHub" resource group:

- **Azure Kubernetes Service (AKS)** - Container orchestration platform
- **Azure Key Vault** - Secure secret management
- **Azure Container Registry** - Docker image storage
- **Persistent Volumes** - For Memgraph data, logs, and configuration
- **Service Principal** - For secure GitHub Actions integration with Azure

## Setup Process

### Setting up Azure Credentials

1. Run the provided setup script:

   ```bash
   cd /Users/nullchimp/Projects/ai-agent
   ./scripts/setup_azure.sh
   ```

   This script will:
   - Log you into Azure with `az login`
   - Create a service principal with Contributor access to the "GitHub" resource group

2. Copy the output JSON which looks similar to:

   ```json
   {
     "clientId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
     "clientSecret": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
     "subscriptionId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
     "tenantId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
     "activeDirectoryEndpointUrl": "https://login.microsoftonline.com",
     "resourceManagerEndpointUrl": "https://management.azure.com/",
     "activeDirectoryGraphResourceId": "https://graph.windows.net/",
     "sqlManagementEndpointUrl": "https://management.core.windows.net:8443/",
     "galleryEndpointUrl": "https://gallery.azure.com/",
     "managementEndpointUrl": "https://management.core.windows.net/"
   }
   ```

   Save this for the next step.

### GitHub Repository Configuration

1. In your GitHub repository, navigate to Settings → Secrets and variables → Actions.

2. Add the following secrets:

   - **AZURE_CREDENTIALS**: Paste the entire JSON output from the setup script
   - **MEMGRAPH_USERNAME**: Choose a username for the Memgraph database
   - **MEMGRAPH_PASSWORD**: Choose a secure password for the Memgraph database

### Infrastructure Deployment

Deploy the infrastructure by either:

1. **Automatic Deployment** - Push to the main branch

   ```bash
   git add .
   git commit -m "Add Azure deployment configuration"
   git push origin main
   ```

2. **Manual Deployment** - Trigger the workflow manually
   - Go to GitHub repository → Actions tab
   - Select "Deploy to Azure" workflow
   - Click "Run workflow" and select the main branch

3. **Monitor Deployment**:
   - Follow the progress in the GitHub Actions tab
   - The workflow will:
     - Set up Terraform
     - Deploy infrastructure to Azure
     - Configure Kubernetes
     - Deploy Memgraph to AKS
     - Verify the deployment
     - Run tests to validate everything is working

## Understanding the Configuration Files

### Terraform Configuration

Located at `/infra/azure/main.tf` and `/infra/azure/variables.tf`:

- **main.tf** - Defines the Azure resources:
  - References existing "GitHub" resource group
  - Creates Key Vault for secrets
  - Creates Container Registry for images
  - Provisions AKS cluster
  - Sets up proper access policies

- **variables.tf** - Defines variables:
  - `environment` - Deployment environment (default: "dev")
  - `memgraph_username` - Memgraph database username
  - `memgraph_password` - Memgraph database password

### Kubernetes Configuration

Located at `/infra/k8s/memgraph.yaml`:

- Defines Kubernetes resources:
  - ConfigMap for Memgraph configuration
  - Deployment for the Memgraph container
  - PersistentVolumeClaims for data persistence
  - Service for exposing Memgraph ports

The Kubernetes config ensures:
- Memgraph container is properly configured
- Credentials are securely injected from Kubernetes secrets
- Data is persisted across pod restarts
- Health checks monitor the container
- The service is exposed via LoadBalancer

### GitHub Actions Workflow

Located at `/.github/workflows/deploy-azure.yml`:

- Defines the CI/CD pipeline that:
  - Sets up Python environment
  - Logs into Azure
  - Initializes and applies Terraform
  - Gets AKS credentials
  - Creates Kubernetes secrets
  - Deploys Memgraph to AKS
  - Verifies the deployment
  - Runs tests

### Setup Script

Located at `/scripts/setup_azure.sh`:

This bash script automates:
- Azure CLI authentication
- Service principal creation with appropriate permissions
- Output of credentials for GitHub Actions

## Accessing Memgraph

After successful deployment:

1. Get the external IP of the Memgraph service:

   ```bash
   az aks get-credentials --resource-group GitHub --name aks-ai-agent-dev
   kubectl get service memgraph
   ```

2. Note the EXTERNAL-IP from the output

3. Access Memgraph using these endpoints:
   - Bolt protocol: `EXTERNAL-IP:7687` (for direct database connections)
   - HTTP API: `EXTERNAL-IP:7444` (for REST API access)
   - MemGraph Lab UI: `EXTERNAL-IP:3000` (for visual database management)

4. Use the credentials (MEMGRAPH_USERNAME and MEMGRAPH_PASSWORD) to authenticate

## Troubleshooting

### Check pod status

```bash
kubectl get pods
kubectl describe pod <pod-name>
kubectl logs <pod-name>
```

### Check service status

```bash
kubectl get services
kubectl describe service memgraph
```

### Common issues

1. **Persistent volumes not provisioning**:
   - Check storage class availability in your Azure region
   - Check the persistent volume claims status

2. **Memgraph not starting**:
   - Check logs for errors
   - Verify secrets were created correctly

3. **Cannot access external IP**:
   - Verify service type is LoadBalancer
   - Check if Azure has assigned an external IP
   - Verify network security groups allow traffic

## Cleanup

To remove the deployed resources:

1. Delete the Kubernetes resources:

   ```bash
   kubectl delete -f infra/k8s/memgraph.yaml
   ```

2. Destroy the Terraform-managed infrastructure:

   ```bash
   cd infra/azure
   terraform destroy -var="environment=dev" \
     -var="memgraph_username=<username>" \
     -var="memgraph_password=<password>"
   ```

3. Delete the service principal:

   ```bash
   az ad sp delete --id <client-id-from-service-principal>
   ```

---

This deployment approach ensures:
- Infrastructure as code with Terraform
- Secure secret management with Azure Key Vault
- Containerized deployment with Kubernetes
- CI/CD automation with GitHub Actions
- Persistent storage for your Memgraph data
