#!/bin/bash
# This script force restarts the Memgraph pod after deployment
# to ensure all authentication settings are properly applied

set -eo pipefail

echo "Forcing restart of Memgraph pod..."
# Scale to 0 pods to ensure clean shutdown
kubectl scale deployment memgraph --replicas=0
echo "Scaled down to 0 replicas, waiting for pods to terminate..."
kubectl wait --for=delete --timeout=60s pod -l app=memgraph || true

echo "Scaling back to 1 replica..."
kubectl scale deployment memgraph --replicas=1
echo "Waiting for pod to be ready..."
kubectl wait --for=condition=ready --timeout=120s pod -l app=memgraph

echo "Memgraph pod has been force restarted"
