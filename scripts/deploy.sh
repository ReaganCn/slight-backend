#!/bin/bash

# Deployment script for Competitor Tracking SaaS Backend
set -e

echo "🚀 Starting deployment of Competitor Tracking SaaS Backend..."

# Check if SAM CLI is installed
if ! command -v sam &> /dev/null; then
    echo "❌ SAM CLI not found. Please install it first:"
    echo "   pip install aws-sam-cli"
    exit 1
fi

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

# Default values
STACK_NAME="competitor-tracking-stack"
REGION="us-east-1"
DB_PASSWORD=""
OPENAI_API_KEY=""
SCRAPINGBEE_API_KEY=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --stack-name)
            STACK_NAME="$2"
            shift 2
            ;;
        --region)
            REGION="$2"
            shift 2
            ;;
        --db-password)
            DB_PASSWORD="$2"
            shift 2
            ;;
        --openai-key)
            OPENAI_API_KEY="$2"
            shift 2
            ;;
        --scrapingbee-key)
            SCRAPINGBEE_API_KEY="$2"
            shift 2
            ;;
        --guided)
            GUIDED=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --stack-name NAME        CloudFormation stack name (default: competitor-tracking-stack)"
            echo "  --region REGION          AWS region (default: us-east-1)"
            echo "  --db-password PASSWORD   RDS PostgreSQL password"
            echo "  --openai-key KEY         OpenAI API key"
            echo "  --scrapingbee-key KEY    ScrapingBee API key"
            echo "  --guided                 Use SAM guided deployment"
            echo "  -h, --help               Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option $1"
            exit 1
            ;;
    esac
done

# Prompt for required parameters if not provided
if [[ -z "$DB_PASSWORD" && -z "$GUIDED" ]]; then
    read -s -p "Enter RDS PostgreSQL password: " DB_PASSWORD
    echo
fi

if [[ -z "$OPENAI_API_KEY" && -z "$GUIDED" ]]; then
    read -s -p "Enter OpenAI API key: " OPENAI_API_KEY
    echo
fi

if [[ -z "$SCRAPINGBEE_API_KEY" && -z "$GUIDED" ]]; then
    read -s -p "Enter ScrapingBee API key: " SCRAPINGBEE_API_KEY
    echo
fi

echo "📦 Building SAM application..."
sam build

if [[ "$GUIDED" == "true" ]]; then
    echo "🎯 Running guided deployment..."
    sam deploy --guided
else
    echo "🎯 Deploying to AWS..."
    sam deploy \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --capabilities CAPABILITY_IAM \
        --parameter-overrides \
            Environment=prod \
            DBPassword="$DB_PASSWORD" \
            OpenAIApiKey="$OPENAI_API_KEY" \
            ScrapingBeeApiKey="$SCRAPINGBEE_API_KEY" \
        --no-confirm-changeset
fi

echo "✅ Deployment completed!"

# Get stack outputs
echo "📋 Stack Outputs:"
aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
    --output table

echo ""
echo "🔄 Next steps:"
echo "1. Run database migration:"
echo "   aws lambda invoke --function-name ${STACK_NAME}-DatabaseMigrationFunction-XXX --payload '{\"action\": \"create_test_user\"}' response.json"
echo ""
echo "2. Test the API endpoints using the API Gateway URL from outputs above"
echo ""
echo "3. Monitor CloudWatch logs for any issues"

echo "🎉 Deployment completed successfully!" 