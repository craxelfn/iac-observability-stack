#!/bin/bash
# MasterProject Cleanup Script
# Deletes all CloudFormation stacks in reverse order

set -e

echo "=========================================="
echo "MasterProject Infrastructure Cleanup"
echo "=========================================="
echo ""
echo "WARNING: This will delete ALL resources!"
echo "Press Ctrl+C to cancel, or Enter to continue..."
read

# Function to delete a stack
delete_stack() {
    local STACK_NAME=$1
    echo "Deleting $STACK_NAME..."
    
    aws cloudformation delete-stack --stack-name $STACK_NAME
    
    echo "Waiting for $STACK_NAME deletion..."
    aws cloudformation wait stack-delete-complete --stack-name $STACK_NAME
    
    echo "$STACK_NAME deleted successfully!"
}

# Delete stacks in reverse order
echo ""
echo "Step 1/6: Deleting CI/CD Stack (if exists)..."
delete_stack "mp-cicd" || true

echo ""
echo "Step 2/6: Deleting Governance Stack..."
delete_stack "mp-governance" || true

echo ""
echo "Step 3/6: Deleting Observability Stack..."
delete_stack "mp-observability" || true

echo ""
echo "Step 4/6: Deleting Compute Stack..."
delete_stack "mp-compute" || true

echo ""
echo "Step 5/6: Deleting Security Stack..."
delete_stack "mp-security" || true

echo ""
echo "Step 6/6: Deleting Network Stack..."
delete_stack "mp-network" || true

echo ""
echo "=========================================="
echo "Cleanup Complete!"
echo "=========================================="

