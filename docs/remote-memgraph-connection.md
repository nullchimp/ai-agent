# Connecting to Remote Memgraph Database

This document explains how to connect to the Memgraph database deployed on Azure.

## DNS Name Configuration

After deployment, the Memgraph service is accessible via a stable DNS name in the format:

```
memgraph-aiagent-<environment>.<azure-region>.cloudapp.azure.com
```

For example:
```
memgraph-aiagent-dev.germanywestcentral.cloudapp.azure.com
```

This DNS name is automatically configured during deployment and will not change unless you redeploy to a different region or rename your resources.

## Connection Method

### 1. Using the Connection Helper Script

The easiest way to configure your connection is to use the provided helper script:

```zsh
# Get connection information for the dev environment
python scripts/get_memgraph_connection.py

# Update your .env file automatically
python scripts/get_memgraph_connection.py --update-env

# Specify a different environment
python scripts/get_memgraph_connection.py prod --update-env
```

### 2. Manual Configuration

If you prefer to configure your connection manually, update your `.env` file with the following variables:

```
MEMGRAPH_URI=memgraph-aiagent-dev.germanywestcentral.cloudapp.azure.com
MEMGRAPH_PORT=7687
MEMGRAPH_USERNAME=your-memgraph-username
MEMGRAPH_PASSWORD=your-memgraph-password
```

## Connecting in Python Code

```python
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env

from core.rag.dbhandler.memgraph import MemGraphClient
import os

# Connect to remote Memgraph database
db = MemGraphClient(
    host=os.environ.get("MEMGRAPH_URI"),
    port=int(os.environ.get("MEMGRAPH_PORT", 7687)),
    username=os.environ.get("MEMGRAPH_USERNAME"),
    password=os.environ.get("MEMGRAPH_PASSWORD"),
)

# Use the connection
with db:
    # Run a simple query
    db._execute("RETURN 'Connected to Memgraph!' AS status")
    print("Connection successful!")
```

You can also run the example script to test your connection:

```zsh
python examples/az-memgraph-connection.py
```

## Web Interfaces

The Memgraph database also provides web interfaces that you can access using the same DNS name:

- **MemGraph Lab UI**: `http://memgraph-aiagent-dev.germanywestcentral.cloudapp.azure.com:3000`
  - A web-based interface for interacting with the database
  - Use your MEMGRAPH_USERNAME and MEMGRAPH_PASSWORD to log in

- **HTTP API**: `http://memgraph-aiagent-dev.germanywestcentral.cloudapp.azure.com:7444`
  - RESTful API for programmatic access to the database

## Troubleshooting

If you encounter connection issues:

1. Verify that your AKS cluster and Memgraph pod are running:
   ```zsh
   az aks get-credentials --resource-group GitHub --name aks-ai-agent-dev
   kubectl get pods -l app=memgraph
   ```

2. Check if the DNS resolution works:
   ```zsh
   nslookup memgraph-aiagent-dev.germanywestcentral.cloudapp.azure.com
   ```

3. Verify network connectivity:
   ```zsh
   telnet memgraph-aiagent-dev.germanywestcentral.cloudapp.azure.com 7687
   ```

4. Check Memgraph logs:
   ```zsh
   kubectl logs -l app=memgraph
   ```

5. Ensure the LoadBalancer service is properly configured:
   ```zsh
   kubectl describe service memgraph
   ```

## Security Considerations

The DNS name makes your Memgraph database accessible over the public internet. To enhance security:

1. Use strong passwords for your Memgraph credentials
2. Consider setting up a VPN or Azure Private Link
3. Implement IP-based restrictions in your Azure Network Security Group
4. Enable TLS encryption when connecting to the database
