# MasterProject Deployment & Cleanup Guide

## Overview

This guide covers automated deployment and cleanup of the complete MasterProject infrastructure, including:
- **Phase 1**: Core infrastructure (Network, Security, Compute, Observability, Governance)
- **Phase 3**: Performance & Cost optimization (RDS Database, ElastiCache Redis, Lambda)

## Prerequisites

### Required Tools
- AWS CLI configured with appropriate credentials
- Bash shell (Linux, macOS, or WSL on Windows)
- Git (for CI/CD integration)
- Python 3.11 (for database seeding)
- k6 (for load testing) - optional

### AWS Permissions
Your AWS user/role needs permissions for:
- CloudFormation (full access)
- EC2, VPC, ALB, Auto Scaling
- RDS, ElastiCache
- Lambda, S3
- IAM (for role creation)
- CloudWatch, X-Ray
- CodePipeline, CodeBuild, CodeDeploy (for CI/CD)

---

## Deployment

### Quick Start

```bash
# Basic deployment (dev environment)
./scripts/deploy.sh

# With custom parameters
./scripts/deploy.sh <environment> <alarm-email> <db-password>

# Example
./scripts/deploy.sh dev your-email@example.com MySecurePass123!
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `environment` | `dev` | Environment name (dev/staging/prod) |
| `alarm-email` | (none) | Email for CloudWatch alarm notifications |
| `db-password` | `ChangeMe123!` | RDS database master password |

### Deployment Steps

The script automatically deploys stacks in the correct dependency order:

1. **Network Stack** (`mp-network`)
   - VPC, Subnets, Internet Gateway, NAT Gateways

2. **Security Stack** (`mp-security`)
   - Security Groups for ALB, EC2, RDS, Redis

3. **Compute Stack** (`mp-compute`)
   - Application Load Balancer
   - Auto Scaling Group with EC2 instances
   - **NEW**: Auto-scaling policies (CPU, Request Count, Response Time)

4. **Observability Stack** (`mp-observability`)
   - CloudWatch Dashboard, Log Groups
   - Metric Filters and Alarms

5. **Governance Stack** (`mp-governance`)
   - CloudTrail, Config, GuardDuty

6. **Database Stack** (`mp-database`) - Phase 3
   - RDS PostgreSQL 15.5
   - Performance Insights enabled
   - Automated backups

7. **Cache Stack** (`mp-cache`) - Phase 3
   - ElastiCache Redis 7.1
   - Encryption at-rest and in-transit

8. **Lambda Stack** (`mp-lambda`) - Phase 3 (if exists)
   - Lambda functions for async processing
   - S3 bucket for exports

### Health Checks

The deployment script automatically:
- Waits for stacks to complete
- Tests ALB health endpoint (retries for 5 minutes)
- Verifies database endpoint is available
- Verifies cache endpoint is available
- Saves stack outputs to `evidence/` directory

### Post-Deployment Steps

After deployment completes, run these commands:

```bash
# 1. Get ALB DNS (saved in evidence)
ALB_DNS=$(aws cloudformation describe-stacks --stack-name mp-compute \
  --query 'Stacks[0].Outputs[?OutputKey==`ALBDnsName`].OutputValue' \
  --output text)

# 2. Seed database with sample data
python app/seed_data.py --count 50000

# 3. Test endpoints
curl http://$ALB_DNS/health
curl http://$ALB_DNS/items?count=10
curl http://$ALB_DNS/

# 4. Run load test to trigger auto-scaling
k6 run --env ALB_DNS=$ALB_DNS tests/scale_test.js

# 5. Monitor scaling activity
watch -n 10 'aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names MasterProject-dev-asg \
  --query "AutoScalingGroups[0].[DesiredCapacity,Instances[].InstanceId]"'
```

### Deployment Outputs

Stack outputs are saved to:
```
evidence/
├── network-stack.json
├── security-stack.json
├── compute-stack.json
├── observability-stack.json
├── governance-stack.json
├── database-stack.json
├── cache-stack.json
└── lambda-stack.json (if deployed)
```

### Monitoring Deployment

```bash
# Watch CloudFormation events for a stack
aws cloudformation describe-stack-events \
  --stack-name mp-database \
  --query 'StackEvents[?ResourceStatus!=`UPDATE_COMPLETE`].[Timestamp,ResourceStatus,ResourceType,ResourceStatusReason]' \
  --output table

# Check all stack statuses
for stack in mp-network mp-security mp-compute mp-observability mp-governance mp-database mp-cache; do
  echo -n "$stack: "
  aws cloudformation describe-stacks --stack-name $stack \
    --query 'Stacks[0].StackStatus' --output text 2>/dev/null || echo "NOT_EXISTS"
done
```

---

## Cleanup

### Quick Start

```bash
# Interactive cleanup (will prompt for confirmation)
./scripts/cleanup.sh
```

### What Gets Deleted

The cleanup script removes all resources in reverse dependency order:

**Phase 3 Components:**
1. Lambda Stack (`mp-lambda`)
2. ElastiCache Redis Stack (`mp-cache`)
3. RDS Database Stack (`mp-database`) - **creates final snapshot first**

**Phase 1 Core Infrastructure:**
4. CI/CD Stack (`mp-cicd`) - if exists
5. Governance Stack (`mp-governance`)
6. Observability Stack (`mp-observability`)
7. Compute Stack (`mp-compute`) - **terminates all EC2 instances**
8. Security Stack (`mp-security`)
9. Network Stack (`mp-network`)

**Additional Cleanup:**
10. Evidence directory (`evidence/`)
11. Project S3 buckets (with confirmation)

### Manual Cleanup

Some resources are retained and require manual cleanup:

```bash
# Delete RDS snapshots (if you don't need them)
aws rds describe-db-snapshots \
  --query 'DBSnapshots[?starts_with(DBSnapshotIdentifier,`masterproject`)].DBSnapshotIdentifier' \
  --output table

aws rds delete-db-snapshot --db-snapshot-identifier <snapshot-id>

# Delete CloudWatch log groups
aws logs describe-log-groups \
  --log-group-name-prefix /masterproject \
  --query 'logGroups[].logGroupName' \
  --output table

aws logs delete-log-group --log-group-name <log-group-name>

# Delete CodePipeline artifact buckets
aws s3 ls | grep mp-.*-pipeline-artifacts
aws s3 rb s3://bucket-name --force
```

### Cleanup Verification

```bash
# Verify all stacks are deleted
aws cloudformation list-stacks \
  --stack-status-filter DELETE_COMPLETE \
  --query 'StackSummaries[?starts_with(StackName,`mp-`)].StackName' \
  --output table

# Check for any remaining resources
aws cloudformation list-stacks \
  --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE \
  --query 'StackSummaries[?starts_with(StackName,`mp-`)].StackName'
```

---

## Troubleshooting

### Deployment Failures

**Stack rollback:**
```bash
# Get rollback reason
aws cloudformation describe-stack-events \
  --stack-name mp-database \
  --query 'StackEvents[?ResourceStatus==`CREATE_FAILED`].[ResourceType,ResourceStatusReason]' \
  --output table

# Delete failed stack and retry
aws cloudformation delete-stack --stack-name mp-database
aws cloudformation wait stack-delete-complete --stack-name mp-database
./scripts/deploy.sh
```

**ALB health check fails:**
```bash
# Check target group health
aws elbv2 describe-target-health \
  --target-group-arn $(aws cloudformation describe-stacks --stack-name mp-compute \
    --query 'Stacks[0].Outputs[?OutputKey==`TargetGroupArn`].OutputValue' --output text)

# Check CodeDeploy status
aws deploy list-deployments --application-name MasterProject-dev-app
aws deploy get-deployment --deployment-id <deployment-id>

# SSH to instance (if needed)
aws ssm start-session --target <instance-id>
sudo journalctl -u masterproject -n 100
```

**Database connection issues:**
```bash
# Verify security group rules
aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=MasterProject-dev-rds-sg" \
  --query 'SecurityGroups[].IpPermissions'

# Test from EC2
aws ssm start-session --target <instance-id>
nc -zv <db-endpoint> 5432
psql -h <db-endpoint> -U dbadmin -d masterprojectdb
```

### Cleanup Failures

**Stack in DELETE_FAILED state:**
```bash
# Find problematic resources
aws cloudformation describe-stack-resources \
  --stack-name mp-database \
  --query 'StackResources[?ResourceStatus==`DELETE_FAILED`]'

# Manually delete resource, then retry
aws cloudformation delete-stack --stack-name mp-database
```

**RDS deletion protection:**
```bash
# Disable deletion protection first
aws rds modify-db-instance \
  --db-instance-identifier MasterProject-dev-db \
  --no-deletion-protection

# Then delete stack
aws cloudformation delete-stack --stack-name mp-database
```

---

## CI/CD Integration

The deployment scripts are designed to be run manually, but can be integrated into CI/CD:

```yaml
# Example: GitHub Actions workflow
name: Deploy Infrastructure
on:
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to deploy'
        required: true
        default: 'dev'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-2
      
      - name: Deploy infrastructure
        run: |
          ./scripts/deploy.sh ${{ github.event.inputs.environment }} \
            ${{ secrets.ALARM_EMAIL }} \
            ${{ secrets.DB_PASSWORD }}
```

---

## Best Practices

1. **Always use version control**: Commit infrastructure changes before deploying
2. **Test in dev first**: Validate changes in dev before prod deployment
3. **Tag releases**: Use git tags to track deployed versions
4. **Monitor deployments**: Watch CloudWatch during and after deployment
5. **Keep backups**: Don't delete RDS snapshots immediately
6. **Document changes**: Update this guide when adding new stacks
7. **Rotate passwords**: Change database password after initial deployment
8. **Review costs**: Check AWS Cost Explorer after deployment

---

## Cost Estimates

Approximate monthly costs for dev environment:

| Service | Configuration | Monthly Cost |
|---------|--------------|--------------|
| EC2 (t3.small x 2) | 2 instances, 20GB each | ~$30 |
| RDS (db.t3.small) | 20GB gp3, no Multi-AZ | ~$25 |
| ElastiCache (cache.t3.micro) | Single node | ~$12 |
| ALB | Low traffic | ~$20 |
| NAT Gateway | 2 AZs | ~$65 |
| Data transfer | Minimal | ~$5 |
| **Total** | | **~$157/month** |

**Cost optimization tips:**
- Use Spot instances for dev (70% savings)
- Implement auto start/stop for non-prod
- Enable S3 lifecycle policies
- Review unused resources monthly

---

## Support

For issues or questions:
1. Check CloudFormation events for specific error messages
2. Review CloudWatch logs: `/masterproject/app` and `/aws/lambda/*`
3. Check RDS Performance Insights for database issues
4. Review this troubleshooting guide
