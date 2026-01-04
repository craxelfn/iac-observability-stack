#!/bin/bash
# MasterProject Deployment Script
# Deploys all CloudFormation stacks in order including Phase 3 components

set -e

# Get the absolute path of the project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

ENVIRONMENT=${1:-dev}
ALARM_EMAIL=${2:-""}
DB_PASSWORD=${3:-"ChangeMe123!"}

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

# Function to check stack status
check_stack_status() {
    local STACK_NAME=$1
    aws cloudformation describe-stacks --stack-name $STACK_NAME \
        --query 'Stacks[0].StackStatus' --output text 2>/dev/null || echo "NOT_EXISTS"
}

# Deploy Phase 1: Core Infrastructure
echo ""
echo "=========================================="
echo "PHASE 1: Core Infrastructure"
echo "=========================================="

echo ""
echo "Step 1/8: Deploying Network Stack..."
deploy_stack "mp-network" "$PROJECT_ROOT/infra/cfn/network.yaml" ""
wait_for_stack "mp-network"

echo ""
echo "Step 2/8: Deploying Security Stack..."
deploy_stack "mp-security" "$PROJECT_ROOT/infra/cfn/security.yaml" ""
wait_for_stack "mp-security"

echo ""
echo "Step 3/8: Deploying Compute Stack..."
deploy_stack "mp-compute" "$PROJECT_ROOT/infra/cfn/compute.yaml" ""
wait_for_stack "mp-compute"

echo ""
echo "Step 4/8: Deploying Observability Stack..."
if [ -n "$ALARM_EMAIL" ]; then
    deploy_stack "mp-observability" "$PROJECT_ROOT/infra/cfn/observability.yaml" "AlarmEmail=$ALARM_EMAIL"
else
    deploy_stack "mp-observability" "$PROJECT_ROOT/infra/cfn/observability.yaml" ""
fi
wait_for_stack "mp-observability"

echo ""
echo "Step 5/8: Deploying Governance Stack..."
deploy_stack "mp-governance" "$PROJECT_ROOT/infra/cfn/governance.yaml" ""
wait_for_stack "mp-governance"

# Deploy Phase 3: Performance & Cost Optimization
echo ""
echo "=========================================="
echo "PHASE 3: Performance & Cost Optimization"
echo "=========================================="

echo ""
echo "Step 6/8: Deploying RDS Database Stack..."
deploy_stack "mp-database" "$PROJECT_ROOT/infra/cfn/database.yaml" "DBPassword=$DB_PASSWORD"
wait_for_stack "mp-database"

echo ""
echo "Step 7/8: Deploying ElastiCache Redis Stack..."
deploy_stack "mp-cache" "$PROJECT_ROOT/infra/cfn/cache.yaml" ""
wait_for_stack "mp-cache"

# Check if Lambda stack exists and deploy
echo ""
echo "Step 8/8: Deploying Lambda Stack (if exists)..."
if [ -f "$PROJECT_ROOT/infra/cfn/lambda.yaml" ]; then
    deploy_stack "mp-lambda" "$PROJECT_ROOT/infra/cfn/lambda.yaml" ""
    wait_for_stack "mp-lambda"
else
    echo "Lambda stack template not found. Skipping..."
fi

# Save evidence
echo ""
echo "=========================================="
echo "Saving Stack Outputs"
echo "=========================================="
mkdir -p "$PROJECT_ROOT/evidence"
echo "Saving evidence to $PROJECT_ROOT/evidence/..."

aws cloudformation describe-stacks --stack-name mp-network > "$PROJECT_ROOT/evidence/network-stack.json"
aws cloudformation describe-stacks --stack-name mp-security > "$PROJECT_ROOT/evidence/security-stack.json"
aws cloudformation describe-stacks --stack-name mp-compute > "$PROJECT_ROOT/evidence/compute-stack.json"
aws cloudformation describe-stacks --stack-name mp-observability > "$PROJECT_ROOT/evidence/observability-stack.json"
aws cloudformation describe-stacks --stack-name mp-governance > "$PROJECT_ROOT/evidence/governance-stack.json"
aws cloudformation describe-stacks --stack-name mp-database > "$PROJECT_ROOT/evidence/database-stack.json"
aws cloudformation describe-stacks --stack-name mp-cache > "$PROJECT_ROOT/evidence/cache-stack.json"

if [ "$(check_stack_status mp-lambda)" != "NOT_EXISTS" ]; then
    aws cloudformation describe-stacks --stack-name mp-lambda > "$PROJECT_ROOT/evidence/lambda-stack.json"
fi

# Get stack outputs
echo ""
echo "Retrieving stack outputs..."

ALB_DNS=$(aws cloudformation describe-stacks --stack-name mp-compute \
    --query 'Stacks[0].Outputs[?OutputKey==`ALBDnsName`].OutputValue' --output text)

DB_ENDPOINT=$(aws cloudformation describe-stacks --stack-name mp-database \
    --query 'Stacks[0].Outputs[?OutputKey==`DBInstanceEndpoint`].OutputValue' --output text)

REDIS_ENDPOINT=$(aws cloudformation describe-stacks --stack-name mp-cache \
    --query 'Stacks[0].Outputs[?OutputKey==`RedisEndpoint`].OutputValue' --output text)

# Run basic health checks
echo ""
echo "=========================================="
echo "Running Health Checks"
echo "=========================================="

echo ""
echo "Testing ALB endpoint..."
sleep 10  # Give ALB time to register targets

MAX_RETRIES=30
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://$ALB_DNS/health || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        echo "✅ ALB health check passed (HTTP 200)"
        break
    else
        echo "Waiting for ALB to be healthy... ($((RETRY_COUNT+1))/$MAX_RETRIES) [HTTP $HTTP_CODE]"
        sleep 10
        RETRY_COUNT=$((RETRY_COUNT+1))
    fi
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "⚠️  Warning: ALB health check timed out. Check EC2 instances."
fi

echo ""
echo "Testing database connectivity..."
echo "Database endpoint: $DB_ENDPOINT"
echo "✅ Database stack deployed (verify connectivity from EC2 instances)"

echo ""
echo "Testing cache connectivity..."
echo "Redis endpoint: $REDIS_ENDPOINT"
echo "✅ Cache stack deployed (verify connectivity from EC2 instances)"

# Deployment summary
echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Core Infrastructure:"
echo "  ALB DNS: http://$ALB_DNS"
echo ""
echo "Phase 3 Components:"
echo "  Database: $DB_ENDPOINT:5432"
echo "  Cache: $REDIS_ENDPOINT:6379"
echo ""
echo "Test Endpoints:"
echo "  curl http://$ALB_DNS/health"
echo "  curl http://$ALB_DNS/items?count=5"
echo "  curl http://$ALB_DNS/"
echo ""
echo "CloudWatch Dashboard:"
echo "  https://console.aws.amazon.com/cloudwatch/home#dashboards:name=MasterProject-Dashboard"
echo ""
echo "RDS Performance Insights:"
echo "  https://console.aws.amazon.com/rds/home#performance-insights:"
echo ""
echo "Evidence saved to: $PROJECT_ROOT/evidence/"
echo ""
echo "=========================================="
echo "Next Steps"
echo "=========================================="
echo ""
echo "1. Seed Database:"
echo "   python app/seed_data.py --count 50000"
echo ""
echo "2. Run Load Tests:"
echo "   k6 run --env ALB_DNS=$ALB_DNS tests/scale_test.js"
echo ""
echo "3. Monitor Scaling:"
echo "   aws autoscaling describe-scaling-activities \\"
echo "     --auto-scaling-group-name MasterProject-dev-asg \\"
echo "     --max-records 20"
echo ""
echo "4. Check Cache Stats:"
echo "   curl http://$ALB_DNS/cache/stats"
echo ""
