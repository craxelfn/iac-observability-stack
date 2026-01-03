# Governance Evidence

This document provides evidence of governance controls in place for the MasterProject.

## CloudTrail Audit Trail

### Verification Commands

```bash
# Find recent CloudTrail events
aws cloudtrail lookup-events --max-results 5

# Search for specific event type
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=AuthorizeSecurityGroupIngress

# Search by username
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=Username,AttributeValue=your-username

# Search by resource
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=ResourceName,AttributeValue=mp-network
```

### CloudTrail Configuration

| Setting | Value |
|---------|-------|
| Trail Name | MasterProjectTrail |
| Multi-Region | Yes |
| Global Services | Yes |
| Log Validation | Enabled |
| S3 Bucket | mp-cloudtrail-logs-{account-id}-{region} |
| CloudWatch Logs | /aws/cloudtrail/masterproject |

### Evidence Capture

After deployment, capture evidence with:

```bash
# Export CloudTrail trail configuration
aws cloudtrail describe-trails --trail-name-list MasterProjectTrail > evidence/cloudtrail-config.json

# Export recent events
aws cloudtrail lookup-events --max-results 20 > evidence/cloudtrail-events.json
```

---

## AWS Config Compliance

### Config Rules Deployed

| Rule Name | Description | Type |
|-----------|-------------|------|
| s3-bucket-public-read-prohibited | Checks S3 buckets don't allow public read | Periodic |
| s3-bucket-public-write-prohibited | Checks S3 buckets don't allow public write | Periodic |
| restricted-ssh | Checks security groups don't allow unrestricted SSH | Change-triggered |
| cloudtrail-enabled | Checks CloudTrail is enabled | Periodic |
| ec2-instance-managed-by-systems-manager | Checks EC2 instances are managed by SSM | Change-triggered |

### Verification Commands

```bash
# List all Config rules
aws configservice describe-config-rules

# Get compliance summary
aws configservice get-compliance-summary-by-config-rule

# Get compliance details for a specific rule
aws configservice get-compliance-details-by-config-rule \
  --config-rule-name s3-bucket-public-read-prohibited

# List non-compliant resources
aws configservice get-compliance-details-by-config-rule \
  --config-rule-name restricted-ssh \
  --compliance-types NON_COMPLIANT
```

### Testing Non-Compliance

1. Create a test S3 bucket:
   ```bash
   aws s3api create-bucket --bucket test-compliance-bucket-$(date +%s)
   ```

2. Make it public (for testing only):
   ```bash
   aws s3api put-public-access-block --bucket <bucket-name> \
     --public-access-block-configuration "BlockPublicAcls=false,IgnorePublicAcls=false"
   ```

3. Wait for Config evaluation (or trigger manually)

4. Check compliance status:
   ```bash
   aws configservice get-compliance-details-by-config-rule \
     --config-rule-name s3-bucket-public-read-prohibited
   ```

5. Fix the issue and verify COMPLIANT status

6. Clean up test bucket:
   ```bash
   aws s3 rb s3://<bucket-name> --force
   ```

---

## Evidence Artifacts

After running tests, store evidence in the `evidence/` directory:

- `evidence/cloudtrail-config.json` - CloudTrail configuration
- `evidence/cloudtrail-events.json` - Sample CloudTrail events
- `evidence/config-rules.json` - AWS Config rules configuration
- `evidence/config-compliance.json` - Compliance evaluation results
