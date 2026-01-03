# Baseline Performance Report

## Test Configuration

| Parameter | Value |
|-----------|-------|
| Test Date | _[To be filled after test]_ |
| Test Duration | 5 minutes (steady state) |
| Virtual Users | 10 VUs |
| Target Environment | _[ALB DNS or localhost]_ |
| Instance Type | t3.small |
| ASG Configuration | Min: 2, Desired: 2, Max: 6 |

### Endpoint Distribution
- `/items`: 70% of requests
- `/health`: 20% of requests
- `/error`: 10% of requests

---

## Test Results

### Response Time Metrics

| Endpoint | p50 | p95 | p99 | Max |
|----------|-----|-----|-----|-----|
| `/health` | _ms | _ms | _ms | _ms |
| `/items` | _ms | _ms | _ms | _ms |
| `/error` | _ms | _ms | _ms | _ms |

### Throughput

| Metric | Value |
|--------|-------|
| Total Requests | _ |
| Requests/second | _ |
| Successful Requests | _ |
| Failed Requests | _ |

### Error Rate

| Metric | Value | Threshold |
|--------|-------|-----------|
| Error Rate | _% | < 1% |
| 4xx Errors | _ | - |
| 5xx Errors | _ | - |

---

## CloudWatch Metrics During Test

### ALB Metrics
_[Insert CloudWatch screenshot of ALB Request Count and Response Time during test]_

### EC2 Metrics
_[Insert CloudWatch screenshot of EC2 CPU Utilization during test]_

### Custom Metrics
_[Insert CloudWatch screenshot of ErrorCount metric during test]_

---

## ASG Behavior

### Scaling Activity
- Did ASG scale out? _[Yes/No]_
- Instances during test: _[Count]_
- Scaling events: _[Description if any]_

> **Note**: With 10 VUs for 5 minutes, the ASG should NOT scale out. This provides a baseline for comparison with higher load tests.

---

## X-Ray Tracing

### Service Map
_[Insert X-Ray Service Map screenshot]_

### Trace Analysis
- Average trace duration: _ms
- p95 trace duration: _ms
- Identified bottlenecks: _[Description]_

---

## Analysis

### Observations
1. _[Observation 1]_
2. _[Observation 2]_
3. _[Observation 3]_

### Performance Bottlenecks
- _[Identified bottleneck 1]_
- _[Identified bottleneck 2]_

### Baseline Metrics for Comparison

| Metric | Baseline Value |
|--------|----------------|
| p50 Latency | _ms |
| p95 Latency | _ms |
| Requests/sec | _ |
| Error Rate | _% |
| CPU Utilization | _% |

---

## Recommendations

1. _[Recommendation 1]_
2. _[Recommendation 2]_
3. _[Recommendation 3]_

---

## Test Commands

```bash
# Run steady state test
k6 run tests/load_test.js

# Run with specific ALB DNS
k6 run tests/load_test.js --env ALB_DNS=your-alb-dns.amazonaws.com

# Run with HTML report
k6 run tests/load_test.js --out json=tests/results/output.json

# View results
cat tests/results/summary.json | jq
```

---

## Appendix

### k6 Raw Output
```
[Paste k6 output here]
```

### CloudWatch Query for Error Logs
```sql
fields @timestamp, @message
| filter @message like /ERROR/
| sort @timestamp desc
| limit 100
```
