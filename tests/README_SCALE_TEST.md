# Auto-Scaling Load Test

This directory contains k6 load test scripts for testing auto-scaling behavior.

## Prerequisites

Install k6:
```bash
# Windows (using Chocolatey)
choco install k6

# Or download from https://k6.io/docs/getting-started/installation/
```

## Running the Scale Test

1. Get your ALB DNS name:
```bash
aws cloudformation describe-stacks --stack-name mp-compute \
  --query 'Stacks[0].Outputs[?OutputKey==`ALBDnsName`].OutputValue' \
  --output text
```

2. Run the test:
```bash
k6 run --env ALB_DNS=your-alb-dns-here.us-east-2.elb.amazonaws.com tests/scale_test.js
```

## Test Stages

The test progresses through these stages:
1. **Warm up** (2min): Ramp to 50 users
2. **Stress** (10min): Ramp to and maintain 200 users
3. **Peak** (6min): Spike to 400 users
4. **Scale down** (6min): Reduce back to 0

Total duration: ~24 minutes

## Expected Behavior

During the test, you should observe:

### In CloudWatch Console

Navigate to CloudWatch > Alarms and Metrics:

1. **Auto Scaling > GroupDesiredCapacity**
   - Should increase from 2 to 4-6 instances during stress phase
   - May reach 8-10 during peak load
   - Should decrease back to 2 after load subsides

2. **EC2 > CPUUtilization**
   - Should approach 55% average (target threshold)
   - Individual instances may spike higher

3. **Application ELB > RequestCount**
   - Should show ~1000 requests/target before scaling

4. **Application ELB > TargetResponseTime**
   - Should stay < 1 second with proper scaling
   - May spike during transitions

### Scaling Timeline (Expected)

- **t+0**: Start with 2 instances
- **t+5min**: CPU hits 55%, triggers scale-out → 4 instances
- **t+10min**: Request count high, adds 2 more → 6 instances
- **t+15min**: Peak load, response time > 1s → 8 instances
- **t+20min**: Load decreases, starts scaling in
- **t+30min**: Back to 2 instances (minimum)

## Monitoring Commands

While test is running:

```bash
# Watch ASG activity
aws autoscaling describe-scaling-activities \
  --auto-scaling-group-name MasterProject-dev-asg \
  --max-records 20 \
  --query 'Activities[*].[StartTime,Description,StatusCode]' \
  --output table

# Watch current instance count
watch -n 10 'aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names MasterProject-dev-asg \
  --query "AutoScalingGroups[0].[MinSize,DesiredCapacity,MaxSize,Instances[].InstanceId]"'
```

## Results

Test results are saved to `tests/results/scale_test_summary.json`

Document findings in `docs/scaling_proof.md` with:
- Screenshots of CloudWatch metrics
- Scaling activity timeline
- Performance metrics at each stage
