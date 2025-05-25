# Troubleshooting Memgraph Connections

This guide provides troubleshooting steps for common issues when connecting to Memgraph.

## Connection Issues

If you're experiencing issues connecting to the Memgraph database deployed on Azure, follow these steps:

### 1. Check if the Memgraph service is running

```bash
kubectl get pods -l app=memgraph
```

The output should show a pod in the `Running` state. If not, check the pod status:

```bash
kubectl describe pod -l app=memgraph
```

### 2. Check the Memgraph logs for errors

```bash
kubectl logs -l app=memgraph
```

Common errors include:
- VM memory map count issues
- Authentication failures
- Networking problems

### 3. Verify credential secret exists

```bash
kubectl get secret memgraph-credentials
```

### 4. Run the diagnostic script

We provide a comprehensive diagnostic script that checks for common issues and attempts to fix them:

```bash
./scripts/memgraph_diagnostics.sh
```

This script will:
- Check pod status
- Verify service configuration
- Validate credentials
- Look for common errors in logs
- Apply fixes when possible
- Test connectivity

### 5. Manual fix for credential issues

If you've changed the Memgraph credentials in GitHub secrets but the pod doesn't reflect the changes:

1. Update the Kubernetes secret:
   ```bash
   kubectl create secret generic memgraph-credentials \
     --from-literal=username=YOUR_USERNAME \
     --from-literal=password=YOUR_PASSWORD \
     --dry-run=client -o yaml | kubectl apply -f -
   ```

2. Force the pod to restart with the new credentials:
   ```bash
   kubectl patch deployment memgraph -p \
     "{\"spec\":{\"template\":{\"metadata\":{\"annotations\":{\"restart-at\":\"$(date +%s)\"}}}}}"
   ```

3. Wait for the new pod to be ready:
   ```bash
   kubectl wait --for=condition=ready pod -l app=memgraph --timeout=5m
   ```

### 6. Testing connectivity

You can test connectivity using the provided test script:

```bash
# Make sure your .env file contains the correct credentials
python examples/10-azure-memgraph-test.py
```

## Common Errors and Solutions

### VM Max Map Count Error

If you see an error like "Max virtual memory areas vm.max_map_count 65530 is too low", this is fixed in the latest deployment configuration with an init container.

### Authentication Errors

If you're getting authentication errors:
1. Verify the credentials in your `.env` file match those in the Kubernetes secret
2. Ensure the GitHub secrets have been properly updated
3. Check if the deployment was updated after changing the credentials

### Connection Timeouts

If connections are timing out:
1. Verify the Azure Network Security Group allows traffic on port 7687
2. Check if the service has a valid external IP address
3. Ensure your client can reach the Azure VM (no firewall blocking access)

## Need Further Help?

If the above steps don't resolve your issue, please:
1. Gather the output from the diagnostic script
2. Collect all relevant error messages
3. Open an issue providing these details
