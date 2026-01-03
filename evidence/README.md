# Evidence directory for deployment outputs
# This directory stores CloudFormation stack outputs and test results

# Example commands to save evidence:
# aws cloudformation describe-stacks --stack-name mp-network > evidence/network-stack.json
# aws cloudformation describe-stacks --stack-name mp-security > evidence/security-stack.json
# aws cloudformation describe-stacks --stack-name mp-compute > evidence/compute-stack.json
# aws cloudformation describe-stacks --stack-name mp-observability > evidence/observability-stack.json
