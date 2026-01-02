# MasterProject - AWS Observability Infrastructure

A fully observable, CloudFormation-managed infrastructure with a simple API demonstrating comprehensive monitoring and tracing capabilities.

## 📁 Project Structure

```
proj/
├── infra/cfn/                    # CloudFormation templates
│   ├── network.yaml              # VPC, subnets, NAT Gateway
│   ├── security.yaml             # Security groups
│   ├── compute.yaml              # ALB, ASG, Launch Template
│   └── observability.yaml        # CloudWatch logs, alarms, dashboard
├── app/                          # FastAPI application
│   ├── main.py                   # API endpoints
│   ├── config.py                 # Configuration
│   └── requirements.txt          # Python dependencies
├── tests/                        # Load testing
│   ├── load_test.js              # k6 load test script
│   └── results/                  # Test results
├── docs/                         # Documentation
│   └── BASELINE_PERFORMANCE_REPORT.md
└── evidence/                     # Deployment outputs
```

## 🚀 Quick Start

### Prerequisites
- AWS CLI configured with appropriate credentials
- Python 3.11+
- k6 for load testing

### Deploy Infrastructure

```bash
# 1. Deploy network stack
aws cloudformation deploy --template-file infra/cfn/network.yaml \
  --stack-name mp-network --capabilities CAPABILITY_NAMED_IAM

# 2. Deploy security groups
aws cloudformation deploy --template-file infra/cfn/security.yaml \
  --stack-name mp-security --capabilities CAPABILITY_NAMED_IAM

# 3. Deploy compute infrastructure
aws cloudformation deploy --template-file infra/cfn/compute.yaml \
  --stack-name mp-compute --capabilities CAPABILITY_NAMED_IAM

# 4. Deploy observability stack
aws cloudformation deploy --template-file infra/cfn/observability.yaml \
  --stack-name mp-observability --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides AlarmEmail=your-email@example.com
```

### Validate Stacks

```bash
# Save stack outputs as evidence
aws cloudformation describe-stacks --stack-name mp-network > evidence/network-stack.json
aws cloudformation describe-stacks --stack-name mp-security > evidence/security-stack.json
aws cloudformation describe-stacks --stack-name mp-compute > evidence/compute-stack.json
aws cloudformation describe-stacks --stack-name mp-observability > evidence/observability-stack.json
```

### Test API Endpoints

```bash
# Get ALB DNS
ALB_DNS=$(aws cloudformation describe-stacks --stack-name mp-compute \
  --query 'Stacks[0].Outputs[?OutputKey==`ALBDnsName`].OutputValue' --output text)

# Test endpoints
curl http://$ALB_DNS/health
curl http://$ALB_DNS/items?count=5
curl http://$ALB_DNS/error
```

### Run Load Tests

```bash
# Install k6: https://k6.io/docs/getting-started/installation/

# Run load test
k6 run tests/load_test.js --env ALB_DNS=$ALB_DNS
```

## 🏗️ Architecture

### Network Layer
- **VPC**: 10.0.0.0/16
- **Public Subnets**: 10.0.1.0/24, 10.0.2.0/24 (multi-AZ)
- **Private Subnets**: 10.0.11.0/24, 10.0.12.0/24 (multi-AZ)
- **NAT Gateway**: Single NAT in public subnet for private subnet internet access

### Compute Layer
- **ALB**: Internet-facing, HTTP listener on port 80
- **ASG**: Min 2, Max 6, Desired 2 instances
- **EC2**: t3.small, Amazon Linux 2023, in private subnets

### Observability
- **CloudWatch Logs**: Application and system logs (7-day retention)
- **CloudWatch Metrics**: Custom metrics from application logs
- **CloudWatch Alarms**: Error rate, latency, 5xx errors
- **CloudWatch Dashboard**: ALB metrics, EC2 metrics, custom metrics
- **X-Ray**: Distributed tracing with custom subsegments

## 📊 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/items?count=N` | GET | Returns N dummy items |
| `/error` | GET | Intentional 500 error |
| `/docs` | GET | Swagger documentation |

## 🔒 Security Groups

| Security Group | Inbound | Outbound |
|----------------|---------|----------|
| ALB | 80, 443 from 0.0.0.0/0 | All traffic |
| EC2 | 8080 from ALB | All traffic |
| RDS | 5432 from EC2 | None |
| Redis | 6379 from EC2 | None |

## 📈 Monitoring

### Alarms
- **HighErrorRate**: > 5 errors in 5 minutes
- **HighP95Latency**: p95 > 500ms
- **ALB5xxErrors**: > 10 5xx errors in 5 minutes
- **UnhealthyHosts**: Any unhealthy host

### Dashboard Widgets
1. ALB Request Count
2. ALB Response Time (p50, p95, p99)
3. ALB 4xx Errors
4. ALB 5xx Errors
5. EC2 CPU Utilization
6. Application Error Count
7. ASG Instance Count
8. ALB Healthy Hosts

## 🧹 Cleanup

```bash
# Delete stacks in reverse order
aws cloudformation delete-stack --stack-name mp-observability
aws cloudformation delete-stack --stack-name mp-compute
aws cloudformation delete-stack --stack-name mp-security
aws cloudformation delete-stack --stack-name mp-network
```

## 📝 Local Development

```bash
cd app
pip install -r requirements.txt
python main.py
```

The API will be available at http://localhost:8080
