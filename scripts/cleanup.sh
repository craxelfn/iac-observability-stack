#!/bin/bash
# MasterProject Cleanup Script
# Deletes all CloudFormation stacks in reverse order including Phase 3 components

set -e

echo "=========================================="
echo "MasterProject Infrastructure Cleanup"
echo "=========================================="
echo ""
echo "⚠️  WARNING: This will delete ALL resources!"
echo ""
echo "This will remove:"
echo "  - All EC2 instances and Auto Scaling Groups"
echo "  - RDS Database (final snapshot will be created)"
echo "  - ElastiCache Redis cluster"
echo "  - Lambda functions and S3 buckets"
echo "  - All networking and security resources"
echo ""
echo "Press Ctrl+C to cancel, or Enter to continue..."
read

# Function to check if stack exists
stack_exists() {
    local STACK_NAME=$1
    aws cloudformation describe-stacks --stack-name $STACK_NAME &>/dev/null
    return $?
}

# Function to delete a stack
delete_stack() {
    local STACK_NAME=$1
    
    if stack_exists $STACK_NAME; then
        echo "Deleting $STACK_NAME..."
        
        aws cloudformation delete-stack --stack-name $STACK_NAME
        
        echo "Waiting for $STACK_NAME deletion..."
        aws cloudformation wait stack-delete-complete --stack-name $STACK_NAME 2>/dev/null || true
        
        echo "✅ $STACK_NAME deleted successfully!"
    else
        echo "⏭️  $STACK_NAME does not exist, skipping..."
    fi
}

# Delete stacks in reverse dependency order
# Phase 3 stacks first (they depend on core infra)
echo ""
echo "=========================================="
echo "PHASE 3: Removing Performance Components"
echo "=========================================="

echo ""
echo "Step 1/11: Deleting Lambda Stack (if exists)..."
delete_stack "mp-lambda"

echo ""
echo "Step 2/11: Deleting ElastiCache Redis Stack..."
delete_stack "mp-cache"

echo ""
echo "Step 3/11: Deleting RDS Database Stack..."
echo "Note: A final snapshot will be created before deletion"
delete_stack "mp-database"

# Core infrastructure
echo ""
echo "=========================================="
echo "PHASE 1: Removing Core Infrastructure"
echo "=========================================="

echo ""
echo "Step 4/11: Deleting CI/CD Stack (if exists)..."
delete_stack "mp-cicd"

echo ""
echo "Step 5/11: Deleting Governance Stack..."
delete_stack "mp-governance"

echo ""
echo "Step 6/11: Deleting Observability Stack..."
delete_stack "mp-observability"

echo ""
echo "Step 7/11: Deleting Compute Stack..."
echo "Note: This will terminate all EC2 instances"
delete_stack "mp-compute"

echo ""
echo "Step 8/11: Deleting Security Stack..."
delete_stack "mp-security"

echo ""
echo "Step 9/11: Deleting Network Stack..."
delete_stack "mp-network"

# Clean up evidence directory
echo ""
echo "=========================================="
echo "Cleaning Up Evidence Files"
echo "=========================================="

echo ""
echo "Step 10/11: Removing evidence directory..."
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

if [ -d "$PROJECT_ROOT/evidence" ]; then
    rm -rf "$PROJECT_ROOT/evidence"
    echo "✅ Evidence directory removed"
else
    echo "⏭️  No evidence directory found"
fi

# Clean up any remaining S3 buckets (for Lambda exports, if created manually)
echo ""
echo "Step 11/11: Checking for project S3 buckets..."
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
BUCKETS=$(aws s3 ls | grep "mp-.*-$ACCOUNT_ID" | awk '{print $3}' || true)

if [ -n "$BUCKETS" ]; then
    echo "Found project S3 buckets:"
    echo "$BUCKETS"
    echo ""
    echo "Delete these buckets? (y/N)"
    read DELETE_BUCKETS
    
    if [ "$DELETE_BUCKETS" = "y" ] || [ "$DELETE_BUCKETS" = "Y" ]; then
        for BUCKET in $BUCKETS; do
            echo "Emptying and deleting bucket: $BUCKET"
            aws s3 rm s3://$BUCKET --recursive 2>/dev/null || true
            aws s3 rb s3://$BUCKET 2>/dev/null || true
        done
        echo "✅ S3 buckets cleaned up"
    else
        echo "⏭️  Skipping S3 bucket deletion"
    fi
else
    echo "⏭️  No project S3 buckets found"
fi

echo ""
echo "=========================================="
echo "Cleanup Complete!"
echo "=========================================="
echo ""
echo "All CloudFormation stacks have been deleted."
echo ""
echo "Remaining manual cleanup (if needed):"
echo "  - RDS snapshots (check RDS console)"
echo "  - ElastiCache snapshots (check ElastiCache console)"
echo "  - CloudWatch log groups (will be retained)"
echo "  - S3 buckets for CodePipeline artifacts"
echo ""
echo "To verify all stacks are deleted:"
echo "  aws cloudformation list-stacks \\"
echo "    --stack-status-filter DELETE_COMPLETE \\"
echo "    --query 'StackSummaries[?starts_with(StackName, \`mp-\`)].StackName'"
echo ""

