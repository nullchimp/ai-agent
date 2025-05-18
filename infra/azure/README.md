# Azure Infrastructure Setup

This directory contains Terraform configurations for setting up the Azure infrastructure required for the AI Agent application.

## Prerequisites

- Azure CLI installed and configured
- Terraform installed (v1.0.0+)
- Access to an Azure subscription

## Resource Import

When working with existing Azure resources, the `import_resources.sh` script helps to import them into Terraform state.

### Running in CI/CD Pipelines

When running in CI/CD pipelines, use the CI_MODE flag to prevent password prompts:

```bash
CI_MODE=true ENVIRONMENT=dev ./import_resources.sh
```

This will use placeholder values for sensitive variables during the import operation, which prevents the script from prompting for these values interactively.

### Environment Variables

The script accepts the following environment variables:

- `ENVIRONMENT`: The deployment environment (dev, staging, prod). Defaults to `dev`.
- `SUBSCRIPTION_ID`: Azure subscription ID. Defaults to the current Azure CLI subscription.
- `RESOURCE_GROUP`: Azure resource group name. Defaults to "GitHub".
- `CI_MODE`: Set to "true" to run in CI/CD mode with placeholder values. Defaults to "false".
- `TENANT_ID`: Azure tenant ID. Required in CI mode.
- `OBJECT_ID`: Service principal object ID. Required in CI mode.

## Manual Deployment

For manual deployment:

1. Set the required environment variables in terraform.tfvars or via environment variables
2. Run `terraform init` to initialize Terraform
3. Run `./import_resources.sh` to import existing resources
4. Run `terraform plan` to review changes
5. Run `terraform apply` to apply changes

## Resource Naming Conventions

- Key Vault: `kv-ai-agent-{environment}`
- Container Registry: `craiagentreg{environment}`
- AKS Cluster: `aks-ai-agent-{environment}`
