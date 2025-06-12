# 🚀 Quick Start Guide

Step-by-step commands to get the Competitor Tracking SaaS Backend running locally and deployed to AWS.

## 📋 Prerequisites

### Required Tools
```bash
# Install AWS CLI
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /

# Install SAM CLI
pip install aws-sam-cli
# OR on macOS
brew install aws-sam-cli

# Install Docker
# Download from https://docker.com/get-started

# Configure AWS credentials
aws configure
```

### API Keys Required
- **OpenAI API Key**: Get from https://platform.openai.com/api-keys
- **ScrapingBee API Key** (Optional): Get from https://app.scrapingbee.com/
  - Only needed if you want to use premium scraping features
  - System defaults to free Playwright scraper

---

## 🏠 Local Development Setup

### Step 1: Environment Setup
```bash
# Clone repository (if not already done)
git clone <your-repo-url>
cd slight-backend

# Copy environment template
cp env.example .env

# Edit .env file with your API keys
nano .env
# OR
code .env
```

### Step 2: Configure Environment Variables
Edit `.env` with your actual values:
```bash
# Database Configuration
DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/competitordb"

# API Keys
OPENAI_API_KEY="sk-your-actual-openai-key"

# Scraping Configuration (NEW - Flexible Architecture)
PREFERRED_SCRAPER="playwright"          # Options: 'playwright' (free), 'scrapingbee' (paid), 'auto'
SCRAPINGBEE_API_KEY="your-scrapingbee-key"  # Only needed if using ScrapingBee

# Environment
ENVIRONMENT="dev"
```

**🎭 Scraping Options Explained:**
- **`playwright`** (FREE): Uses browser automation, requires no API keys
- **`scrapingbee`** (PAID): Uses premium proxy service, requires API key  
- **`auto`** (SMART): Automatically chooses best available option

### Step 3: Start Local Database
```bash
# Start PostgreSQL with Docker
docker-compose up -d postgres

# Verify database is running
docker-compose ps

# Access database admin (optional)
# Open http://localhost:8080 in browser
# Server: postgres, Username: postgres, Password: postgres, Database: competitordb
```

### Step 4: Install Python Dependencies
```bash
# Navigate to source directory
cd src

# Install dependencies (includes Playwright)
pip install -r requirements.txt

# Install Playwright browsers (required for local development)
playwright install chromium

# OR use virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

**📦 Dependencies Installed:**
- **Database**: SQLAlchemy, asyncpg, psycopg2
- **Scraping**: Playwright (free), BeautifulSoup, aiohttp
- **AI**: LangChain, OpenAI
- **AWS**: boto3, botocore

### Step 5: Initialize Database
```bash
# Run database migrations and create test user
python ../scripts/test_local.py

# OR manually run migrations
python -c "
import asyncio
import sys
import os
sys.path.insert(0, '.')
from handlers.migrations import run_migrations, create_test_user

async def setup():
    # Run migrations
    result = await run_migrations()
    print('Migrations:', result)
    
    # Create test user
    user_result = await create_test_user()
    print('Test user:', user_result)

asyncio.run(setup())
"
```

### Step 6: Test Local Setup
```bash
# Run comprehensive tests
python ../scripts/test_local.py

# Expected output:
# ✅ Database connection successful
# ✅ Database migrations completed
# ✅ Test user created
# ✅ Competitor created
# ✅ All tests passed!
```

### Step 7: Test Scraping Architecture (NEW)
```bash
# Test the flexible scraping architecture
python ../scripts/test_scraping.py

# Expected output:
# 🔍 Available Scrapers:
# ✅ Playwright: Ready
# ❌ ScrapingBee: API key required (or ✅ if key provided)
# 🎭 Testing Playwright Scraper: ✅ Success
# 🤖 Auto-detected scraper: Playwright
```

### Step 8: Test Individual Functions (Optional)
```bash
# Test competitor management
python -c "
import asyncio
import sys
sys.path.insert(0, '.')
from handlers.competitor_management import handler

event = {
    'httpMethod': 'GET',
    'queryStringParameters': {'user_id': 'test-user-id'},
    'pathParameters': None,
    'body': None
}
result = handler(event, {})
print(result)
"

# Test flexible scraper creation
python -c "
import sys
sys.path.insert(0, '.')
from handlers.scrape_competitor import CompetitorScraper
from scrapers.factory import ScraperFactory

# Test auto-detection
scraper = CompetitorScraper()
print('✅ Auto-detection scraper created')

# Show available scrapers
available = ScraperFactory.get_available_scrapers()
for name, info in available.items():
    status = '✅' if info['available'] else '❌'
    print(f'{status} {name}: {info[\"status\"]}')
"

# Test specific scraper (Playwright)
python -c "
import asyncio
import sys
sys.path.insert(0, '.')
from handlers.scrape_competitor import CompetitorScraper

async def test_playwright():
    async with CompetitorScraper('playwright') as scraper:
        info = scraper.get_scraper_info()
        print(f'✅ Playwright scraper ready: {info[\"name\"]} (cost: {info[\"cost\"]})')

asyncio.run(test_playwright())
"
```

---

## ☁️ AWS Deployment

### Step 1: Prepare for Deployment
```bash
# Ensure you're in project root
cd /path/to/slight-backend

# Verify AWS credentials
aws sts get-caller-identity

# Should return your AWS account info
```

### Step 2: Quick Deployment (Guided)
```bash
# Run guided deployment (recommended for first time)
./scripts/deploy.sh --guided

# Follow the prompts to configure:
# - Stack name
# - AWS region
# - Database password
# - API keys
# - Deployment preferences
```

### Step 3: Direct Deployment with Parameters
```bash
# Deploy with Playwright (FREE) - no ScrapingBee key needed
./scripts/deploy.sh \
  --stack-name "competitor-tracking-prod" \
  --region "us-east-1" \
  --db-password "YourSecurePassword123!" \
  --openai-key "sk-your-openai-api-key" \
  --scrapingbee-key "dummy-key-not-used"

# OR deploy with ScrapingBee (PAID) - premium features
./scripts/deploy.sh \
  --stack-name "competitor-tracking-prod" \
  --region "us-east-1" \
  --db-password "YourSecurePassword123!" \
  --openai-key "sk-your-openai-api-key" \
  --scrapingbee-key "your-actual-scrapingbee-api-key"
```

**💡 Deployment Notes:**
- **Lambda Memory**: Increased to 1GB for Playwright browser automation
- **Lambda Timeout**: Increased to 60s for browser startup time
- **Default Scraper**: Playwright (free) unless ScrapingBee key provided and preferred

### Step 4: Manual SAM Commands (Alternative)
```bash
# Build the application
sam build

# Deploy with parameters
sam deploy \
  --stack-name competitor-tracking-stack \
  --region us-east-1 \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    Environment=prod \
    DBPassword="YourSecurePassword123!" \
    OpenAIApiKey="sk-your-openai-api-key" \
    ScrapingBeeApiKey="your-scrapingbee-api-key" \
  --no-confirm-changeset
```

### Step 5: Initialize Production Database
```bash
# Get the migration function name from CloudFormation outputs
aws cloudformation describe-stacks \
  --stack-name competitor-tracking-stack \
  --query 'Stacks[0].Outputs[?OutputKey==`DatabaseMigrationFunction`].OutputValue' \
  --output text

# Run database migration
aws lambda invoke \
  --function-name "competitor-tracking-stack-DatabaseMigrationFunction-XXXXXXXXXX" \
  --payload '{"action": "create_test_user"}' \
  response.json

# Check response
cat response.json
```

### Step 6: Verify Deployment
```bash
# Get API Gateway endpoint
aws cloudformation describe-stacks \
  --stack-name competitor-tracking-stack \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayEndpoint`].OutputValue' \
  --output text

# Test API endpoint (replace with your actual endpoint)
curl -X GET "https://your-api-id.execute-api.us-east-1.amazonaws.com/Prod/competitors?user_id=test-user-id"
```

---

## 🧪 Testing Deployed API

### Get API Gateway URL
```bash
# Get the API endpoint from CloudFormation
API_URL=$(aws cloudformation describe-stacks \
  --stack-name competitor-tracking-stack \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayEndpoint`].OutputValue' \
  --output text)

echo "API URL: $API_URL"
```

### Test Endpoints
```bash
# Replace USER_ID with actual test user ID from migration response

# 1. List competitors
curl -X GET "$API_URL/competitors?user_id=YOUR_USER_ID"

# 2. Create a competitor
curl -X POST "$API_URL/competitors" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "YOUR_USER_ID",
    "name": "Test Competitor",
    "website": "https://example.com",
    "pricing_url": "https://example.com/pricing",
    "description": "A test competitor"
  }'

# 3. Generate battle card
curl -X POST "$API_URL/battle-card" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "generate",
    "user_id": "YOUR_USER_ID"
  }'

# 4. Trigger scraping
curl -X POST "$API_URL/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "scrape_all"
  }'
```

---

## 🕷️ Testing Scraping Options

### Test Different Scrapers Locally
```bash
# Test auto-detection (will use Playwright by default)
python scripts/test_scraping.py

# Test Playwright specifically (FREE)
PREFERRED_SCRAPER=playwright python scripts/test_scraping.py

# Test ScrapingBee (PAID) - only if you have API key
PREFERRED_SCRAPER=scrapingbee SCRAPINGBEE_API_KEY=your_key python scripts/test_scraping.py
```

### Compare Scraper Performance
```bash
# Create a comparison test
python -c "
import asyncio
import time
import os
import sys
sys.path.insert(0, 'src')

from handlers.scrape_competitor import CompetitorScraper

async def compare_scrapers():
    url = 'https://httpbin.org/html'  # Simple test page
    
    # Test Playwright
    start = time.time()
    try:
        async with CompetitorScraper('playwright') as scraper:
            result1 = await scraper.scrape_url(url, 'Test')
            playwright_time = time.time() - start
            print(f'🎭 Playwright: {playwright_time:.2f}s - ✅ Success')
    except Exception as e:
        print(f'🎭 Playwright: ❌ Failed - {e}')
    
    # Test ScrapingBee (if available)
    if os.getenv('SCRAPINGBEE_API_KEY'):
        start = time.time()
        try:
            async with CompetitorScraper('scrapingbee') as scraper:
                result2 = await scraper.scrape_url(url, 'Test')
                bee_time = time.time() - start
                print(f'🐝 ScrapingBee: {bee_time:.2f}s - ✅ Success')
        except Exception as e:
            print(f'🐝 ScrapingBee: ❌ Failed - {e}')
    else:
        print('🐝 ScrapingBee: ⏭️  Skipped (no API key)')

asyncio.run(compare_scrapers())
"
```

### Test Deployed Scraping
```bash
# Test scraping on AWS (replace with your API URL)
API_URL="https://your-api-id.execute-api.us-east-1.amazonaws.com/Prod"

# Test auto-detection scraping
curl -X POST "$API_URL/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "test_scrape",
    "url": "https://httpbin.org/html",
    "competitor_name": "Test Site"
  }'

# Check Lambda logs to see which scraper was used
sam logs -n ScrapeCompetitorFunction --stack-name competitor-tracking-stack --tail
```

### Scraper Cost Analysis
```bash
# Calculate monthly costs for different scenarios
python -c "
print('💰 Scraping Cost Analysis (per month):')
print()
print('🎭 Playwright (FREE):')
print('   • Scraping: $0')
print('   • Lambda: ~$1-5 (1GB memory, depends on usage)')
print('   • Total: ~$1-5')
print()
print('🐝 ScrapingBee (PAID):')
print('   • Scraping: $29-199 (depending on plan)')
print('   • Lambda: ~$0.50-2 (512MB memory)')
print('   • Total: ~$29.50-201')
print()
print('📊 Break-even Analysis:')
print('   • ScrapingBee worth it if: advanced anti-bot needed')
print('   • Playwright sufficient for: most SaaS pricing pages')
print('   • Recommendation: Start with Playwright, upgrade if needed')
"
```

---

## 🔧 Troubleshooting Commands

### Local Development Issues
```bash
# Check Docker containers
docker-compose ps
docker-compose logs postgres

# Check database connection
docker exec -it competitor-tracking-postgres psql -U postgres -d competitordb -c "\dt"

# Restart database
docker-compose restart postgres

# View logs
docker-compose logs -f postgres
```

### AWS Deployment Issues
```bash
# Check CloudFormation stack status
aws cloudformation describe-stacks --stack-name competitor-tracking-stack

# View CloudFormation events
aws cloudformation describe-stack-events --stack-name competitor-tracking-stack

# Check Lambda function logs
sam logs -n ScrapeCompetitorFunction --stack-name competitor-tracking-stack --tail

# View all stack outputs
aws cloudformation describe-stacks \
  --stack-name competitor-tracking-stack \
  --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
  --output table
```

### Database Connection Issues
```bash
# Test database connectivity from Lambda
aws lambda invoke \
  --function-name "competitor-tracking-stack-DatabaseMigrationFunction-XXXXXXXXXX" \
  --payload '{"action": "health_check"}' \
  response.json

cat response.json
```

---

## 🗑️ Cleanup Commands

### Stop Local Development
```bash
# Stop Docker containers
docker-compose down

# Remove volumes (WARNING: deletes all data)
docker-compose down -v

# Remove images
docker-compose down --rmi all
```

### Delete AWS Resources
```bash
# Delete CloudFormation stack (WARNING: deletes all AWS resources)
sam delete --stack-name competitor-tracking-stack

# OR manually
aws cloudformation delete-stack --stack-name competitor-tracking-stack

# Monitor deletion
aws cloudformation describe-stacks --stack-name competitor-tracking-stack
```

---

## 📊 Monitoring Commands

### View Lambda Logs
```bash
# Real-time logs for scraping function
sam logs -n ScrapeCompetitorFunction --stack-name competitor-tracking-stack --tail

# Real-time logs for battle card function
sam logs -n GenerateBattleCardFunction --stack-name competitor-tracking-stack --tail

# Logs for competitor management
sam logs -n CompetitorManagementFunction --stack-name competitor-tracking-stack --tail
```

### Database Queries
```bash
# Connect to local database
docker exec -it competitor-tracking-postgres psql -U postgres -d competitordb

# Check table contents
# SELECT * FROM users;
# SELECT * FROM competitors;
# SELECT * FROM scrape_results ORDER BY scraped_at DESC LIMIT 5;
# SELECT * FROM battle_cards ORDER BY generated_at DESC LIMIT 5;
```

---

## ✅ Quick Validation Checklist

### Local Setup ✓
- [ ] Docker containers running
- [ ] Database connection successful
- [ ] Migrations completed
- [ ] Test user created
- [ ] Dependencies installed
- [ ] Environment variables configured

### AWS Deployment ✓
- [ ] CloudFormation stack deployed successfully
- [ ] All Lambda functions created
- [ ] RDS instance running
- [ ] API Gateway endpoints accessible
- [ ] Database migration completed
- [ ] Test API calls successful

**🎉 You're all set! Your Competitor Tracking SaaS Backend is ready to use.** 