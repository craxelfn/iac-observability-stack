# Release Runbook

This runbook documents the release process for MasterProject.

## Overview

The CI/CD pipeline automatically deploys code changes pushed to the `main` branch:

```
GitHub Push → CodePipeline → CodeBuild (test) → CodeDeploy (deploy) → EC2 Instances
```

---

## Pre-Release Checklist

- [ ] All unit tests passing locally
- [ ] Code reviewed and approved
- [ ] Feature tested in development environment
- [ ] No critical alerts in CloudWatch

---

## Automated Deployment Flow

### 1. Trigger Pipeline

```bash
# Push code changes
git add .
git commit -m "Release: <description>"
git push origin main
```

### 2. Monitor Pipeline

1. Open AWS Console → CodePipeline
2. Select `MasterProject-dev-pipeline`
3. Watch stages progress: Source → Build → Deploy

### 3. Pipeline Stages

| Stage | Actions | Duration |
|-------|---------|----------|
| Source | Fetch code from GitHub | ~30s |
| Build | Install, lint, test, package | ~3-5 min |
| Deploy | Deploy to EC2 via CodeDeploy | ~5-10 min |

---

## Deployment Verification

After successful deployment:

```bash
# Get ALB DNS
ALB_DNS=$(aws cloudformation describe-stacks --stack-name mp-compute \
    --query 'Stacks[0].Outputs[?OutputKey==`ALBDnsName`].OutputValue' --output text)

# Test health endpoint
curl http://$ALB_DNS/health

# Test items endpoint
curl http://$ALB_DNS/items?count=3

# Check application version
curl http://$ALB_DNS/
```

---

## Rollback Procedures

### Automatic Rollback

CodeDeploy automatically rolls back if:
- Deployment fails at any hook
- Health check fails in ValidateService hook
- Deployment explicitly stopped

### Manual Rollback

**Option 1: Redeploy Previous Revision**

```bash
# List recent deployments
aws deploy list-deployments \
  --application-name MasterProject-dev \
  --deployment-group-name MasterProject-dev-dg

# Get deployment details
aws deploy get-deployment --deployment-id <deployment-id>

# Redeploy previous successful revision
aws deploy create-deployment \
  --application-name MasterProject-dev \
  --deployment-group-name MasterProject-dev-dg \
  --revision <previous-revision>
```

**Option 2: Stop Current Deployment**

```bash
aws deploy stop-deployment --deployment-id <deployment-id>
```

**Option 3: Git Revert**

```bash
git revert HEAD
git push origin main
# Wait for pipeline to deploy the revert
```

---

## Monitoring During Deployment

### CloudWatch Metrics

Monitor these metrics during deployment:

| Metric | Namespace | Threshold |
|--------|-----------|-----------|
| HealthyHostCount | AWS/ApplicationELB | > 0 |
| UnHealthyHostCount | AWS/ApplicationELB | < desired |
| HTTPCode_Target_5XX_Count | AWS/ApplicationELB | < 10/min |
| RequestCount | AWS/ApplicationELB | Normal range |

### CloudWatch Dashboard

```
https://console.aws.amazon.com/cloudwatch/home#dashboards:name=MasterProject-Dashboard
```

### Application Logs

```bash
# View application logs
aws logs tail /masterproject/app --follow

# View recent errors
aws logs filter-log-events \
  --log-group-name /masterproject/app \
  --filter-pattern "ERROR"
```

---

## Troubleshooting

### Deployment Stuck

1. Check CodeDeploy agent status on EC2:
   ```bash
   aws ssm send-command \
     --document-name "AWS-RunShellScript" \
     --parameters 'commands=["systemctl status codedeploy-agent"]' \
     --targets "Key=tag:Project,Values=MasterProject"
   ```

2. Check deployment logs:
   ```bash
   aws deploy get-deployment --deployment-id <id>
   ```

### Application Not Starting

1. Check application logs:
   ```bash
   aws logs tail /masterproject/app -n 100
   ```

2. SSH via SSM and check:
   ```bash
   aws ssm start-session --target <instance-id>
   # Then on instance:
   sudo systemctl status masterproject
   sudo journalctl -u masterproject -n 50
   ```

### Health Check Failing

1. Verify application is listening:
   ```bash
   curl http://localhost:8080/health
   ```

2. Check target group health:
   ```bash
   aws elbv2 describe-target-health \
     --target-group-arn <target-group-arn>
   ```

---

## Emergency Procedures

### Complete Service Outage

1. Check ALB and Target Group health
2. Check EC2 instance status
3. Check application logs for errors
4. If needed, rollback to last known good version

### Security Incident

1. Isolate affected resources
2. Check CloudTrail for suspicious activity
3. Follow incident response procedure
4. Contact security team

---

## Contact Information

| Role | Contact |
|------|---------|
| On-Call Engineer | [Configure] |
| Security Team | [Configure] |
| AWS Support | [Configure] |
