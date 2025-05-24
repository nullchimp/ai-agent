# Memgraph Azure Deployment

This deployment setup provides a **cost-optimized** Memgraph database on Azure with:

- ✅ **Minimal Cost**: Uses Standard_B1s VM (cheapest option)
- ✅ **Persistent Storage**: Standard SSD for data persistence
- ✅ **Authentication Enforced**: Memgraph-mage with credentials
- ✅ **External Access**: LoadBalancer for public connectivity
- ✅ **Full Automation**: GitHub Actions & local deployment script

## Quick Start

### 1. Setup Environment

Copy the template and configure your credentials:

```bash
cp .env.template .env
# Edit .env with your Azure subscription details and Memgraph credentials
```

### 2. Deploy Locally (Recommended for testing)

```bash
# Ensure you're logged into Azure CLI
az login

# Run the deployment script
./scripts/deploy-azure.sh
```

### 3. Deploy via GitHub Actions

1. Set these repository secrets:
   - `AZURE_SUBSCRIPTION_ID`
   - `AZURE_TENANT_ID` 
   - `AZURE_CLIENT_ID`
   - `MEMGRAPH_USERNAME`
   - `MEMGRAPH_PASSWORD`

2. Push to `dev` branch or manually trigger the workflow

## Cost Optimization

This deployment is optimized for **minimal Azure costs**:

- **VM Size**: Standard_B1s (1 vCPU, 1GB RAM) - ~$12/month
- **Storage**: Standard SSD LRS - ~$2/month for 11GB total
- **Network**: Standard LoadBalancer - ~$18/month
- **Total**: ~$32/month for a production-ready setup

## Access Information

After deployment, you'll get external access via:

- **Bolt Protocol**: `EXTERNAL_IP:7687` (for applications)
- **HTTP API**: `EXTERNAL_IP:7444` (for REST API)
- **Memgraph Lab UI**: `EXTERNAL_IP:3000` (for visual interface)

## Authentication

The deployment enforces authentication using the credentials you provide:
- Username: Set in `MEMGRAPH_USERNAME`
- Password: Set in `MEMGRAPH_PASSWORD`

## File Structure

```
infra/
├── azure/
│   └── main.tf              # Terraform AKS cluster configuration
└── k8s/
    ├── storageclass.yaml    # Cost-optimized storage class
    └── memgraph.yaml        # Memgraph deployment manifest
```

## Troubleshooting

### Check Deployment Status
```bash
kubectl get pods -l app=memgraph
kubectl get service memgraph
kubectl logs -l app=memgraph
```

### Connect to Memgraph
```bash
# Get external IP
kubectl get service memgraph -o jsonpath='{.status.loadBalancer.ingress[0].ip}'

# Test connection (requires pymgclient)
python -c "
import mgclient
conn = mgclient.connect(host='EXTERNAL_IP', port=7687, username='your_username', password='your_password')
cursor = conn.cursor()
cursor.execute('RETURN 1 as test')
print(cursor.fetchall())
"
```

### Cost Monitoring
- Monitor costs in Azure Cost Management
- Consider using Azure Advisor for optimization recommendations
- Scale down/up the cluster as needed: `az aks scale --node-count 1`

## Cleanup

To avoid ongoing charges:

```bash
# Delete the deployment
terraform destroy -chdir=infra/azure \
  -var="subscription_id=$AZURE_SUBSCRIPTION_ID" \
  -var="location=$LOCATION" \
  -var="environment=$ENVIRONMENT" \
  -var="resource_group=$RESOURCE_GROUP"
```
