# 🚀 Competitor Tracking SaaS Backend

A **serverless Python backend** for tracking competitor pricing and generating AI-powered competitive intelligence. Built with AWS Lambda, PostgreSQL, and flexible web scraping architecture.

## 🎯 Key Features

- **🕷️ Flexible Web Scraping**: Choose between Playwright (FREE) or ScrapingBee (PAID)
- **🤖 AI Battle Cards**: GPT-4 powered competitive analysis and positioning
- **🔍 Intelligent URL Discovery**: Optimized workflow with confidence validation (NEW)
- **🛡️ Confidence Validation**: Prevents wrong results for lesser-known companies (NEW)
- **📱 Social Media Integration**: Automated tracking of LinkedIn, Twitter, Instagram, TikTok
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
                        │ • Cohere AI     │
                        │ • Social Media  │
                        │ • Search APIs   │
                        └─────────────────┘
```

## 🆕 NEW: Optimized URL Discovery with Confidence Validation

### **Simplified Workflow: Search → LLM Rank → LLM Select**
The system now uses a streamlined 3-step process that's more efficient and reliable:

1. **🔍 Search Engines Do Implicit Categorization**
   - Search "Company pricing" → pricing URLs
   - Search "Company features" → features URLs  
   - Search "Company blog" → blog URLs

2. **🤖 LLM Ranks Top 10 Most Relevant URLs**
   - Analyzes URL paths, titles, descriptions
   - Returns URLs ordered by relevance with confidence scores

3. **🎯 LLM Selects Single Best URL**
   - Chooses most valuable for competitive analysis
   - Returns final URL per category with confidence validation

### **🛡️ Confidence Validation System**
**Problem Solved**: Prevents wrong results for lesser-known companies and startups.

**Multi-Layer Validation**:
- **Brand Recognition**: AI validates if company is well-known enough for reliable results
- **Domain Validation**: Ensures discovered domains actually belong to the company
- **URL Confidence**: LLM can declare "NO_RELEVANT_URLS" if none are suitable
- **Configurable Thresholds**: Adjust precision based on use case

```python
# Conservative (high confidence required)
min_confidence_threshold = 0.8  # Only very confident results

# Balanced (recommended)
min_confidence_threshold = 0.6  # Good balance of coverage and accuracy

# Permissive (exploratory research)
min_confidence_threshold = 0.3  # More results, potentially less reliable
```

**Expected Behavior by Company Type**:
- **🏢 Well-Known Companies** (Notion, Slack): Pass all thresholds (0.8+ confidence)
- **🚀 Emerging Startups** (Cursor, Linear): Pass lower/medium thresholds (0.6-0.8)
- **❓ Unknown/Fictional Companies**: Fail validation entirely (return empty results)

### **🤖 Flexible LLM Selection**
Choose different AI models for each step to optimize cost and quality:

```python
# Cost-effective
ranking_llm="cohere", selection_llm="cohere"

# Hybrid approach  
ranking_llm="cohere", selection_llm="openai"

# Premium quality
ranking_llm="openai", selection_llm="openai"
```

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
- OpenAI API key or Cohere API key

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

# Test optimized URL discovery with confidence validation
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
  --cohere-key "your-cohere-key" \
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

### **🆕 Optimized URL Discovery Endpoints**
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/competitors/{id}/discover-urls` | Trigger optimized URL discovery with confidence validation |
| `GET` | `/competitors/{id}/urls` | List discovered URLs with confidence scores |
| `PUT` | `/competitors/{id}/urls` | Confirm/reject discovered URLs |
| `POST` | `/competitors/{id}/scrape-all` | Scrape all confirmed URLs |
| `POST` | `/competitors/{id}/scrape-category` | Scrape specific URL category |

### **Social Media Endpoints**
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

# 🆕 AI APIs (Cohere-first strategy with OpenAI fallback)
COHERE_API_KEY="your-cohere-key"   # Primary AI for URL discovery (cost-effective)
OPENAI_API_KEY="sk-your-key"       # Fallback AI for premium quality when needed
SCRAPINGBEE_API_KEY="your-key"     # Optional

# 🆕 Enhanced Search APIs for Reliable URL Discovery
GOOGLE_CSE_API_KEY="your-google-cse-api-key"     # Google Custom Search (100 free/day)
GOOGLE_CSE_ID="your-google-cse-id"               # Custom Search Engine ID
BRAVE_API_KEY="your-brave-api-key"               # Brave Search (2000 free/month)

# 🆕 Confidence Validation Settings
URL_DISCOVERY_CONFIDENCE_THRESHOLD="0.6"         # Default confidence threshold
LANGCHAIN_SEARCH_RESULTS_LIMIT="10"              # Search result limit

# Social Media APIs
TWITTER_BEARER_TOKEN="your_twitter_bearer_token"
LINKEDIN_EMAIL="your_linkedin_email"             # For unofficial API
LINKEDIN_PASSWORD="your_linkedin_password"       # For unofficial API
INSTAGRAM_USERNAME="your_instagram_username"     # For unofficial API
INSTAGRAM_PASSWORD="your_instagram_password"     # For unofficial API
TIKTOK_ACCESS_TOKEN="your_tiktok_access_token"
```

## 📊 Usage Examples

### **🆕 Optimized Workflow with Confidence Validation**

```javascript
// 1. Create competitor
POST /competitors
{
  "name": "Emerging Startup",
  "website": "https://startup.com",
  "description": "AI-powered tool for developers"
}

// 2. Discover URLs with confidence validation
POST /competitors/{id}/discover-urls
{
  "search_depth": "standard",
  "categories": ["pricing", "features", "blog"],
  "ranking_llm": "cohere",
  "selection_llm": "cohere", 
  "min_confidence_threshold": 0.6  // Balanced approach
}

// Response includes confidence scores:
{
  "discovered_urls": [
    {
      "url": "https://startup.com/pricing",
      "category": "pricing",
      "confidence_score": 0.85,
      "brand_confidence": 0.80,
      "ranking_confidence": 0.90,
      "selection_confidence": 0.85
    }
  ]
}

// 3. System automatically filters out low-confidence results
// Better to return no data than wrong data for unknown companies
```

### **🛡️ Confidence Validation Examples**

```python
# Well-known company (high confidence)
urls = await discover_urls("Notion", threshold=0.8)  # ✅ Returns results

# Emerging startup (medium confidence)  
urls = await discover_urls("Cursor", threshold=0.6)  # ✅ Returns results
urls = await discover_urls("Cursor", threshold=0.8)  # ⚠️ May filter some results

# Unknown company (low confidence)
urls = await discover_urls("FakeStartup", threshold=0.6)  # ❌ Returns empty (protected)
```

### **🤖 LLM Selection Optimization**

```python
# Cost-effective approach
discovered_urls = await service.discover_competitor_urls(
    competitor_name="Company",
    ranking_llm="cohere",      # Fast and cheap for ranking
    selection_llm="cohere",    # Consistent quality
    min_confidence_threshold=0.6
)

# Premium quality approach  
discovered_urls = await service.discover_competitor_urls(
    competitor_name="Company", 
    ranking_llm="openai",      # Premium ranking
    selection_llm="openai",    # Premium selection
    min_confidence_threshold=0.7
)
```

## 🧪 Testing

```bash
# 🆕 Test optimized URL discovery with confidence validation
python scripts/test_url_discovery.py

# 🆕 Test confidence validation specifically
python scripts/test_confidence_validation.py

# 🆕 Test LLM combinations and confidence thresholds
python scripts/test_url_discovery_simple.py

# Test all scraping options
python scripts/test_scraping.py

# Test comprehensive workflow
python scripts/test_local.py
```

### **🔧 Test Configuration Examples**
```python
# Test different confidence levels
CONFIDENCE_THRESHOLDS = [0.3, 0.6, 0.8]  # Low, Medium, High

# Test different company types
TEST_COMPANIES = [
    ("Notion", "https://notion.so", "HIGH_CONFIDENCE"),      # Well-known
    ("Cursor", "https://cursor.com", "MEDIUM_CONFIDENCE"),   # Startup
    ("FakeXYZ", "https://fakexyz.com", "LOW_CONFIDENCE")     # Unknown
]
```

## 📁 Project Structure

```
├── src/
│   ├── handlers/           # Lambda function handlers
│   │   ├── url_discovery.py      # Optimized URL discovery logic
│   │   ├── social_media.py       # Social media integration
│   │   └── scrape_competitor.py  # Enhanced with URL discovery
│   ├── services/           # Business logic services
│   │   ├── url_discovery.py      # Optimized workflow with confidence validation
│   │   └── social_media.py       # Social media APIs
│   ├── scrapers/           # Flexible scraping implementations
│   ├── models.py           # Enhanced database models
│   ├── database.py         # Database connections
│   └── requirements.txt    # Updated Python dependencies
├── scripts/                # Deployment and testing scripts
│   ├── test_url_discovery.py         # Comprehensive test suite
│   ├── test_confidence_validation.py # Confidence validation tests
│   └── test_url_discovery_simple.py  # LLM combination tests
├── template.yaml           # AWS SAM template
├── docker-compose.yml      # Local development
├── CONFIDENCE_VALIDATION.md # 🆕 Confidence validation documentation
├── DOCUMENTATION.md        # Technical documentation
└── RUN.md                  # Setup and deployment guide
```

## 💰 Cost Analysis

### Free Tier (Playwright + Cohere)
- **Scraping**: $0
- **URL Discovery**: ~$0-2/month (Cohere free tier + confidence validation)
- **Lambda**: ~$1-5/month (depends on usage)
- **RDS**: ~$13/month (db.t3.micro)
- **Total**: ~$14-20/month

### Premium Tier (ScrapingBee + OpenAI)
- **Scraping**: $29-199/month
- **URL Discovery**: ~$2-5/month (Cohere + OpenAI fallback)
- **Social Media APIs**: $0-50/month (varies by platform)
- **Lambda**: ~$1-3/month (optimized workflow)
- **RDS**: ~$13/month
- **Total**: ~$45-270/month

### **🆕 Hybrid Tier (Recommended)**
- **Scraping**: Playwright (free) with ScrapingBee fallback
- **URL Discovery**: Cohere-first with OpenAI for critical selections
- **Confidence Validation**: Prevents wasted API calls on unknown companies
- **Total**: ~$20-70/month (optimal cost/performance)

## 🔍 Monitoring & Logs

```bash
# View Lambda logs
sam logs -n URLDiscoveryFunction --tail

# Check confidence validation metrics
# SELECT category, AVG(confidence_score), COUNT(*) 
# FROM competitor_urls 
# WHERE confidence_score >= 0.6
# GROUP BY category;

# Monitor filtered results (protected from wrong data)
# SELECT COUNT(*) as filtered_results
# FROM discovery_logs 
# WHERE status = 'filtered_low_confidence';
```

## 🔐 Security Features

- **VPC Isolation**: Database in private subnets
- **IAM Least Privilege**: Minimal required permissions
- **API Key Management**: Secure environment variables
- **Input Validation**: Sanitized database operations
- **Multi-tenant**: User-isolated data access
- **Confidence Validation**: Prevents data pollution from unreliable sources

## 🆕 New Feature Highlights

### **Optimized URL Discovery Workflow**
- **3-Step Process**: Search → LLM Rank → LLM Select (simplified from complex batching)
- **Implicit Categorization**: Search engines handle categorization naturally
- **Flexible LLM Selection**: Choose different models for ranking vs selection
- **Performance Optimized**: Reduced API calls and faster processing

### **Confidence Validation System**
- **Brand Recognition**: AI validates if company is well-known enough
- **Multi-Layer Confidence**: Brand, ranking, and selection confidence scores
- **Configurable Thresholds**: Adjust precision based on use case
- **Graceful Degradation**: Clear feedback when results are filtered

### **Enhanced Error Handling**
- **Smart Fallbacks**: Cohere → OpenAI → Pattern matching
- **Early Filtering**: Avoid expensive searches for unrecognized brands
- **Transparent Confidence**: Users see why results were filtered

## 📚 Documentation

- **[CONFIDENCE_VALIDATION.md](CONFIDENCE_VALIDATION.md)**: 🆕 Comprehensive guide to confidence validation
- **[DOCUMENTATION.md](DOCUMENTATION.md)**: Complete technical documentation
- **[RUN.md](RUN.md)**: Updated setup and deployment guide

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly (including confidence validation tests)
5. Submit a pull request

## 📞 Support

For questions or issues:
1. Check the confidence validation documentation
2. Review the testing scripts (especially confidence validation tests)
3. Examine CloudFormation events for deployment issues
4. Check Lambda logs for runtime errors

---

**Built with ❤️ for reliable competitive intelligence**
**🛡️ Now with confidence validation to prevent wrong results for lesser-known companies**