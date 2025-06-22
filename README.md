# 🚀 Competitor Tracking SaaS Backend

A **serverless Python backend** for tracking competitor pricing and generating AI-powered competitive intelligence. Built with AWS Lambda, PostgreSQL, and flexible web scraping architecture.

## 🎯 Key Features

- **🕷️ Flexible Web Scraping**: Choose between Playwright (FREE) or ScrapingBee (PAID)
- **🤖 AI Battle Cards**: GPT-4 powered competitive analysis and positioning
- **🔍 Intelligent URL Discovery**: LangChain-powered automatic discovery of competitor pages (NEW)
- **📱 Social Media Integration**: Automated tracking of LinkedIn, Twitter, Instagram, TikTok (NEW)
- **⚡ Serverless Architecture**: AWS Lambda + RDS PostgreSQL for scalability
- **🔄 Automated Scheduling**: Regular competitor monitoring every 6 hours
- **📊 Historical Tracking**: Store and analyze pricing trends over time
- **🎭 Multi-tenant Support**: Built for SaaS with user isolation

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API Gateway   │────│  Lambda Functions │────│  RDS PostgreSQL │
│   (REST API)    │    │   (Handlers)      │    │   (Database)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         └──────────────│  External APIs  │──────────────┘
                        │ • ScrapingBee   │
                        │ • OpenAI GPT-4  │
                        │ • Social Media  │
                        │ • LangChain     │
                        └─────────────────┘
```

## 🆕 NEW: Intelligent URL Discovery & Social Media

### **Automated Competitor Page Discovery**
The system intelligently discovers competitor pages using LangChain with reliable search APIs:
- **Pricing pages**: Automatically find subscription and pricing information
- **Feature pages**: Discover product capabilities and feature comparisons
- **Blog pages**: Locate content marketing and thought leadership
- **Social media**: Find LinkedIn, Twitter, Instagram, and TikTok profiles

### **Robust AI Fallback System**
Enhanced error handling ensures continuous operation even with API failures:
- **Cohere Primary**: Fast, reliable, and cost-effective AI categorization
- **OpenAI Fallback**: Premium quality GPT-4 when Cohere unavailable
- **Pattern Matching**: Final fallback ensures system never fails
- **Smart Error Detection**: Detects quota limits, rate limits, and API failures
- **Optimized Performance**: Faster failure detection and immediate fallback switching

### **Smart Confirmation Workflow**
- URLs discovered with confidence scores
- User review and confirmation interface
- Automatic categorization and validation

### **Enhanced Social Media Tracking**
- **LinkedIn**: Company followers, employee count, recent posts
- **Twitter/X**: Follower metrics, engagement rates, recent tweets
- **Instagram**: Business account metrics, post engagement
- **TikTok**: Video performance, follower growth

## 🕷️ Flexible Scraping Options

| Feature | Playwright (FREE) | ScrapingBee (PAID) |
|---------|-------------------|---------------------|
| **Cost** | $0 | $29-199/month |
| **JavaScript Support** | ✅ Full | ✅ Full |
| **Anti-Bot Detection** | ⚠️ Basic | ✅ Advanced |
| **Proxy Rotation** | ❌ | ✅ Professional |
| **Geographic Targeting** | ❌ | ✅ Available |
| **Memory Usage** | 1GB | 512MB |

**Recommendation**: Start with Playwright (free), upgrade to ScrapingBee if you encounter anti-bot protection.

## 🚀 Quick Start

### Prerequisites
- AWS CLI configured
- Docker installed
- Python 3.9+
- OpenAI API key

### 1. Clone & Setup
```bash
git clone <your-repo-url>
cd slight-backend
cp env.example .env
# Edit .env with your API keys
```

### 2. Local Development
```bash
# Start database
docker-compose up -d postgres

# Install dependencies
cd src && pip install -r requirements.txt
playwright install chromium

# Run tests
python ../scripts/test_local.py

# Test URL discovery (NEW)
python ../scripts/test_url_discovery.py
```

### 3. Deploy to AWS
```bash
# Quick deployment
./scripts/deploy.sh --guided

# Or with parameters
./scripts/deploy.sh \
  --stack-name "competitor-tracking" \
  --region "us-east-1" \
  --db-password "YourPassword123!" \
  --openai-key "sk-your-key"
```

## 📋 API Endpoints

### **Core Endpoints**
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/competitors` | List competitors |
| `POST` | `/competitors` | Create competitor |
| `PUT` | `/competitors/{id}` | Update competitor |
| `DELETE` | `/competitors/{id}` | Delete competitor |
| `POST` | `/scrape` | Trigger scraping |
| `POST` | `/battle-card` | Generate AI analysis |

### **🆕 NEW: URL Discovery Endpoints**
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/competitors/{id}/discover-urls` | Trigger intelligent URL discovery |
| `GET` | `/competitors/{id}/urls` | List discovered URLs |
| `PUT` | `/competitors/{id}/urls` | Confirm/reject discovered URLs |
| `POST` | `/competitors/{id}/scrape-all` | Scrape all confirmed URLs |
| `POST` | `/competitors/{id}/scrape-category` | Scrape specific URL category |

### **🆕 NEW: Social Media Endpoints**
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/competitors/{id}/social-media` | Get social media data |
| `POST` | `/competitors/{id}/social-media` | Fetch fresh social data |
| `POST` | `/competitors/{id}/social-media/{platform}` | Fetch specific platform |

## 🔧 Environment Configuration

```bash
# Database
DATABASE_URL="postgresql+asyncpg://..."

# Scraping (Choose your option)
PREFERRED_SCRAPER="playwright"     # Free option
PREFERRED_SCRAPER="scrapingbee"    # Paid option  
PREFERRED_SCRAPER="auto"           # Smart detection

# API Keys
COHERE_API_KEY="your-cohere-key"   # Primary AI for URL categorization
OPENAI_API_KEY="sk-your-key"       # Fallback AI when Cohere unavailable
SCRAPINGBEE_API_KEY="your-key"     # Optional

# 🆕 NEW: Reliable Search APIs for URL Discovery
GOOGLE_CSE_API_KEY="your-google-cse-api-key"     # Google Custom Search (100 free/day)
GOOGLE_CSE_ID="your-google-cse-id"               # Custom Search Engine ID
BRAVE_API_KEY="your-brave-api-key"               # Brave Search (2000 free/month)
LANGCHAIN_SEARCH_RESULTS_LIMIT="10"              # Search result limit
URL_DISCOVERY_CONFIDENCE_THRESHOLD="0.7"         # Confidence threshold

# 🆕 NEW: Social Media APIs
TWITTER_BEARER_TOKEN="your_twitter_bearer_token"
LINKEDIN_EMAIL="your_linkedin_email"             # For unofficial API
LINKEDIN_PASSWORD="your_linkedin_password"       # For unofficial API
INSTAGRAM_USERNAME="your_instagram_username"     # For unofficial API
INSTAGRAM_PASSWORD="your_instagram_password"     # For unofficial API
TIKTOK_ACCESS_TOKEN="your_tiktok_access_token"
```

## 📊 Usage Examples

### **🆕 Enhanced Workflow with Reliable URL Discovery**

```javascript
// 1. Create competitor
POST /competitors
{
  "name": "Competitor Inc",
  "website": "https://competitor.com",
  "description": "AI-powered SaaS competitor"
}

// 2. Discover URLs using Google Custom Search & Brave Search
POST /competitors/{id}/discover-urls
// Returns: categorized URLs with confidence scores from reliable sources

// 3. User confirms URLs
PUT /competitors/{id}/urls
{
  "confirmations": [
    {"url_id": "uuid1", "status": "confirmed"},
    {"url_id": "uuid2", "status": "rejected"}
  ]
}

// 4. Trigger comprehensive data collection
POST /competitors/{id}/scrape-all
// Scrapes all confirmed URLs + fetches social media data

// 5. Get complete competitive intelligence
GET /competitors/{id}
// Returns: enhanced competitor data with discovered information
```

### Scraping with Auto-Detection
```python
from handlers.scrape_competitor import EnhancedCompetitorScraper

# Automatically chooses best available scraper
async with EnhancedCompetitorScraper() as scraper:
    # Scrape all confirmed URLs
    result = await scraper.scrape_all_competitor_urls(competitor_id)
    
    # Or scrape specific category
    result = await scraper.scrape_by_category(competitor_id, "pricing")
```

### **🆕 Reliable URL Discovery with Cohere-First AI**
```python
from services.url_discovery import URLDiscoveryService

# Initialize with Cohere-first AI strategy
discovery_service = URLDiscoveryService(
    cohere_api_key="your-cohere-key",      # Primary AI
    openai_api_key="sk-...",               # Fallback AI
    google_cse_api_key="your-google-key",
    google_cse_id="your-cse-id",
    brave_api_key="your-brave-key"
)
discovered_urls = await discovery_service.discover_competitor_urls(
    "Competitor Name",
    "https://competitor.com"
)
```

### **🆕 Social Media Integration**
```python
from services.social_media import SocialMediaFetcher

social_fetcher = SocialMediaFetcher(config={
    'TWITTER_BEARER_TOKEN': 'your_token',
    'LINKEDIN_EMAIL': 'your_email'
})

result = await social_fetcher.fetch_all_platforms(competitor_id, social_urls)
```

### Force Specific Scraper
```python
# Use free Playwright
async with CompetitorScraper("playwright") as scraper:
    result = await scraper.scrape_url(url, name)

# Use paid ScrapingBee  
async with CompetitorScraper("scrapingbee") as scraper:
    result = await scraper.scrape_url(url, name)
```

## 🧪 Testing

```bash
# 🆕 Modular URL discovery testing with Cohere-first
python scripts/test_url_discovery_simple.py

# Test all scraping options
python scripts/test_scraping.py

# Test specific scraper
PREFERRED_SCRAPER=playwright python scripts/test_scraping.py

# Test comprehensive URL discovery workflow
python scripts/test_url_discovery.py

# Compare performance
python scripts/test_local.py
```

### **🔧 Modular Test Configuration**
The new `test_url_discovery_simple.py` script offers selectable test modules:

```python
# ✅ QUICK TEST (Default - Recommended for development)
TESTS_TO_RUN = [
    "test_configuration_status",      # Check API keys & service status
    "test_cohere_primary_discovery",  # Full discovery with Cohere-first
]

# 🧠 AI-ONLY TESTS (Uncomment to test just AI categorization)
# TESTS_TO_RUN = ["test_configuration_status", "test_ai_categorization_only"]

# 🔍 SEARCH-ONLY TESTS (Uncomment to test just search backends)  
# TESTS_TO_RUN = ["test_configuration_status", "test_search_backends_only"]

# ⚡ PERFORMANCE COMPARISON (Uncomment to compare AI configurations)
# TESTS_TO_RUN = ["test_configuration_status", "test_performance_comparison"]
```

**Usage**: Simply comment/uncomment the `TESTS_TO_RUN` configuration you want to use.

## 📁 Project Structure

```
├── src/
│   ├── handlers/           # Lambda function handlers
│   │   ├── url_discovery.py      # NEW: URL discovery logic
│   │   ├── social_media.py       # NEW: Social media integration
│   │   └── scrape_competitor.py  # Enhanced with URL discovery
│   ├── services/           # NEW: Business logic services
│   │   ├── url_discovery.py      # LangChain URL discovery
│   │   └── social_media.py       # Social media APIs
│   ├── scrapers/           # Flexible scraping implementations
│   ├── models.py           # Enhanced database models
│   ├── database.py         # Database connections
│   └── requirements.txt    # Updated Python dependencies
├── scripts/                # Deployment and testing scripts
│   └── test_url_discovery.py     # NEW: Comprehensive test suite
├── template.yaml           # AWS SAM template
├── docker-compose.yml      # Local development
├── DOCUMENTATION.md        # Technical documentation
└── RUN.md                  # Setup and deployment guide
```

## 💰 Cost Analysis

### Free Tier (Playwright + Cohere)
- **Scraping**: $0
- **URL Discovery**: ~$0-2/month (Cohere free tier)
- **Lambda**: ~$1-5/month (depends on usage)
- **RDS**: ~$13/month (db.t3.micro)
- **Total**: ~$14-20/month

### Premium Tier (ScrapingBee + Social APIs)
- **Scraping**: $29-199/month
- **URL Discovery**: ~$2-5/month (Cohere + OpenAI fallback)
- **Social Media APIs**: $0-50/month (varies by platform)
- **Lambda**: ~$1-3/month (lower memory usage)
- **RDS**: ~$13/month
- **Total**: ~$45-270/month

## 🔍 Monitoring & Logs

```bash
# View Lambda logs
sam logs -n ScrapeCompetitorFunction --tail

# Check database
docker exec -it postgres psql -U postgres -d competitordb

# Monitor URL discovery jobs
# SELECT * FROM competitor_urls ORDER BY discovered_at DESC;

# Monitor social media data
# SELECT * FROM social_media_data ORDER BY fetched_at DESC;
```

## 🔐 Security Features

- **VPC Isolation**: Database in private subnets
- **IAM Least Privilege**: Minimal required permissions
- **API Key Management**: Secure environment variables
- **Input Validation**: Sanitized database operations
- **Multi-tenant**: User-isolated data access
- **Rate Limiting**: Respectful social media API usage

## 🆕 New Feature Highlights

### **Intelligent URL Discovery**
- **LangChain Integration**: AI-powered web search and analysis
- **Confidence Scoring**: ML-based relevance assessment
- **Sitemap Analysis**: Automated sitemap parsing
- **User Confirmation**: Review workflow for discovered URLs

### **Social Media Intelligence**
- **Multi-Platform Support**: LinkedIn, Twitter, Instagram, TikTok
- **Engagement Metrics**: Detailed performance analytics
- **Historical Tracking**: Monitor follower growth and engagement trends
- **Content Analysis**: Recent posts and engagement patterns

### **Enhanced Scraping**
- **URL-Category Mapping**: Intelligent categorization of scraped content
- **Batch Operations**: Scrape multiple URLs efficiently
- **Enhanced Metadata**: Rich context about scraped data
- **Error Handling**: Graceful failure recovery

## 📚 Documentation

- **[DOCUMENTATION.md](DOCUMENTATION.md)**: Complete technical documentation with new features
- **[RUN.md](RUN.md)**: Updated setup and deployment guide

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly (including new URL discovery tests)
5. Submit a pull request

## 📞 Support

For questions or issues:
1. Check the documentation files
2. Review the testing scripts (including `test_url_discovery.py`)
3. Examine CloudFormation events for deployment issues
4. Check Lambda logs for runtime errors

---

**Built with ❤️ for competitive intelligence and business strategy**