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
- **Cohere API Key** (Recommended): Get from https://cohere.ai/
  - Primary AI for cost-effective URL discovery and confidence validation
- **OpenAI API Key**: Get from https://platform.openai.com/api-keys
  - Fallback AI for premium quality when needed
- **ScrapingBee API Key** (Optional): Get from https://app.scrapingbee.com/
  - Only needed if you want to use premium scraping features
  - System defaults to free Playwright scraper

### 🆕 NEW: Enhanced API Keys for Optimized URL Discovery
- **Google Custom Search API Key**: Get from https://console.developers.google.com/
  - High-quality search results (100 free queries/day)
- **Brave Search API Key**: Get from https://api.search.brave.com/
  - Independent search index (2,000 free queries/month)
- **Twitter Bearer Token**: Get from https://developer.twitter.com/
- **LinkedIn Credentials**: For unofficial API access (use carefully)
- **Instagram Credentials**: For business account metrics
- **TikTok Access Token**: Get from https://developers.tiktok.com/

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

# 🆕 Enhanced AI Configuration (Cohere-first strategy)
COHERE_API_KEY="your-cohere-api-key"         # Primary AI for URL discovery (cost-effective)
OPENAI_API_KEY="sk-your-actual-openai-key"   # Fallback AI for premium quality

# Scraping Configuration (Flexible Architecture)
PREFERRED_SCRAPER="playwright"          # Free option
PREFERRED_SCRAPER="scrapingbee"    # Paid option  
PREFERRED_SCRAPER="auto"           # Smart detection
SCRAPINGBEE_API_KEY="your-scrapingbee-key"  # Only needed if using ScrapingBee

# 🆕 Enhanced URL Discovery Configuration
GOOGLE_CSE_API_KEY="your-google-cse-api-key"         # Google Custom Search (100 free/day)
GOOGLE_CSE_ID="your-google-cse-id"                   # Custom Search Engine ID
BRAVE_API_KEY="your-brave-api-key"                   # Brave Search (2,000 free/month)
LANGCHAIN_SEARCH_RESULTS_LIMIT="10"                  # Search result limit

# 🆕 Confidence Validation Settings
URL_DISCOVERY_CONFIDENCE_THRESHOLD="0.6"             # Default confidence threshold (0.0-1.0)
# 0.8 = Conservative (high confidence required)
# 0.6 = Balanced (recommended for most use cases)
# 0.3 = Permissive (more results, potentially less reliable)

# Social Media API Keys
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

**🆕 Enhanced URL Discovery Options:**
- **Optimized Workflow**: Search → LLM Rank → LLM Select (simplified from complex batching)
- **Confidence Validation**: Prevents wrong results for lesser-known companies
- **Flexible LLM Selection**: Choose different AI models for ranking vs selection
- **Google Custom Search**: Premium quality search (100 free queries/day)
- **Brave Search API**: Independent search index (2,000 free queries/month)
- **Cohere-first AI**: Cost-effective AI with OpenAI fallback for premium quality

**🛡️ Confidence Validation Benefits:**
- **Brand Recognition**: AI validates if company is well-known enough for reliable results
- **Multi-Layer Confidence**: Brand, ranking, and selection confidence scores
- **Configurable Thresholds**: Adjust precision based on use case (0.3-0.8)
- **Graceful Degradation**: Returns empty results rather than wrong data for unknown companies

**Social Media Integration:**
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

# Install dependencies (includes enhanced packages)
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
- **AI/Search**: OpenAI, Cohere (primary), google-search-results
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
# ✅ URL discovery service ready (optimized workflow)
# ✅ Social media service ready
# ✅ All tests passed!
```

### Step 7: 🆕 Test Optimized URL Discovery & Confidence Validation
```bash
# Test the optimized URL discovery workflow with confidence validation
python ../scripts/test_url_discovery.py

# Test confidence validation specifically (different company types)
python ../scripts/test_confidence_validation.py

# Test LLM combinations and confidence thresholds
python ../scripts/test_url_discovery_simple.py

# Expected output:
# 🔍 Testing Optimized URL Discovery Service:
# ✅ Cohere AI ready (primary)
# ✅ OpenAI ready (fallback)
# ✅ Google Custom Search working
# ✅ Brave Search API working
# ✅ Confidence validation working
# 
# 🛡️ Testing Confidence Validation:
# ✅ Well-known companies: Pass all thresholds
# ✅ Emerging startups: Pass lower/medium thresholds
# ✅ Unknown companies: Filtered out (protected from wrong results)
# 
# 📱 Testing Social Media Integration:
# ✅ Twitter API ready (if token provided)
# ✅ LinkedIn API ready (if credentials provided)
# ✅ Instagram API ready (if credentials provided)
# ✅ TikTok API ready (if token provided)
# 
# 💾 Testing Enhanced Database Models:
# ✅ CompetitorUrl model with confidence scores
# ✅ SocialMediaData model created
# ✅ Enhanced relationships working
# 
# 🔄 Testing End-to-End Optimized Workflow:
# ✅ Optimized URL discovery pipeline
# ✅ Confidence validation filtering
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

# Test optimized URL discovery service with confidence validation
python -c "
import asyncio
import sys
sys.path.insert(0, '.')
from services.url_discovery import URLDiscoveryService
import os

async def test_discovery():
    if os.getenv('COHERE_API_KEY') or os.getenv('OPENAI_API_KEY'):
        service = URLDiscoveryService(
            cohere_api_key=os.getenv('COHERE_API_KEY'),
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            brave_api_key=os.getenv('BRAVE_API_KEY')
        )
        
        # Test with different confidence thresholds
        for threshold in [0.3, 0.6, 0.8]:
            print(f'🎯 Testing confidence threshold: {threshold}')
            urls = await service.discover_competitor_urls(
                'Cursor', 
                'https://cursor.com',
                min_confidence_threshold=threshold
            )
            if urls:
                print(f'✅ Found {len(urls)} URLs (confidence >= {threshold})')
                for url in urls[:2]:  # Show first 2
                    conf = url.get('confidence_score', 0)
                    print(f'  - {url.get('category')}: {url.get('url')} (confidence: {conf:.2f})')
            else:
                print(f'⚠️ No URLs met confidence threshold {threshold}')
    else:
        print('❌ Cohere or OpenAI API key required for URL discovery')

asyncio.run(test_discovery())
"

# Test confidence validation for different company types
python -c "
import asyncio
import sys
sys.path.insert(0, '.')
from services.url_discovery import URLDiscoveryService
import os

async def test_companies():
    if os.getenv('COHERE_API_KEY') or os.getenv('OPENAI_API_KEY'):
        service = URLDiscoveryService(
            cohere_api_key=os.getenv('COHERE_API_KEY'),
            openai_api_key=os.getenv('OPENAI_API_KEY')
        )
        
        companies = [
            ('Notion', 'https://notion.so', 'Well-known'),
            ('Cursor', 'https://cursor.com', 'Emerging startup'),
            ('FakeCompanyXYZ', 'https://fakecompanyxyz.com', 'Unknown/fictional')
        ]
        
        for name, url, type_desc in companies:
            print(f🔍 Testing {name} ({type_desc})')
            try:
                validation = await service._validate_brand_recognition(name, url)
                recognized = validation['is_recognized']
                confidence = validation['confidence']
                reason = validation['reason']
                
                status = '✅' if recognized else '❌'
                print(f'   {status} Recognized: {recognized} (confidence: {confidence:.2f})')
                print(f'   💭 Reason: {reason}')
            except Exception as e:
                print(f'   ❌ Error: {e}')
    else:
        print('❌ AI API key required for brand recognition validation')

asyncio.run(test_companies())
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
# - API keys (including new Cohere and confidence validation settings)
# - Deployment preferences
```

### Step 3: Direct Deployment with Enhanced Parameters
```bash
# Deploy with optimized URL discovery (Cohere-first)
./scripts/deploy.sh \
  --stack-name "competitor-tracking-prod" \
  --region "us-east-1" \
  --db-password "YourSecurePassword123!" \
  --cohere-key "your-cohere-api-key" \
  --openai-key "sk-your-openai-api-key" \
  --confidence-threshold "0.6"

# Deploy with enhanced search capabilities
./scripts/deploy.sh \
  --stack-name "competitor-tracking-prod" \
  --region "us-east-1" \
  --db-password "YourSecurePassword123!" \
  --cohere-key "your-cohere-api-key" \
  --google-cse-key "your-google-cse-key" \
  --google-cse-id "your-google-cse-id" \
  --brave-key "your-brave-api-key"

# Deploy with full social media integration
./scripts/deploy.sh \
  --stack-name "competitor-tracking-prod" \
  --region "us-east-1" \
  --db-password "YourSecurePassword123!" \
  --cohere-key "your-cohere-api-key" \
  --openai-key "sk-your-openai-api-key" \
  --twitter-token "your-twitter-bearer-token" \
  --linkedin-email "your-linkedin-email" \
  --linkedin-password "your-linkedin-password" \
  --scrapingbee-key "your-scrapingbee-key"
```

**💡 Enhanced Deployment Notes:**
- **Lambda Memory**: Optimized for different features (1GB for URL discovery, 512MB for social media)
- **Lambda Timeout**: Increased to 90s for complex URL discovery operations
- **Environment Variables**: Automatically configured for optimized workflow and confidence validation
- **Database Schema**: Enhanced migrations run automatically on first deployment
- **Confidence Validation**: Default threshold of 0.6 (configurable via environment variable)

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
    CohereApiKey="your-cohere-api-key" \
    OpenAIApiKey="sk-your-openai-api-key" \
    ScrapingBeeApiKey="your-scrapingbee-api-key" \
    TwitterBearerToken="your-twitter-token" \
    LinkedInEmail="your-linkedin-email" \
    LinkedInPassword="your-linkedin-password" \
    GoogleCSEApiKey="your-google-cse-key" \
    GoogleCSEId="your-google-cse-id" \
    BraveApiKey="your-brave-api-key" \
    ConfidenceThreshold="0.6" \
  --no-confirm-changeset
```

### Step 5: Initialize Production Database (Enhanced)
```bash
# Get the migration function name from CloudFormation outputs
aws cloudformation describe-stacks \
  --stack-name competitor-tracking-stack \
  --query 'Stacks[0].Outputs[?OutputKey==`DatabaseMigrationFunction`].OutputValue' \
  --output text

# Run enhanced database migration (includes new tables with confidence validation)
aws lambda invoke \
  --function-name "competitor-tracking-stack-DatabaseMigrationFunction-XXXXXXXXXX" \
  --payload '{"action": "create_test_user"}' \
  response.json

# Check response
cat response.json

# Expected to see new tables created:
# - competitors (enhanced with confidence tracking)
# - competitor_urls (with confidence_score column)
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

# 🆕 Test optimized URL discovery endpoint with confidence validation
curl -X POST "$API_URL/competitors/test-competitor-id/discover-urls" \
  -H "Content-Type: application/json" \
  -d '{
    "search_depth": "standard",
    "categories": ["pricing", "features"],
    "ranking_llm": "cohere",
    "selection_llm": "cohere",
    "min_confidence_threshold": 0.6
  }'

# Test social media endpoint
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

# 1. List competitors (enhanced with confidence validation status)
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

# 3. Generate enhanced battle card (with discovered URLs and confidence scores)
curl -X POST "$API_URL/battle-card" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "generate",
    "user_id": "YOUR_USER_ID"
  }'
```

### 🆕 Test Optimized URL Discovery Endpoints
```bash
COMPETITOR_ID="your-competitor-id"

# 1. Trigger optimized URL discovery with confidence validation
curl -X POST "$API_URL/competitors/$COMPETITOR_ID/discover-urls" \
  -H "Content-Type: application/json" \
  -d '{
    "search_depth": "standard",
    "categories": ["pricing", "features", "blog"],
    "ranking_llm": "cohere",
    "selection_llm": "cohere",
    "min_confidence_threshold": 0.6
  }'

# 2. Get discovered URLs with confidence scores
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

### Test Social Media Endpoints
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

# 🆕 Test enhanced scraping with optimized URL discovery
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
        print(f🧪 Testing {category} page: {url}')
        
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
# Calculate monthly costs for different scenarios (updated with confidence validation)
python -c "
print('💰 Enhanced Cost Analysis (per month):')
print()
print('🆓 FREE TIER (Optimized Workflow):')
print('   • Scraping: Playwright ($0)')
print('   • URL Discovery: Cohere free tier (~$0-2)')
print('   • Confidence Validation: Included (prevents wasted API calls)')
print('   • Social Media: Free tier APIs (~$0)')
print('   • Lambda: ~$1-3 (optimized performance)')
print('   • RDS: ~$13 (db.t3.micro)')
print('   • Total: ~$14-18')
print()
print('💎 PREMIUM TIER (All Features):')
print('   • Scraping: ScrapingBee ($29-199)')
print('   • URL Discovery: Cohere + OpenAI fallback (~$3-10)')
print('   • Confidence Validation: Included (improves accuracy)')
print('   • Social Media: Paid APIs (~$0-50)')
print('   • Lambda: ~$2-5 (higher usage)')
print('   • RDS: ~$13-25 (depends on usage)')
print('   • Total: ~$47-289')
print()
print('🎯 HYBRID APPROACH (Recommended):')
print('   • Scraping: Playwright (free) with ScrapingBee fallback')
print('   • URL Discovery: Cohere-first with OpenAI for critical selections')
print('   • Confidence Validation: Prevents costs on unknown companies')
print('   • Social Media: Mix of free and paid APIs')
print('   • Total: ~$18-65 (optimal cost/performance)')
print()
print('📊 Break-even Analysis:')
print('   • Premium worth it if: >100 competitors tracked')
print('   • Free tier sufficient for: <50 competitors')
print('   • Hybrid optimal for: 20-100 competitors')
print('   • Confidence validation saves 20-40% on API costs for unknown brands')
"
```

---

## 🔧 Troubleshooting Commands (Enhanced)

### Local Development Issues
```bash
# Check Docker containers
docker-compose ps
docker-compose logs postgres

# Check database connection and new tables with confidence validation
docker exec -it competitor-tracking-postgres psql -U postgres -d competitordb -c "
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;
"

# Should show enhanced tables:
# - battle_cards
# - competitor_urls (with confidence_score column)
# - competitors (enhanced)
# - scrape_jobs
# - scrape_results
# - social_media_data
# - users

# Test confidence validation services individually
python -c "
import sys
sys.path.insert(0, 'src')

# Test optimized URL discovery service
try:
    from services.url_discovery import URLDiscoveryService
    print('✅ Optimized URL Discovery service imports successfully')
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

# View CloudFormation events (check for new Lambda functions with confidence validation)
aws cloudformation describe-stack-events --stack-name competitor-tracking-stack

# Check enhanced Lambda function logs
sam logs -n URLDiscoveryFunction --stack-name competitor-tracking-stack --tail
sam logs -n SocialMediaFunction --stack-name competitor-tracking-stack --tail
sam logs -n ScrapeCompetitorFunction --stack-name competitor-tracking-stack --tail

# View all stack outputs (should include new function ARNs and confidence validation settings)
aws cloudformation describe-stacks \
  --stack-name competitor-tracking-stack \
  --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
  --output table
```

### Enhanced Database Connection Issues
```bash
# Test database connectivity with confidence validation tables
aws lambda invoke \
  --function-name "competitor-tracking-stack-DatabaseMigrationFunction-XXXXXXXXXX" \
  --payload '{"action": "health_check", "check_confidence_validation": true}' \
  response.json

cat response.json

# Should confirm confidence validation tables exist:
# - competitor_urls (with confidence_score, brand_confidence columns)
# - social_media_data
```

### Confidence Validation Debugging
```bash
# Debug confidence validation issues
python -c "
import os
import sys
sys.path.insert(0, 'src')

print('🛡️ Confidence Validation Debug:')
print(f'Cohere API Key: {\"✅\" if os.getenv(\"COHERE_API_KEY\") else \"❌\"}')
print(f'OpenAI API Key: {\"✅\" if os.getenv(\"OPENAI_API_KEY\") else \"⚠️ Fallback\"}')
print(f'Google CSE Key: {\"✅\" if os.getenv(\"GOOGLE_CSE_API_KEY\") else \"⚠️ Optional\"}')
print(f'Brave API Key: {\"✅\" if os.getenv(\"BRAVE_API_KEY\") else \"⚠️ Optional\"}')
print(f'Confidence Threshold: {os.getenv(\"URL_DISCOVERY_CONFIDENCE_THRESHOLD\", \"0.6\")}')

try:
    from services.url_discovery import URLDiscoveryService
    service = URLDiscoveryService(
        cohere_api_key=os.getenv('COHERE_API_KEY'),
        openai_api_key=os.getenv('OPENAI_API_KEY')
    )
    print('✅ URL Discovery service with confidence validation ready')
except Exception as e:
    print(f'❌ Confidence validation setup error: {e}')
"

# Debug optimized workflow
python -c "
import os
import sys
sys.path.insert(0, 'src')

print('🔍 Optimized Workflow Debug:')
search_backends = []
if os.getenv('GOOGLE_CSE_API_KEY'):
    search_backends.append('Google Custom Search')
if os.getenv('BRAVE_API_KEY'):
    search_backends.append('Brave Search')

print(f'Available search backends: {search_backends}')
print(f'LLM options: Cohere (primary), OpenAI (fallback)')
print(f'Workflow: Search → LLM Rank → LLM Select → Confidence Filter')
"
```

---

## 🗑️ Cleanup Commands

### Stop Local Development
```bash
# Stop Docker containers
docker-compose down

# Remove volumes (WARNING: deletes all data including confidence validation tables)
docker-compose down -v

# Remove images
docker-compose down --rmi all
```

### Delete AWS Resources (Enhanced)
```bash
# Delete CloudFormation stack (WARNING: deletes all AWS resources including confidence validation functions)
sam delete --stack-name competitor-tracking-stack

# OR manually
aws cloudformation delete-stack --stack-name competitor-tracking-stack

# Monitor deletion (will show deletion of enhanced resources)
aws cloudformation describe-stacks --stack-name competitor-tracking-stack
```

---

## 📊 Enhanced Monitoring Commands

### View Lambda Logs (All Functions)
```bash
# Real-time logs for enhanced scraping function
sam logs -n ScrapeCompetitorFunction --stack-name competitor-tracking-stack --tail

# 🆕 Real-time logs for optimized URL discovery function
sam logs -n URLDiscoveryFunction --stack-name competitor-tracking-stack --tail

# Real-time logs for social media function
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

# Check enhanced table contents with confidence validation
# SELECT * FROM users;
# SELECT * FROM competitors;
# 
# 🆕 Check confidence validation tables:
# SELECT * FROM competitor_urls ORDER BY discovered_at DESC LIMIT 5;
# SELECT category, AVG(confidence_score), COUNT(*) 
# FROM competitor_urls 
# WHERE confidence_score >= 0.6
# GROUP BY category;
# 
# Check confidence validation effectiveness:
# SELECT 
#   COUNT(*) as total_discoveries,
#   COUNT(CASE WHEN confidence_score >= 0.6 THEN 1 END) as high_confidence,
#   COUNT(CASE WHEN confidence_score < 0.6 THEN 1 END) as filtered_out
# FROM competitor_urls;
# 
# Check social media metrics trends:
# SELECT platform, AVG(followers_count), COUNT(*) 
# FROM social_media_data 
# GROUP BY platform;
#
# Check enhanced scrape results
# SELECT * FROM scrape_results ORDER BY scraped_at DESC LIMIT 5;
# SELECT * FROM battle_cards ORDER BY generated_at DESC LIMIT 5;
```

---

## ✅ Enhanced Quick Validation Checklist

### Local Setup ✓
- [ ] Docker containers running
- [ ] Database connection successful
- [ ] Enhanced migrations completed (confidence validation tables created)
- [ ] Test user created
- [ ] Dependencies installed (including Cohere and enhanced packages)
- [ ] Environment variables configured (including confidence validation settings)
- [ ] Optimized URL discovery service functional
- [ ] Confidence validation working
- [ ] Social media service functional

### AWS Deployment ✓
- [ ] CloudFormation stack deployed successfully
- [ ] All Lambda functions created (including optimized URL discovery)
- [ ] RDS instance running
- [ ] API Gateway endpoints accessible (including confidence validation endpoints)
- [ ] Enhanced database migration completed
- [ ] Test API calls successful (core + optimized features)
- [ ] Optimized URL discovery endpoints working
- [ ] Confidence validation filtering working
- [ ] Social media endpoints working

### 🆕 Confidence Validation Features ✓
- [ ] Brand recognition validation working
- [ ] Domain validation functional
- [ ] URL ranking confidence assessment operational
- [ ] URL selection confidence validation working
- [ ] Configurable confidence thresholds functional
- [ ] Multi-layer confidence scoring working
- [ ] Graceful degradation for unknown companies
- [ ] Enhanced database tables populated with confidence scores

**🎉 You're all set! Your Enhanced Competitor Tracking SaaS Backend with Optimized URL Discovery and Confidence Validation is ready to use.**

## 🚀 Next Steps

### Getting Started with Enhanced Features
1. **Create a competitor** with basic info (name + website)
2. **Trigger optimized URL discovery** with confidence validation to find reliable competitive intelligence
3. **Review confidence scores** to understand data reliability
4. **Adjust confidence thresholds** based on your use case (0.3-0.8)
5. **Fetch social media data** to get comprehensive competitive insights
6. **Generate enhanced battle cards** with reliable, confidence-validated data

### Scaling Recommendations
- **Start with balanced confidence threshold (0.6)** for most use cases
- **Use conservative threshold (0.8)** for critical business decisions
- **Use permissive threshold (0.3)** for exploratory research
- **Monitor filtered results** to understand confidence validation effectiveness
- **Upgrade to premium APIs** when tracking 50+ competitors
- **Use hybrid approach** for optimal cost/performance balance

**Your competitive intelligence platform now provides reliable results while protecting against wrong data for lesser-known companies!** 🛡️ 🚀 