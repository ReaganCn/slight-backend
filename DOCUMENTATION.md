# 📚 Technical Documentation

Complete technical documentation for the Competitor Tracking SaaS Backend, explaining the architecture, file structure, and entry points for each feature.

---

## 🏗️ Architecture Overview

The system follows a **serverless microservices architecture** with the following components:

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
                        │ • LangChain     │
                        │ • Social Media  │
                        │ • DuckDuckGo    │
                        └─────────────────┘
```

**Data Flow:**
1. **API Gateway** receives HTTP requests
2. **Lambda Functions** process business logic
3. **Services Layer** handles complex operations (URL discovery, social media)
4. **Database Layer** handles data persistence
5. **External APIs** provide scraping, AI, and social media capabilities

---

## 📂 File Structure & Components

### **🔧 Infrastructure as Code**

#### `template.yaml` - **Main Infrastructure Definition**
**Purpose:** AWS SAM template defining all cloud resources
**Entry Point:** `sam deploy` command

**Key Resources Defined:**
- **VPC & Networking**: Custom VPC, subnets, security groups
- **RDS PostgreSQL**: Database instance with proper security
- **Lambda Functions**: All serverless functions with VPC config
- **API Gateway**: RESTful endpoints with CORS
- **IAM Roles**: Least-privilege security policies

**Critical Sections:**
```yaml
# Database Definition
CompetitorDB:
  Type: AWS::RDS::DBInstance
  Properties:
    Engine: postgres
    DBInstanceClass: db.t3.micro

# Lambda Function Example
ScrapeCompetitorFunction:
  Type: AWS::Serverless::Function
  Properties:
    CodeUri: src/
    Handler: handlers.scrape_competitor.handler
```

---

### **💾 Database Layer**

#### `src/models.py` - **Enhanced Data Models & Schema**
**Purpose:** SQLAlchemy ORM models defining database schema
**Entry Point:** Imported by all handlers for database operations

**Core Models:**
- **`User`**: Multi-tenant user management
- **`Competitor`**: Competitor profiles and scraping configuration
- **`ScrapeResult`**: Historical pricing/feature data (JSONB storage)
- **`BattleCard`**: AI-generated competitive intelligence
- **`ScrapeJob`**: Job tracking and status monitoring

**🆕 NEW: Enhanced Models:**
- **`CompetitorUrl`**: Discovered URLs with confidence scores and categories
- **`SocialMediaData`**: Social media metrics and engagement data

**Enhanced Competitor Model:**
```python
class Competitor(Base):
    __tablename__ = "competitors"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Core fields
    name = Column(String(200), nullable=False)
    website = Column(String(500))
    
    # URL Discovery Status
    url_discovery_status = Column(String(50), default="pending")
    url_discovery_last_run = Column(DateTime(timezone=True))
    
    # Relationships
    scrape_results = relationship("ScrapeResult", back_populates="competitor")
    urls = relationship("CompetitorUrl", back_populates="competitor")
    social_media_data = relationship("SocialMediaData", back_populates="competitor")
```

**CompetitorUrl Model:**
```python
class CompetitorUrl(Base):
    __tablename__ = "competitor_urls"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    competitor_id = Column(UUID(as_uuid=True), ForeignKey("competitors.id"))
    
    # URL Information
    url = Column(String(1000), nullable=False)
    category = Column(String(100))  # pricing, features, blog, social, etc.
    confidence_score = Column(Float)
    
    # Status Management
    status = Column(String(50), default="pending")  # pending, confirmed, rejected
    discovered_at = Column(DateTime(timezone=True), default=func.now())
    
    # Discovery Metadata
    discovery_method = Column(String(100))  # search, sitemap, ai_analysis
    page_title = Column(String(500))
    page_description = Column(Text)
```

**SocialMediaData Model:**
```python
class SocialMediaData(Base):
    __tablename__ = "social_media_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    competitor_id = Column(UUID(as_uuid=True), ForeignKey("competitors.id"))
    
    # Platform Information
    platform = Column(String(50), nullable=False)  # linkedin, twitter, instagram, tiktok
    profile_url = Column(String(500))
    username = Column(String(200))
    
    # Metrics
    followers_count = Column(Integer)
    following_count = Column(Integer)
    posts_count = Column(Integer)
    engagement_rate = Column(Float)
    
    # Profile Data
    profile_data = Column(JSON)  # Flexible storage for platform-specific data
    recent_posts = Column(JSON)  # Recent posts with engagement metrics
    
    # Metadata
    fetched_at = Column(DateTime(timezone=True), default=func.now())
    fetch_status = Column(String(50), default="success")
```

#### `src/database.py` - **Database Connection Management**
**Purpose:** Async database connections and session management
**Entry Point:** Imported by all handlers for database access

**Key Functions:**
- **`get_session()`**: Async context manager for database sessions
- **`ensure_connection()`**: Connection retry logic for Lambda cold starts
- **`init_database()`**: Schema creation and migrations
- **Utility functions**: Common database operations

**Usage Pattern:**
```python
async with get_session() as session:
    result = await session.execute(select(Competitor))
    competitors = result.scalars().all()
```

---

### **🆕 Services Layer (NEW)**

#### `src/services/url_discovery.py` - **Intelligent URL Discovery Service**
**Purpose:** LangChain-powered automatic discovery of competitor URLs with Cohere-first AI strategy
**Entry Point:** Used by URL discovery handler

**Key Features:**
- **Google Custom Search**: High-quality search results (100 free queries/day)
- **Brave Search API**: Independent search index (2,000 free queries/month)
- **Sitemap Analysis**: Automated sitemap parsing and categorization
- **Confidence Scoring**: ML-based relevance assessment for discovered URLs
- **Category Detection**: Automatic categorization (pricing, features, blog, social)
- **Cohere-First AI**: Fast, reliable AI categorization with OpenAI fallback
- **Smart Error Handling**: Intelligent quota detection and immediate fallback switching

**Core Class:**
```python
class URLDiscoveryService:
    def __init__(self, cohere_api_key: str = None,
                 openai_api_key: str = None, 
                 google_cse_api_key: str = None,
                 google_cse_id: str = None,
                 brave_api_key: str = None):
        # Cohere-first AI strategy with OpenAI fallback
        self.cohere_llm = ChatCohere(model="command-r-08-2024", cohere_api_key=cohere_api_key)
        self.openai_llm = ChatOpenAI(model="gpt-4", api_key=openai_api_key, max_retries=1)
        self._init_search_tools()  # Initialize Google CSE and Brave Search
        
    async def discover_competitor_urls(self, competitor_name: str, base_url: str) -> List[DiscoveredURL]:
        """Main discovery pipeline with Cohere-first AI categorization"""
        urls = []
        urls.extend(await self._search_based_discovery(competitor_name))
        urls.extend(await self._sitemap_analysis(base_url))
        urls = await self._ai_categorize_url_with_fallback(urls, competitor_name)
        return self._deduplicate_and_score(urls)
```

**Discovery Methods:**
- **Google Custom Search**: Premium quality search results with high reliability
- **Brave Search API**: Independent search index with privacy focus
- **Sitemap analysis**: Parses XML sitemaps for comprehensive URL discovery
- **Cohere-first AI**: Fast, cost-effective categorization and confidence scoring
- **OpenAI fallback**: Premium quality analysis when Cohere unavailable
- **Social media detection**: Automatic social profile discovery
- **Smart error handling**: Quota detection and immediate fallback switching

#### `src/services/social_media.py` - **Social Media Integration Service**
**Purpose:** Unified social media data fetching across multiple platforms
**Entry Point:** Used by social media handler

**Supported Platforms:**
- **Twitter/X**: Official API v2 integration
- **LinkedIn**: Unofficial API for company data
- **Instagram**: Business account metrics
- **TikTok**: Video performance and follower data

**Core Class:**
```python
class SocialMediaFetcher:
    def __init__(self, config: Dict[str, str]):
        self.twitter_client = self._init_twitter(config)
        self.linkedin_client = self._init_linkedin(config)
        self.instagram_client = self._init_instagram(config)
        self.tiktok_client = self._init_tiktok(config)
    
    async def fetch_all_platforms(self, competitor_id: str, social_urls: Dict[str, str]) -> Dict[str, Any]:
        """Fetch data from all available platforms in parallel"""
        tasks = []
        for platform, url in social_urls.items():
            if hasattr(self, f'fetch_{platform}'):
                tasks.append(getattr(self, f'fetch_{platform}')(url))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return self._process_results(results)
```

**Features:**
- **Parallel Processing**: Fetch from multiple platforms simultaneously
- **Error Handling**: Graceful failure handling for API rate limits
- **Data Standardization**: Unified data format across platforms
- **Historical Tracking**: Store metrics over time for trend analysis

---

### **🕷️ Enhanced Scraping Module**

#### `src/scrapers/` - **Scraping Architecture**
**Purpose:** Modular scraping implementations with unified interface
**Entry Point:** Used by `EnhancedCompetitorScraper` in handlers

**Key Components:**

#### `src/scrapers/base.py` - **Base Scraper Interface**
**Purpose:** Abstract base class ensuring consistent API across all scrapers
**Key Features:**
- **Unified Interface**: All scrapers implement the same methods
- **Common Utilities**: Shared price pattern analysis and logging
- **Type Safety**: Enforced method signatures and return types

#### `src/scrapers/playwright_scraper.py` - **FREE Browser Automation**
**Purpose:** Playwright-based scraper for full JavaScript support
**Key Features:**
- **Zero API Costs**: Completely free to use
- **Full JS Rendering**: Handles React/Vue/Angular apps
- **Smart Selectors**: Enhanced price and feature extraction
- **Lambda Optimized**: Configured for serverless deployment

#### `src/scrapers/scrapingbee_scraper.py` - **PAID API Service**
**Purpose:** ScrapingBee API integration for premium scraping features
**Key Features:**
- **Professional Proxies**: Rotating residential/datacenter IPs
- **Advanced Anti-Bot**: Bypasses CAPTCHAs and detection systems
- **Geographic Targeting**: Scrape from different countries
- **High Reliability**: Enterprise-grade infrastructure

#### `src/scrapers/factory.py` - **Scraper Factory & Auto-Detection**
**Purpose:** Smart scraper selection and instantiation
**Key Features:**
- **Auto-Detection**: Chooses best scraper based on environment
- **Fallback Logic**: ScrapingBee → Playwright if needed
- **Environment Parsing**: Reads `PREFERRED_SCRAPER` variable
- **Easy Switching**: Runtime scraper selection

---

### **⚡ Lambda Handlers (Enhanced Entry Points)**

#### `src/handlers/competitor_management.py` - **🏢 Competitor CRUD Operations**
**Entry Point:** API Gateway `/competitors` endpoints
**HTTP Methods:** GET, POST, PUT, DELETE

**Enhanced with URL Discovery Integration:**
- **`create_competitor()`**: Optionally trigger URL discovery on creation
- **`get_competitors()`**: Include URL discovery status in responses
- **`get_competitor()`**: Return discovered URLs and social media data
- **URL discovery status tracking**: pending, in_progress, completed, failed

**API Routes Handled:**
```
POST   /competitors           # Create competitor (with optional URL discovery)
GET    /competitors           # List competitors (with discovery status)
GET    /competitors/{id}      # Get competitor (with URLs and social data)
PUT    /competitors/{id}      # Update competitor
DELETE /competitors/{id}      # Delete competitor
```

#### `src/handlers/url_discovery.py` - **🔍 NEW: Intelligent URL Discovery**
**Entry Point:** API Gateway `/competitors/{id}/discover-urls` and related endpoints

**Key Functions:**
- **`discover_urls()`**: Trigger URL discovery for a competitor
- **`get_discovered_urls()`**: Retrieve discovered URLs with status
- **`confirm_urls()`**: User confirmation workflow for discovered URLs
- **`get_discovery_status()`**: Check discovery job status

**API Routes Handled:**
```
POST   /competitors/{id}/discover-urls     # Trigger URL discovery
GET    /competitors/{id}/urls              # List discovered URLs
PUT    /competitors/{id}/urls              # Confirm/reject URLs
GET    /competitors/{id}/urls/status       # Discovery status
```

**Discovery Pipeline:**
1. **Initialize Discovery**: Create discovery job record
2. **URL Discovery**: Use LangChain service to find relevant URLs
3. **Categorization**: Classify URLs by type (pricing, features, blog, social)
4. **Confidence Scoring**: ML-based relevance assessment
5. **User Confirmation**: Present URLs for user review
6. **Status Tracking**: Monitor discovery progress and results

#### `src/handlers/social_media.py` - **📱 NEW: Social Media Integration**
**Entry Point:** API Gateway `/competitors/{id}/social-media` endpoints

**Key Functions:**
- **`fetch_social_data()`**: Fetch fresh social media data
- **`get_social_data()`**: Retrieve stored social media metrics
- **`fetch_platform_data()`**: Fetch data from specific platform
- **`get_social_trends()`**: Analyze historical social media trends

**API Routes Handled:**
```
GET    /competitors/{id}/social-media                # Get stored social data
POST   /competitors/{id}/social-media               # Fetch fresh social data
POST   /competitors/{id}/social-media/{platform}    # Fetch specific platform
GET    /competitors/{id}/social-media/trends        # Historical trends
```

**Social Media Pipeline:**
1. **Platform Detection**: Identify social media URLs from discovered URLs
2. **Parallel Fetching**: Fetch data from multiple platforms simultaneously
3. **Data Standardization**: Normalize data across different platforms
4. **Historical Storage**: Store metrics for trend analysis
5. **Error Handling**: Graceful handling of API rate limits and errors

#### `src/handlers/scrape_competitor.py` - **🕷️ Enhanced Web Scraping Engine**
**Entry Point 1:** API Gateway `/competitors/{id}/scrape-*` endpoints
**Entry Point 2:** CloudWatch Events (scheduled scraping every 6 hours)

**🎯 Enhanced Scraping Architecture:**
The system now supports **URL-category-aware scraping** with the new `EnhancedCompetitorScraper` class:

**Key Classes & Functions:**
- **`EnhancedCompetitorScraper`**: URL discovery integration with category-aware scraping
- **`scrape_all_competitor_urls()`**: Scrape all confirmed URLs for a competitor
- **`scrape_by_category()`**: Scrape URLs of specific category (pricing, features, blog)
- **`scrape_discovered_url()`**: Scrape individual discovered URL with context

**Enhanced API Routes:**
```
POST   /competitors/{id}/scrape-all         # Scrape all confirmed URLs
POST   /competitors/{id}/scrape-category    # Scrape specific URL category
POST   /competitors/{id}/scrape-discovered  # Scrape specific discovered URL
```

**Enhanced Scraping Pipeline:**
1. **URL Selection**: Choose URLs based on category and confirmation status
2. **Context-Aware Scraping**: Different strategies for pricing vs. blog pages
3. **Batch Processing**: Efficiently scrape multiple URLs
4. **Enhanced Metadata**: Rich context about scraped data and source URLs
5. **Error Handling**: Fallback logic and retry mechanisms

#### `src/handlers/battle_card.py` - **⚔️ Enhanced AI Battle Card Generation**
**Entry Point:** API Gateway `/battle-card` endpoint

**Enhanced with URL Discovery Data:**
- **Richer Context**: Uses discovered URLs and social media data
- **Category-Specific Analysis**: Pricing vs. feature comparison insights
- **Social Intelligence**: Incorporates social media metrics and trends
- **Enhanced Prompts**: More comprehensive competitive analysis

**Enhanced Battle Card Structure:**
- Executive Summary
- Competitive Positioning Matrix
- Comprehensive Pricing Analysis (from discovered pricing pages)
- Feature Gaps & Advantages (from discovered feature pages)
- Content Strategy Analysis (from discovered blog pages)
- Social Media Presence Comparison
- Sales Objection Handling
- Win/Loss Factors
- Recommended Messaging

#### `src/handlers/migrations.py` - **🔄 Enhanced Database Management**
**Entry Point:** Manual Lambda invocation for database operations

**Enhanced Functions:**
- **`run_migrations()`**: Create enhanced database schema with new tables
- **`create_test_user()`**: Initialize test data including discovered URLs
- **`migrate_existing_data()`**: Migrate existing competitors to new schema
- **Health check functions**: Verify database connectivity and new tables

---

### **🔧 Configuration & Setup**

#### `src/requirements.txt` - **Enhanced Python Dependencies**
**Purpose:** Defines all Python packages required by Lambda functions

**Enhanced Dependencies:**
```txt
# Database
sqlalchemy==2.0.23      # Async ORM
asyncpg==0.29.0         # PostgreSQL async driver

# Web Scraping
beautifulsoup4==4.12.2  # HTML parsing
aiohttp==3.9.1          # Async HTTP client
playwright==1.40.0      # Browser automation

# AI/ML & Search
langchain==0.0.350      # LLM framework
openai==1.3.7           # GPT-4 integration
duckduckgo-search==3.9.6 # Web search for URL discovery

# Social Media APIs
tweepy==4.14.0          # Twitter API
linkedin-api==2.0.0     # LinkedIn (unofficial)
instagrapi==2.0.0       # Instagram (unofficial)
TikTokApi==5.3.0        # TikTok API

# URL Processing
validators==0.22.0      # URL validation
requests-html==0.10.0   # Advanced web scraping
sitemap-parser==0.6.3   # Sitemap parsing

# AWS
boto3==1.34.0           # AWS SDK
```

#### `env.example` - **Enhanced Environment Configuration Template**
**Purpose:** Template for local development environment variables

**Enhanced Variables:**
```bash
# Database
DATABASE_URL="postgresql+asyncpg://..."  # Database connection

# Scraping (Choose your option)
PREFERRED_SCRAPER="playwright"     # Free option
PREFERRED_SCRAPER="scrapingbee"    # Paid option  
PREFERRED_SCRAPER="auto"           # Smart detection

# Core API Keys
OPENAI_API_KEY="sk-..."                 # GPT-4 access
SCRAPINGBEE_API_KEY="..."               # Web scraping service (optional)

# 🆕 NEW: URL Discovery
SERPAPI_KEY="your-serpapi-key"                    # Optional for enhanced search
LANGCHAIN_SEARCH_RESULTS_LIMIT="10"              # Search result limit
URL_DISCOVERY_CONFIDENCE_THRESHOLD="0.7"         # Confidence threshold

# 🆕 NEW: Social Media APIs
TWITTER_BEARER_TOKEN="your_twitter_bearer_token"
LINKEDIN_EMAIL="your_linkedin_email"             # For unofficial API
LINKEDIN_PASSWORD="your_linkedin_password"       # For unofficial API
INSTAGRAM_USERNAME="your_instagram_username"     # For unofficial API
INSTAGRAM_PASSWORD="your_instagram_password"     # For unofficial API
TIKTOK_ACCESS_TOKEN="your_tiktok_access_token"

# Environment
ENVIRONMENT="dev"                       # Deployment environment
```

---

### **🐳 Local Development**

#### `docker-compose.yml` - **Local Infrastructure**
**Purpose:** Local PostgreSQL database for development
**Entry Point:** `docker-compose up -d postgres`

**Services:**
- **PostgreSQL 15**: Local database instance
- **Adminer**: Database administration UI (http://localhost:8080)

#### `scripts/init-db.sql` - **Database Initialization**
**Purpose:** Initial database setup for local development
**Entry Point:** Automatically executed when PostgreSQL starts

**Operations:**
- Enable UUID extension
- Set timezone to UTC
- Prepare for application schema creation

---

### **🚀 Deployment & Testing**

#### `scripts/deploy.sh` - **Automated Deployment**
**Purpose:** Streamlined AWS deployment with parameter management
**Entry Point:** `./scripts/deploy.sh [options]`

**Features:**
- Parameter validation and prompts
- SAM build and deploy automation
- CloudFormation output parsing
- Post-deployment instructions

#### `scripts/test_local.py` - **Local Testing Framework**
**Purpose:** Comprehensive testing and validation for local setup
**Entry Point:** `python scripts/test_local.py`

**Enhanced Test Coverage:**
- Database connectivity
- Migration execution (including new tables)
- User creation
- Competitor management
- URL discovery service
- Social media integration
- Handler initialization
- Data cleanup

#### `scripts/test_url_discovery.py` - **🆕 NEW: URL Discovery Testing**
**Purpose:** Comprehensive testing of URL discovery and social media features
**Entry Point:** `python scripts/test_url_discovery.py`

**Test Coverage:**
- URL discovery service functionality
- Social media API integration
- Database model creation and relationships
- Handler integration testing
- End-to-end workflow validation

#### `scripts/test_url_discovery_simple.py` - **🆕 NEW: Modular URL Discovery Testing**
**Purpose:** Modular testing framework with selectable test configurations
**Entry Point:** `python scripts/test_url_discovery_simple.py`

**Test Modules:**
- **Configuration Status**: API keys and service availability
- **Cohere-Primary Discovery**: Full URL discovery with Cohere-first AI
- **AI Categorization Only**: Test just AI categorization performance
- **Search Backends Only**: Test just search API functionality
- **Performance Comparison**: Compare different AI configurations

**Key Features:**
- Easy test selection via `TESTS_TO_RUN` configuration
- Cohere-first AI strategy validation
- Performance metrics and timing analysis
- Batch processing with progress tracking
- Comprehensive error handling and fallback testing

---

## 🎯 Enhanced Feature Entry Points Summary

### **1. Competitor Management (Enhanced)**
- **Primary Entry:** `GET/POST/PUT/DELETE /competitors`
- **Handler:** `src/handlers/competitor_management.py`
- **Core Logic:** CRUD operations with URL discovery integration
- **Database:** `Competitor`, `CompetitorUrl`, `SocialMediaData` models

### **2. 🆕 URL Discovery System**
- **Primary Entry:** `POST /competitors/{id}/discover-urls`
- **Handler:** `src/handlers/url_discovery.py`
- **Service:** `src/services/url_discovery.py`
- **Core Logic:** LangChain-powered intelligent URL discovery with confidence scoring
- **Database:** `CompetitorUrl` model with status tracking

### **3. 🆕 Social Media Integration**
- **Primary Entry:** `GET/POST /competitors/{id}/social-media`
- **Handler:** `src/handlers/social_media.py`
- **Service:** `src/services/social_media.py`
- **Core Logic:** Multi-platform social media data fetching and analysis
- **Database:** `SocialMediaData` model with metrics tracking

### **4. Enhanced Web Scraping**
- **Primary Entry:** `POST /competitors/{id}/scrape-*` or CloudWatch scheduled events
- **Handler:** `src/handlers/scrape_competitor.py`
- **Core Logic:** Category-aware scraping with URL discovery integration
- **Database:** Enhanced `ScrapeResult` and `ScrapeJob` models

### **5. Enhanced AI Battle Cards**
- **Primary Entry:** `POST /battle-card`
- **Handler:** `src/handlers/battle_card.py`
- **Core Logic:** GPT-4 analysis with discovered URLs and social media data
- **Database:** Enhanced `BattleCard` model with richer context

### **6. Database Management (Enhanced)**
- **Primary Entry:** Direct Lambda invocation
- **Handler:** `src/handlers/migrations.py`
- **Core Logic:** Schema creation with new tables and data migration
- **Database:** All enhanced models in `src/models.py`

---

## 🔄 Enhanced Data Flow Diagrams

### **URL Discovery Flow**
```
API Request → Lambda → LangChain Service → DuckDuckGo Search → AI Analysis → Database Storage
     ↓         ↓            ↓                    ↓               ↓              ↓
User Trigger  Validate   Search Web        Parse Results   Categorize     Store URLs
             Request     + Sitemap           + Score       + Confidence   + Metadata
```

### **Social Media Flow**
```
API Request → Lambda → Social Media Service → Platform APIs → Data Processing → Database Storage
     ↓         ↓              ↓                    ↓              ↓               ↓
User Trigger  Route      Parallel Fetch       API Responses   Standardize    Historical
             Platform    (Twitter, LinkedIn)   + Rate Limits   Format         Tracking
```

### **Enhanced Scraping Flow**
```
Trigger → URL Selection → Scraper Factory → Content Extraction → Enhanced Storage
   ↓           ↓              ↓                  ↓                  ↓
Schedule    Category        Auto-detect       Category-aware    Metadata +
Event       Filter         Best Scraper      Parsing Logic     Source URLs
```

---

## 🔌 Enhanced Integration Points

### **External APIs**
- **Cohere Command-R**: `https://api.cohere.ai/v1/`
  - Used in: `src/services/url_discovery.py`, `src/handlers/battle_card.py`
  - Purpose: Primary AI for URL categorization and competitive analysis

- **OpenAI GPT-4**: `https://api.openai.com/v1/`
  - Used in: `src/services/url_discovery.py`, `src/handlers/battle_card.py`
  - Purpose: Fallback AI when Cohere unavailable, premium quality analysis

- **Google Custom Search API**: `https://www.googleapis.com/customsearch/v1`
  - Used in: `src/services/url_discovery.py`
  - Purpose: High-quality web search for URL discovery (100 free/day)

- **Brave Search API**: `https://api.search.brave.com/res/v1/web/search`
  - Used in: `src/services/url_discovery.py`
  - Purpose: Independent web search for URL discovery (2,000 free/month)

- **Social Media APIs**:
  - **Twitter API v2**: Official API for follower and engagement metrics
  - **LinkedIn**: Unofficial API for company data
  - **Instagram**: Business account metrics
  - **TikTok**: Video performance data

- **ScrapingBee**: `https://app.scrapingbee.com/api/v1/`
  - Used in: `src/handlers/scrape_competitor.py`
  - Purpose: Premium web scraping with anti-bot features

### **Enhanced AWS Services**
- **API Gateway**: Enhanced with new URL discovery and social media endpoints
- **Lambda**: Additional functions for URL discovery and social media
- **RDS PostgreSQL**: Enhanced schema with new tables
- **CloudWatch**: Enhanced logging and scheduled events

---

## 🛠️ Enhanced Development Workflow

### **Adding New Features**
1. **Define Enhanced Models**: Update `src/models.py` with new tables/relationships
2. **Create Services**: Add business logic to `src/services/`
3. **Create/Update Handlers**: Add/modify files in `src/handlers/`
4. **Update Template**: Add Lambda functions and API routes to `template.yaml`
5. **Add Tests**: Extend testing scripts
6. **Deploy**: Use `scripts/deploy.sh`

### **Testing New Features**
1. **URL Discovery**: Run `python scripts/test_url_discovery.py`
2. **Social Media**: Test individual platform integrations
3. **Enhanced Scraping**: Test category-aware scraping
4. **Integration**: Run full workflow tests

---

## 📊 Enhanced Monitoring & Observability

### **New Log Sources**
- **URL Discovery Service**: LangChain and AI-powered search logs
- **Social Media Service**: Platform API interaction and rate limit logs
- **Enhanced Scraping**: Category-aware scraping and URL metadata logs

### **New Health Checks**
- **URL Discovery Status**: Monitor discovery job progress and success rates
- **Social Media APIs**: Track API rate limits and authentication status
- **Enhanced Database**: Verify new table integrity and relationships

### **New Performance Metrics**
- **URL Discovery Time**: Time to discover and categorize URLs with Cohere-first AI
- **AI Fallback Performance**: Response time and success rate of Cohere → OpenAI fallback
- **Social Media Fetch Speed**: Multi-platform data retrieval performance
- **Enhanced Scraping Efficiency**: Category-specific scraping performance

---

This enhanced documentation provides a complete technical overview of the system with all new URL discovery and social media features integrated. The architecture now supports intelligent competitor analysis with automated URL discovery, comprehensive social media tracking, and Cohere-first AI-powered insights with robust fallback mechanisms.

## 🔬 Testing Strategy

### **Cohere-First AI Testing**
The system now prioritizes Cohere for AI operations with comprehensive fallback testing:

- **Primary Testing**: `test_url_discovery_simple.py` with modular test selection
- **Fallback Validation**: Automatic testing of Cohere → OpenAI → Pattern Matching chain
- **Performance Metrics**: Response time comparison between AI providers
- **Error Handling**: Quota detection and immediate fallback switching
- **Cost Optimization**: Cohere free tier utilization with premium fallback

### **Test Configuration Examples**
```python
# Quick development testing (Cohere-first)
TESTS_TO_RUN = ["test_configuration_status", "test_cohere_primary_discovery"]

# AI performance comparison
TESTS_TO_RUN = ["test_configuration_status", "test_performance_comparison"]

# Search backend validation
TESTS_TO_RUN = ["test_configuration_status", "test_search_backends_only"]
```

The enhanced testing framework ensures reliable operation across different AI providers while optimizing for cost and performance. 