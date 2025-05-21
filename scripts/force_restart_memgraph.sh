#!/bin/bash
# This script force restarts the Memgraph pod after deployment
# to ensure all authentication settings are properly applied

set -e

echo "Forcing restart of Memgraph pod..."

# Get all pod names matching our app
POD_NAMES=$(kubectl get pods -l app=memgraph -o name)
if [ -n "$POD_NAMES" ]; then
    echo "Found pods: $POD_NAMES"
    
    # Delete the pods directly (faster and more reliable than scaling down)
    echo "Deleting pods directly..."
    kubectl delete pods -l app=memgraph --grace-period=10 --force --timeout=30s || true
    
    # Wait a moment to ensure deletion has started
    sleep 5
    
    # Check if pods are still terminating
    TERMINATING_PODS=$(kubectl get pods -l app=memgraph --no-headers 2>/dev/null | grep -c "Terminating" || echo "0")
    if [ "$TERMINATING_PODS" -gt 0 ]; then
        echo "Some pods still terminating, forcing immediate deletion..."
        kubectl delete pods -l app=memgraph --grace-period=0 --force --timeout=10s || true
    fi
else
    echo "No Memgraph pods found, proceeding with deployment"
fi

# Scale to ensure we have exactly one replica
echo "Setting deployment to 1 replica..."
kubectl scale deployment memgraph --replicas=1

# Wait for the new pod to be ready with a more generous timeout
echo "Waiting for new pod to be ready (this may take up to 3 minutes)..."
kubectl wait --for=condition=ready --timeout=180s pod -l app=memgraph || true

# Verify pod is running
POD_STATUS=$(kubectl get pods -l app=memgraph -o jsonpath='{.items[0].status.phase}' 2>/dev/null || echo "Unknown")
echo "Memgraph pod status: $POD_STATUS"

if [ "$POD_STATUS" = "Running" ]; then
    echo "✅ Memgraph pod successfully restarted and running"
else
    echo "⚠️ Memgraph pod may not be fully ready yet, but deployment will continue"
    kubectl get pods -l app=memgraph
fi
