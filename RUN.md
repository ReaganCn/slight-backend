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

### 🆕 NEW: Optional API Keys for Enhanced Features
- **Twitter Bearer Token**: Get from https://developer.twitter.com/
- **LinkedIn Credentials**: For unofficial API access (use carefully)
- **Instagram Credentials**: For business account metrics
- **TikTok Access Token**: Get from https://developers.tiktok.com/
- **SerpAPI Key**: Get from https://serpapi.com/ (for enhanced search)

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

# Core API Keys
COHERE_API_KEY="your-cohere-api-key"         # Primary AI for URL categorization
OPENAI_API_KEY="sk-your-actual-openai-key"   # Fallback AI (GPT-4 access)

# Scraping Configuration (Flexible Architecture)
PREFERRED_SCRAPER="playwright"          # Options: 'playwright' (free), 'scrapingbee' (paid), 'auto'
SCRAPINGBEE_API_KEY="your-scrapingbee-key"  # Only needed if using ScrapingBee

# 🆕 NEW: URL Discovery Configuration
SERPAPI_KEY="your-serpapi-key"                    # Optional for enhanced search capabilities
LANGCHAIN_SEARCH_RESULTS_LIMIT="10"              # Number of search results to analyze
URL_DISCOVERY_CONFIDENCE_THRESHOLD="0.7"         # Minimum confidence score for auto-confirmation

# 🆕 NEW: Social Media API Keys
TWITTER_BEARER_TOKEN="your_twitter_bearer_token"
LINKEDIN_EMAIL="your_linkedin_email"             # For unofficial LinkedIn API
LINKEDIN_PASSWORD="your_linkedin_password"       # Use app-specific password if 2FA enabled
INSTAGRAM_USERNAME="your_instagram_username"     # For unofficial Instagram API
INSTAGRAM_PASSWORD="your_instagram_password"     # Use app-specific password if 2FA enabled
TIKTOK_ACCESS_TOKEN="your_tiktok_access_token"

# Environment
ENVIRONMENT="dev"
```

**🎭 Scraping Options Explained:**
- **`playwright`** (FREE): Uses browser automation, requires no API keys
- **`scrapingbee`** (PAID): Uses premium proxy service, requires API key  
- **`auto`** (SMART): Automatically chooses best available option

**🆕 NEW: URL Discovery Options:**
- **Google Custom Search**: Premium quality search (100 free queries/day)
- **Brave Search API**: Independent search index (2,000 free queries/month)
- **Sitemap Analysis**: Automated sitemap parsing and URL extraction
- **AI Enhancement**: Cohere-first AI categorization with OpenAI fallback

**🆕 NEW: Social Media Integration:**
- **Twitter/X**: Official API v2 (requires Bearer Token)
- **LinkedIn**: Unofficial API (use personal credentials carefully)
- **Instagram**: Business account metrics (unofficial API)
- **TikTok**: Official API for business accounts

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

# Install dependencies (includes Playwright + new packages)
pip install -r requirements.txt

# Add playwright to path
export PATH="$HOME/Library/Python/3.9/bin:$PATH"
source ~/.zshrc  # or ~/.bash_profile

# Install Playwright browsers (required for local development)
playwright install chromium

# OR use virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

**📦 Enhanced Dependencies Installed:**
- **Database**: SQLAlchemy, asyncpg, psycopg2
- **Scraping**: Playwright (free), BeautifulSoup, aiohttp, requests-html
- **AI/Search**: LangChain, OpenAI, google-search-results
- **Social Media**: tweepy, linkedin-api, instagrapi, TikTokApi
- **URL Processing**: validators, sitemap-parser
- **AWS**: boto3, botocore

### Step 5: Initialize Database
```bash
# Run database migrations and create test user (enhanced schema)
python ../scripts/test_local.py

# OR manually run migrations
python -c "
import asyncio
import sys
import os
sys.path.insert(0, '.')
from handlers.migrations import run_migrations, create_test_user

async def setup():
    # Run enhanced migrations (includes new tables)
    result = await run_migrations()
    print('Migrations:', result)
    
    # Create test user with sample data
    user_result = await create_test_user()
    print('Test user:', user_result)

asyncio.run(setup())
"
```

### Step 6: Test Local Setup
```bash
# Run comprehensive tests (enhanced)
python ../scripts/test_local.py

# Expected output:
# ✅ Database connection successful
# ✅ Database migrations completed (including new tables)
# ✅ Test user created
# ✅ Competitor created
# ✅ URL discovery service ready (Google CSE + Brave Search)
# ✅ Social media service ready
# ✅ All tests passed!
```

### Step 7: 🆕 NEW: Test URL Discovery & Social Media Features
```bash
# Test the complete URL discovery and social media workflow
python ../scripts/test_url_discovery.py

# 🆕 NEW: Test modular URL discovery with Cohere-first
python ../scripts/test_url_discovery_simple.py

# Expected output:
# 🔍 Testing URL Discovery Service:
# ✅ LangChain integration ready
# ✅ Google Custom Search working
# ✅ Brave Search API working
# ✅ URL categorization working
# ✅ Confidence scoring working
# 
# 📱 Testing Social Media Integration:
# ✅ Twitter API ready (if token provided)
# ✅ LinkedIn API ready (if credentials provided)
# ✅ Instagram API ready (if credentials provided)
# ✅ TikTok API ready (if token provided)
# 
# 💾 Testing Database Models:
# ✅ CompetitorUrl model created
# ✅ SocialMediaData model created
# ✅ Relationships working
# 
# 🔄 Testing End-to-End Workflow:
# ✅ URL discovery pipeline
# ✅ Social media fetching
# ✅ Enhanced scraping
# ✅ All integration tests passed!
```

### Step 8: Test Individual Functions (Enhanced)
```bash
# Test enhanced competitor management
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
print('Enhanced competitor management:', result)
"

# Test URL discovery service with Cohere-first
python -c "
import asyncio
import sys
sys.path.insert(0, '.')
from services.url_discovery import URLDiscoveryService
import os

async def test_discovery():
    if os.getenv('COHERE_API_KEY'):
        service = URLDiscoveryService(
            cohere_api_key=os.getenv('COHERE_API_KEY'),
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            serpapi_key=os.getenv('SERPAPI_KEY')
        )
        urls = await service.discover_competitor_urls('Slack', 'https://slack.com')
        print(f'✅ Discovered {len(urls)} URLs for Slack')
        for url in urls[:3]:  # Show first 3
            print(f'  - {url.category}: {url.url} (confidence: {url.confidence_score:.2f})')
    else:
        print('❌ Cohere API key required for URL discovery')

asyncio.run(test_discovery())
"

# Test social media service
python -c "
import asyncio
import sys
sys.path.insert(0, '.')
from services.social_media import SocialMediaFetcher
import os

async def test_social():
    config = {
        'TWITTER_BEARER_TOKEN': os.getenv('TWITTER_BEARER_TOKEN'),
        'LINKEDIN_EMAIL': os.getenv('LINKEDIN_EMAIL'),
        'LINKEDIN_PASSWORD': os.getenv('LINKEDIN_PASSWORD'),
        'INSTAGRAM_USERNAME': os.getenv('INSTAGRAM_USERNAME'),
        'INSTAGRAM_PASSWORD': os.getenv('INSTAGRAM_PASSWORD'),
        'TIKTOK_ACCESS_TOKEN': os.getenv('TIKTOK_ACCESS_TOKEN')
    }
    
    fetcher = SocialMediaFetcher(config)
    available_platforms = fetcher.get_available_platforms()
    print(f'✅ Available social media platforms: {list(available_platforms.keys())}')

asyncio.run(test_social())
"

# Test enhanced scraping
python -c "
import asyncio
import sys
sys.path.insert(0, '.')
from handlers.scrape_competitor import EnhancedCompetitorScraper

async def test_enhanced_scraping():
    async with EnhancedCompetitorScraper() as scraper:
        info = scraper.get_scraper_info()
        print(f'✅ Enhanced scraper ready: {info[\"name\"]} (category-aware: {info.get(\"category_aware\", True)})')

asyncio.run(test_enhanced_scraping())
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
# - API keys (including new social media keys)
# - Deployment preferences
```

### Step 3: Direct Deployment with Enhanced Parameters
```bash
# Deploy with basic features (free tier)
./scripts/deploy.sh \
  --stack-name "competitor-tracking-prod" \
  --region "us-east-1" \
  --db-password "YourSecurePassword123!" \
  --openai-key "sk-your-openai-api-key" \
  --scrapingbee-key "dummy-key-not-used"

# Deploy with enhanced URL discovery
./scripts/deploy.sh \
  --stack-name "competitor-tracking-prod" \
  --region "us-east-1" \
  --db-password "YourSecurePassword123!" \
  --openai-key "sk-your-openai-api-key" \
  --serpapi-key "your-serpapi-key" \
  --scrapingbee-key "dummy-key-not-used"

# Deploy with full social media integration
./scripts/deploy.sh \
  --stack-name "competitor-tracking-prod" \
  --region "us-east-1" \
  --db-password "YourSecurePassword123!" \
  --openai-key "sk-your-openai-api-key" \
  --twitter-token "your-twitter-bearer-token" \
  --linkedin-email "your-linkedin-email" \
  --linkedin-password "your-linkedin-password" \
  --scrapingbee-key "your-scrapingbee-key"
```

**💡 Enhanced Deployment Notes:**
- **Lambda Memory**: Optimized for different features (1GB for URL discovery, 512MB for social media)
- **Lambda Timeout**: Increased to 90s for complex URL discovery operations
- **Environment Variables**: Automatically configured for all new services
- **Database Schema**: Enhanced migrations run automatically on first deployment

### Step 4: Manual SAM Commands (Alternative)
```bash
# Build the application
sam build

# Deploy with enhanced parameters
sam deploy \
  --stack-name competitor-tracking-stack \
  --region us-east-1 \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    Environment=prod \
    DBPassword="YourSecurePassword123!" \
    OpenAIApiKey="sk-your-openai-api-key" \
    ScrapingBeeApiKey="your-scrapingbee-api-key" \
    TwitterBearerToken="your-twitter-token" \
    LinkedInEmail="your-linkedin-email" \
    LinkedInPassword="your-linkedin-password" \
    SerpApiKey="your-serpapi-key" \
  --no-confirm-changeset
```

### Step 5: Initialize Production Database (Enhanced)
```bash
# Get the migration function name from CloudFormation outputs
aws cloudformation describe-stacks \
  --stack-name competitor-tracking-stack \
  --query 'Stacks[0].Outputs[?OutputKey==`DatabaseMigrationFunction`].OutputValue' \
  --output text

# Run enhanced database migration (includes new tables)
aws lambda invoke \
  --function-name "competitor-tracking-stack-DatabaseMigrationFunction-XXXXXXXXXX" \
  --payload '{"action": "create_test_user"}' \
  response.json

# Check response
cat response.json

# Expected to see new tables created:
# - competitors (enhanced)
# - competitor_urls (new)
# - social_media_data (new)
```

### Step 6: Verify Enhanced Deployment
```bash
# Get API Gateway endpoint
API_URL=$(aws cloudformation describe-stacks \
  --stack-name competitor-tracking-stack \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayEndpoint`].OutputValue' \
  --output text)

echo "API URL: $API_URL"

# Test core functionality
curl -X GET "$API_URL/competitors?user_id=test-user-id"

# 🆕 Test new URL discovery endpoint
curl -X POST "$API_URL/competitors/test-competitor-id/discover-urls" \
  -H "Content-Type: application/json" \
  -d '{"trigger_discovery": true}'

# 🆕 Test new social media endpoint
curl -X GET "$API_URL/competitors/test-competitor-id/social-media"
```

---

## 🧪 Testing Deployed API (Enhanced)

### Get API Gateway URL
```bash
# Get the API endpoint from CloudFormation
API_URL=$(aws cloudformation describe-stacks \
  --stack-name competitor-tracking-stack \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayEndpoint`].OutputValue' \
  --output text)

echo "API URL: $API_URL"
```

### Test Core Endpoints
```bash
# Replace USER_ID with actual test user ID from migration response

# 1. List competitors (enhanced with URL discovery status)
curl -X GET "$API_URL/competitors?user_id=YOUR_USER_ID"

# 2. Create a competitor (with optional URL discovery trigger)
curl -X POST "$API_URL/competitors" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "YOUR_USER_ID",
    "name": "Test Competitor",
    "website": "https://example.com",
    "description": "A test competitor",
    "trigger_url_discovery": true
  }'

# 3. Generate enhanced battle card (with discovered URLs and social data)
curl -X POST "$API_URL/battle-card" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "generate",
    "user_id": "YOUR_USER_ID"
  }'
```

### 🆕 Test New URL Discovery Endpoints
```bash
COMPETITOR_ID="your-competitor-id"

# 1. Trigger URL discovery
curl -X POST "$API_URL/competitors/$COMPETITOR_ID/discover-urls" \
  -H "Content-Type: application/json" \
  -d '{
    "search_depth": "comprehensive",
    "include_social": true
  }'

# 2. Get discovered URLs
curl -X GET "$API_URL/competitors/$COMPETITOR_ID/urls"

# 3. Confirm/reject discovered URLs
curl -X PUT "$API_URL/competitors/$COMPETITOR_ID/urls" \
  -H "Content-Type: application/json" \
  -d '{
    "confirmations": [
      {"url_id": "url-uuid-1", "status": "confirmed"},
      {"url_id": "url-uuid-2", "status": "rejected"}
    ]
  }'

# 4. Scrape all confirmed URLs
curl -X POST "$API_URL/competitors/$COMPETITOR_ID/scrape-all"

# 5. Scrape specific category
curl -X POST "$API_URL/competitors/$COMPETITOR_ID/scrape-category" \
  -H "Content-Type: application/json" \
  -d '{"category": "pricing"}'
```

### 🆕 Test New Social Media Endpoints
```bash
# 1. Get stored social media data
curl -X GET "$API_URL/competitors/$COMPETITOR_ID/social-media"

# 2. Fetch fresh social media data
curl -X POST "$API_URL/competitors/$COMPETITOR_ID/social-media" \
  -H "Content-Type: application/json" \
  -d '{
    "platforms": ["twitter", "linkedin", "instagram"],
    "include_posts": true
  }'

# 3. Fetch specific platform data
curl -X POST "$API_URL/competitors/$COMPETITOR_ID/social-media/twitter" \
  -H "Content-Type: application/json" \
  -d '{"include_recent_posts": true}'

# 4. Get social media trends
curl -X GET "$API_URL/competitors/$COMPETITOR_ID/social-media/trends?days=30"
```

---

## 🕷️ Testing Enhanced Scraping Options

### Test Different Scrapers Locally
```bash
# Test auto-detection (will use Playwright by default)
python scripts/test_scraping.py

# Test Playwright specifically (FREE)
PREFERRED_SCRAPER=playwright python scripts/test_scraping.py

# Test ScrapingBee (PAID) - only if you have API key
PREFERRED_SCRAPER=scrapingbee SCRAPINGBEE_API_KEY=your_key python scripts/test_scraping.py

# 🆕 Test enhanced scraping with URL discovery
python scripts/test_url_discovery.py --test-scraping
```

### Compare Enhanced Scraper Performance
```bash
# Create a comprehensive comparison test
python -c "
import asyncio
import time
import os
import sys
sys.path.insert(0, 'src')

from handlers.scrape_competitor import EnhancedCompetitorScraper

async def compare_enhanced_scrapers():
    test_urls = [
        ('https://slack.com/pricing', 'pricing'),
        ('https://notion.so/product', 'features'),
        ('https://airtable.com/blog', 'blog')
    ]
    
    for url, category in test_urls:
        print(f'\\n🧪 Testing {category} page: {url}')
        
        # Test enhanced scraping
        start = time.time()
        try:
            async with EnhancedCompetitorScraper() as scraper:
                result = await scraper.scrape_discovered_url({
                    'url': url,
                    'category': category,
                    'confidence_score': 0.9
                }, 'Test Competitor')
                duration = time.time() - start
                print(f'✅ Enhanced scraping: {duration:.2f}s - Category: {category}')
                print(f'   Extracted data points: {len(result.get(\"data\", {}))}')
        except Exception as e:
            print(f'❌ Enhanced scraping failed: {e}')

asyncio.run(compare_enhanced_scrapers())
"
```

### Test Deployed Enhanced Scraping
```bash
# Test category-aware scraping on AWS
API_URL="https://your-api-id.execute-api.us-east-1.amazonaws.com/Prod"

# Test scraping by category
curl -X POST "$API_URL/competitors/$COMPETITOR_ID/scrape-category" \
  -H "Content-Type: application/json" \
  -d '{
    "category": "pricing",
    "scraper_preference": "auto"
  }'

# Test scraping all confirmed URLs
curl -X POST "$API_URL/competitors/$COMPETITOR_ID/scrape-all" \
  -H "Content-Type: application/json"

# Check enhanced Lambda logs
sam logs -n ScrapeCompetitorFunction --stack-name competitor-tracking-stack --tail
```

### Enhanced Cost Analysis
```bash
# Calculate monthly costs for different scenarios (updated)
python -c "
print('💰 Enhanced Cost Analysis (per month):')
print()
print('🆓 FREE TIER (Basic Features):')
print('   • Scraping: Playwright ($0)')
print('   • URL Discovery: Cohere free tier (~$0-2)')
print('   • Social Media: Free tier APIs (~$0)')
print('   • Lambda: ~$1-3 (varies by usage)')
print('   • RDS: ~$13 (db.t3.micro)')
print('   • Total: ~$14-18')
print()
print('💎 PREMIUM TIER (All Features):')
print('   • Scraping: ScrapingBee ($29-199)')
print('   • URL Discovery: Cohere + OpenAI fallback (~$5-15)')
print('   • Social Media: Paid APIs (~$0-50)')
print('   • Lambda: ~$2-5 (higher usage)')
print('   • RDS: ~$13-25 (depends on usage)')
print('   • Total: ~$49-294')
print()
print('🎯 HYBRID APPROACH (Recommended):')
print('   • Scraping: Playwright (free) with ScrapingBee fallback')
print('   • URL Discovery: Cohere-first with OpenAI fallback')
print('   • Social Media: Mix of free and paid APIs')
print('   • Total: ~$20-70 (optimal cost/performance)')
print()
print('📊 Break-even Analysis:')
print('   • Premium worth it if: >100 competitors tracked')
print('   • Free tier sufficient for: <50 competitors')
print('   • Hybrid optimal for: 20-100 competitors')
"
```

---

## 🔧 Troubleshooting Commands (Enhanced)

### Local Development Issues
```bash
# Check Docker containers
docker-compose ps
docker-compose logs postgres

# Check database connection and new tables
docker exec -it competitor-tracking-postgres psql -U postgres -d competitordb -c "
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;
"

# Should show new tables:
# - battle_cards
# - competitor_urls (NEW)
# - competitors (enhanced)
# - scrape_jobs
# - scrape_results
# - social_media_data (NEW)
# - users

# Test new services individually
python -c "
import sys
sys.path.insert(0, 'src')

# Test URL discovery service
try:
    from services.url_discovery import URLDiscoveryService
    print('✅ URL Discovery service imports successfully')
except Exception as e:
    print(f'❌ URL Discovery service error: {e}')

# Test social media service
try:
    from services.social_media import SocialMediaFetcher
    print('✅ Social Media service imports successfully')
except Exception as e:
    print(f'❌ Social Media service error: {e}')
"

# Restart database
docker-compose restart postgres

# View logs
docker-compose logs -f postgres
```

### AWS Deployment Issues (Enhanced)
```bash
# Check CloudFormation stack status
aws cloudformation describe-stacks --stack-name competitor-tracking-stack

# View CloudFormation events (check for new Lambda functions)
aws cloudformation describe-stack-events --stack-name competitor-tracking-stack

# Check enhanced Lambda function logs
sam logs -n URLDiscoveryFunction --stack-name competitor-tracking-stack --tail
sam logs -n SocialMediaFunction --stack-name competitor-tracking-stack --tail
sam logs -n ScrapeCompetitorFunction --stack-name competitor-tracking-stack --tail

# View all stack outputs (should include new function ARNs)
aws cloudformation describe-stacks \
  --stack-name competitor-tracking-stack \
  --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
  --output table
```

### Enhanced Database Connection Issues
```bash
# Test database connectivity with new tables
aws lambda invoke \
  --function-name "competitor-tracking-stack-DatabaseMigrationFunction-XXXXXXXXXX" \
  --payload '{"action": "health_check", "check_new_tables": true}' \
  response.json

cat response.json

# Should confirm new tables exist:
# - competitor_urls
# - social_media_data
```

### New Feature Debugging
```bash
# Debug URL discovery issues
python -c "
import os
import sys
sys.path.insert(0, 'src')

print('🔍 URL Discovery Debug:')
print(f'Cohere API Key: {\"✅\" if os.getenv(\"COHERE_API_KEY\") else \"❌\"}')
print(f'OpenAI API Key: {\"✅\" if os.getenv(\"OPENAI_API_KEY\") else \"⚠️ Fallback\"}')
print(f'SerpAPI Key: {\"✅\" if os.getenv(\"SERPAPI_KEY\") else \"⚠️ Optional\"}')

try:
    from langchain.tools import DuckDuckGoSearchAPIWrapper
    search = DuckDuckGoSearchAPIWrapper()
    print('✅ DuckDuckGo search ready')
except Exception as e:
    print(f'❌ DuckDuckGo search error: {e}')
"

# Debug social media integration
python -c "
import os
import sys
sys.path.insert(0, 'src')

print('📱 Social Media Debug:')
platforms = {
    'Twitter': os.getenv('TWITTER_BEARER_TOKEN'),
    'LinkedIn': os.getenv('LINKEDIN_EMAIL'),
    'Instagram': os.getenv('INSTAGRAM_USERNAME'),
    'TikTok': os.getenv('TIKTOK_ACCESS_TOKEN')
}

for platform, key in platforms.items():
    status = '✅' if key else '⚠️ Optional'
    print(f'{platform}: {status}')
"
```

---

## 🗑️ Cleanup Commands

### Stop Local Development
```bash
# Stop Docker containers
docker-compose down

# Remove volumes (WARNING: deletes all data including new tables)
docker-compose down -v

# Remove images
docker-compose down --rmi all
```

### Delete AWS Resources (Enhanced)
```bash
# Delete CloudFormation stack (WARNING: deletes all AWS resources including new Lambda functions)
sam delete --stack-name competitor-tracking-stack

# OR manually
aws cloudformation delete-stack --stack-name competitor-tracking-stack

# Monitor deletion (will show deletion of new resources)
aws cloudformation describe-stacks --stack-name competitor-tracking-stack
```

---

## 📊 Enhanced Monitoring Commands

### View Lambda Logs (All Functions)
```bash
# Real-time logs for enhanced scraping function
sam logs -n ScrapeCompetitorFunction --stack-name competitor-tracking-stack --tail

# 🆕 Real-time logs for URL discovery function
sam logs -n URLDiscoveryFunction --stack-name competitor-tracking-stack --tail

# 🆕 Real-time logs for social media function
sam logs -n SocialMediaFunction --stack-name competitor-tracking-stack --tail

# Real-time logs for enhanced battle card function
sam logs -n GenerateBattleCardFunction --stack-name competitor-tracking-stack --tail

# Enhanced competitor management logs
sam logs -n CompetitorManagementFunction --stack-name competitor-tracking-stack --tail
```

### Enhanced Database Queries
```bash
# Connect to local database
docker exec -it competitor-tracking-postgres psql -U postgres -d competitordb

# Check enhanced table contents
# SELECT * FROM users;
# SELECT * FROM competitors;
# 
# 🆕 Check new tables:
# SELECT * FROM competitor_urls ORDER BY discovered_at DESC LIMIT 5;
# SELECT * FROM social_media_data ORDER BY fetched_at DESC LIMIT 5;
# 
# Check enhanced scrape results
# SELECT * FROM scrape_results ORDER BY scraped_at DESC LIMIT 5;
# SELECT * FROM battle_cards ORDER BY generated_at DESC LIMIT 5;
#
# 🆕 Check URL discovery statistics:
# SELECT category, COUNT(*), AVG(confidence_score) 
# FROM competitor_urls 
# GROUP BY category;
#
# 🆕 Check social media metrics trends:
# SELECT platform, AVG(followers_count), COUNT(*) 
# FROM social_media_data 
# GROUP BY platform;
```

---

## ✅ Enhanced Quick Validation Checklist

### Local Setup ✓
- [ ] Docker containers running
- [ ] Database connection successful
- [ ] Enhanced migrations completed (new tables created)
- [ ] Test user created
- [ ] Dependencies installed (including new packages)
- [ ] Environment variables configured (including social media keys)
- [ ] URL discovery service functional
- [ ] Social media service functional

### AWS Deployment ✓
- [ ] CloudFormation stack deployed successfully
- [ ] All Lambda functions created (including new ones)
- [ ] RDS instance running
- [ ] API Gateway endpoints accessible (including new endpoints)
- [ ] Enhanced database migration completed
- [ ] Test API calls successful (core + new features)
- [ ] URL discovery endpoints working
- [ ] Social media endpoints working

### 🆕 New Features Validation ✓
- [ ] URL discovery workflow complete
- [ ] Social media integration working
- [ ] Enhanced scraping functional
- [ ] New database tables populated
- [ ] Category-aware scraping working
- [ ] Confidence scoring operational
- [ ] Multi-platform social media fetching
- [ ] Enhanced battle card generation

**🎉 You're all set! Your Enhanced Competitor Tracking SaaS Backend with URL Discovery and Social Media Integration is ready to use.**

## 🚀 Next Steps

### Getting Started with New Features
1. **Create a competitor** with basic info (name + website)
2. **Trigger URL discovery** to find pricing, features, and social pages
3. **Review and confirm** discovered URLs through the API
4. **Fetch social media data** to get follower metrics and engagement
5. **Generate enhanced battle cards** with comprehensive competitive intelligence

### Scaling Recommendations
- **Start with free tier** for initial testing and small competitor sets
- **Upgrade to premium APIs** when tracking 50+ competitors
- **Monitor costs** and adjust API usage based on needs
- **Use hybrid approach** for optimal cost/performance balance

**Your competitive intelligence platform is now powered by AI-driven discovery and comprehensive social media tracking!** 🚀 