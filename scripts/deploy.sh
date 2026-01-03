#!/bin/bash
# MasterProject Deployment Script
# Deploys all CloudFormation stacks in order

set -e

# Get the absolute path of the project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

ENVIRONMENT=${1:-dev}
ALARM_EMAIL=${2:-""}

echo "=========================================="
echo "MasterProject Infrastructure Deployment"
echo "Environment: $ENVIRONMENT"
echo "Project Root: $PROJECT_ROOT"
echo "=========================================="

# Function to deploy a stack
deploy_stack() {
    local STACK_NAME=$1
    local TEMPLATE_FILE=$2
    local EXTRA_PARAMS=$3

    echo ""
    echo "Deploying $STACK_NAME..."
    
    aws cloudformation deploy \
        --template-file "$TEMPLATE_FILE" \
        --stack-name "$STACK_NAME" \
        --capabilities CAPABILITY_NAMED_IAM \
        --parameter-overrides Environment=$ENVIRONMENT $EXTRA_PARAMS \
        --no-fail-on-empty-changeset
    
    echo "$STACK_NAME deployed successfully!"
}

# Function to wait for stack completion
wait_for_stack() {
    local STACK_NAME=$1
    echo "Waiting for $STACK_NAME to complete..."
    aws cloudformation wait stack-create-complete --stack-name $STACK_NAME 2>/dev/null || \
    aws cloudformation wait stack-update-complete --stack-name $STACK_NAME 2>/dev/null || true
}

# Deploy stacks in order
echo ""
echo "Step 1/5: Deploying Network Stack..."
deploy_stack "mp-network" "$PROJECT_ROOT/infra/cfn/network.yaml" ""
wait_for_stack "mp-network"

echo ""
echo "Step 2/5: Deploying Security Stack..."
deploy_stack "mp-security" "$PROJECT_ROOT/infra/cfn/security.yaml" ""
wait_for_stack "mp-security"

echo ""
echo "Step 3/5: Deploying Compute Stack..."
deploy_stack "mp-compute" "$PROJECT_ROOT/infra/cfn/compute.yaml" ""
wait_for_stack "mp-compute"

echo ""
echo "Step 4/5: Deploying Observability Stack..."
if [ -n "$ALARM_EMAIL" ]; then
    deploy_stack "mp-observability" "$PROJECT_ROOT/infra/cfn/observability.yaml" "AlarmEmail=$ALARM_EMAIL"
else
    deploy_stack "mp-observability" "$PROJECT_ROOT/infra/cfn/observability.yaml" ""
fi
wait_for_stack "mp-observability"

echo ""
echo "Step 5/5: Deploying Governance Stack..."
deploy_stack "mp-governance" "$PROJECT_ROOT/infra/cfn/governance.yaml" ""
wait_for_stack "mp-governance"

# Save evidence
echo ""
echo "Saving stack outputs to evidence directory..."
mkdir -p "$PROJECT_ROOT/evidence"
aws cloudformation describe-stacks --stack-name mp-network > "$PROJECT_ROOT/evidence/network-stack.json"
aws cloudformation describe-stacks --stack-name mp-security > "$PROJECT_ROOT/evidence/security-stack.json"
aws cloudformation describe-stacks --stack-name mp-compute > "$PROJECT_ROOT/evidence/compute-stack.json"
aws cloudformation describe-stacks --stack-name mp-observability > "$PROJECT_ROOT/evidence/observability-stack.json"
aws cloudformation describe-stacks --stack-name mp-governance > "$PROJECT_ROOT/evidence/governance-stack.json"

# Get ALB DNS
ALB_DNS=$(aws cloudformation describe-stacks --stack-name mp-compute \
    --query 'Stacks[0].Outputs[?OutputKey==`ALBDnsName`].OutputValue' --output text)

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "ALB DNS: http://$ALB_DNS"
echo ""
echo "Test endpoints:"
echo "  curl http://$ALB_DNS/health"
echo "  curl http://$ALB_DNS/items?count=5"
echo "  curl http://$ALB_DNS/error"
echo ""
echo "CloudWatch Dashboard:"
echo "  https://console.aws.amazon.com/cloudwatch/home#dashboards:name=MasterProject-Dashboard"
echo ""
echo "=========================================="
echo "CI/CD Stack (Optional - requires GitHub setup)"
echo "=========================================="
echo ""
echo "To deploy the CI/CD pipeline, you need:"
echo "  1. A CodeStar connection to GitHub (create in AWS Console)"
echo "  2. Your GitHub repository details"
echo ""
echo "Then run:"
echo "  aws cloudformation deploy \\"
echo "    --template-file infra/cfn/cicd.yaml \\"
echo "    --stack-name mp-cicd \\"
echo "    --capabilities CAPABILITY_NAMED_IAM \\"
echo "    --parameter-overrides \\"
echo "      GitHubOwner=YOUR_GITHUB_USERNAME \\"
echo "      GitHubRepo=YOUR_REPO_NAME \\"
echo "      CodeStarConnectionArn=YOUR_CODESTAR_CONNECTION_ARN"
echo ""

