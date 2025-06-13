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
                        └─────────────────┘
```

**Data Flow:**
1. **API Gateway** receives HTTP requests
2. **Lambda Functions** process business logic
3. **Database Layer** handles data persistence
4. **External APIs** provide scraping and AI capabilities

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

#### `src/models.py` - **Data Models & Schema**
**Purpose:** SQLAlchemy ORM models defining database schema
**Entry Point:** Imported by all handlers for database operations

**Key Models:**
- **`User`**: Multi-tenant user management
- **`Competitor`**: Competitor profiles and scraping configuration
- **`ScrapeResult`**: Historical pricing/feature data (JSONB storage)
- **`BattleCard`**: AI-generated competitive intelligence
- **`ScrapeJob`**: Job tracking and status monitoring

**Example Model Structure:**
```python
class Competitor(Base):
    __tablename__ = "competitors"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    pricing_url = Column(String(500))
    # Relationships
    scrape_results = relationship("ScrapeResult", back_populates="competitor")
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

### **🕷️ Flexible Scraping Module**

#### `src/scrapers/` - **Scraping Architecture**
**Purpose:** Modular scraping implementations with unified interface
**Entry Point:** Used by `CompetitorScraper` in handlers

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

**Configuration Options:**
```python
playwright_config = {
    'headless': True,
    'timeout': 30000,
    'wait_time': 3000,
    'viewport': {'width': 1920, 'height': 1080}
}
```

#### `src/scrapers/scrapingbee_scraper.py` - **PAID API Service**
**Purpose:** ScrapingBee API integration for premium scraping features
**Key Features:**
- **Professional Proxies**: Rotating residential/datacenter IPs
- **Advanced Anti-Bot**: Bypasses CAPTCHAs and detection systems
- **Geographic Targeting**: Scrape from different countries
- **High Reliability**: Enterprise-grade infrastructure

**Configuration Options:**
```python
scrapingbee_config = {
    'render_js': True,
    'premium_proxy': True,
    'country_code': 'US',
    'wait': 3000
}
```

#### `src/scrapers/factory.py` - **Scraper Factory & Auto-Detection**
**Purpose:** Smart scraper selection and instantiation
**Key Features:**
- **Auto-Detection**: Chooses best scraper based on environment
- **Fallback Logic**: ScrapingBee → Playwright if needed
- **Environment Parsing**: Reads `PREFERRED_SCRAPER` variable
- **Easy Switching**: Runtime scraper selection

**Factory Methods:**
```python
# Auto-detection
scraper = ScraperFactory.create_scraper()

# Explicit selection
scraper = ScraperFactory.create_from_string("playwright")

# Environment-based
scraper = get_scraper_from_env()
```

---

### **⚡ Lambda Handlers (Main Entry Points)**

#### `src/handlers/competitor_management.py` - **🏢 Competitor CRUD Operations**
**Entry Point:** API Gateway `/competitors` endpoints
**HTTP Methods:** GET, POST, PUT, DELETE

**Key Functions:**
- **`create_competitor()`**: Add new competitor to track
- **`get_competitors()`**: List all competitors for a user
- **`get_competitor()`**: Retrieve specific competitor details
- **`update_competitor()`**: Modify competitor information
- **`delete_competitor()`**: Soft delete (deactivate) competitor

**API Routes Handled:**
```
POST   /competitors           # Create competitor
GET    /competitors           # List competitors
GET    /competitors/{id}      # Get specific competitor
PUT    /competitors/{id}      # Update competitor
DELETE /competitors/{id}      # Delete competitor
```

**Handler Function:**
```python
def handler(event, context):
    # Routes HTTP methods to appropriate functions
    # Handles CORS, authentication, error handling
    # Returns standardized JSON responses
```

#### `src/handlers/scrape_competitor.py` - **🕷️ Flexible Web Scraping Engine**
**Entry Point 1:** API Gateway `/scrape` endpoint (manual triggers)
**Entry Point 2:** CloudWatch Events (scheduled scraping every 6 hours)

**🎯 Flexible Scraping Architecture:**
The system now supports **multiple scraping implementations** that can be switched without code changes:

**Scraping Implementations:**
- **🎭 Playwright (FREE)**: Full JavaScript support, no API costs
- **🐝 ScrapingBee (PAID)**: Premium proxy rotation, anti-bot features

**Key Classes & Functions:**
- **`CompetitorScraper`**: Flexible wrapper supporting multiple scraper backends
- **`scrape_single_competitor()`**: Scrape individual competitor using chosen implementation
- **`scrape_all_active_competitors()`**: Batch scraping operation

**Auto-Detection Logic:**
The system automatically chooses the best scraper based on:
1. `PREFERRED_SCRAPER` environment variable
2. Available API keys (ScrapingBee)
3. Fallback to Playwright (free) if no preference set

**Usage Examples:**
```python
# Auto-detection (recommended)
async with CompetitorScraper() as scraper:
    result = await scraper.scrape_url(url, competitor_name)

# Force specific scraper
async with CompetitorScraper("playwright") as scraper:  # FREE
    result = await scraper.scrape_url(url, competitor_name)

async with CompetitorScraper("scrapingbee") as scraper:  # PAID
    result = await scraper.scrape_url(url, competitor_name)
```

**Environment Configuration:**
```bash
PREFERRED_SCRAPER=auto              # Auto-detect (default)
PREFERRED_SCRAPER=playwright        # Force free Playwright
PREFERRED_SCRAPER=scrapingbee       # Force paid ScrapingBee
SCRAPINGBEE_API_KEY=your_key        # Required for ScrapingBee
```

**Scraping Pipeline:**
1. **Scraper Selection**: Auto-detect or use specified scraper type
2. **URL Fetching**: 
   - Playwright: Browser automation with full JS support
   - ScrapingBee: API service with proxy rotation
3. **HTML Parsing**: BeautifulSoup with intelligent selectors
4. **Data Extraction**: Pricing, features, metadata_ using enhanced selectors
5. **Storage**: Save results with scraper metadata_ and performance metrics
6. **Error Handling**: Fallback logic and retry mechanisms

**Event Formats:**
```python
# Manual scrape
{"competitor_id": "uuid"}

# Scrape all active
{"action": "scrape_all"}

# Scheduled (from CloudWatch)
{"action": "scheduled_scrape"}
```

**Cost Comparison:**
| Feature | Playwright | ScrapingBee |
|---------|------------|-------------|
| **Cost** | FREE | $29-199/month |
| **JavaScript** | ✅ Full | ✅ Full |
| **Memory** | 1GB | 512MB |
| **Proxy Rotation** | ❌ | ✅ Professional |
| **Anti-Bot Bypass** | ⚠️ Basic | ✅ Advanced |

#### `src/handlers/battle_card.py` - **⚔️ AI Battle Card Generation**
**Entry Point:** API Gateway `/battle-card` endpoint

**Key Classes & Functions:**
- **`BattleCardGenerator`**: LangChain + GPT-4 integration
- **`generate_battle_card()`**: Create AI-powered competitive analysis
- **`get_battle_card()`**: Retrieve existing battle card
- **`list_battle_cards()`**: List user's battle cards

**AI Generation Pipeline:**
1. **Data Aggregation**: Collect competitor data and scrape results
2. **Prompt Engineering**: Build context-rich prompts for GPT-4
3. **AI Processing**: Generate structured battle card content
4. **Post-processing**: Format, validate, and store results
5. **Metadata Tracking**: Token usage, costs, model versions

**Battle Card Structure:**
- Executive Summary
- Competitive Positioning Matrix
- Pricing Comparison & Analysis
- Feature Gaps & Advantages
- Sales Objection Handling
- Win/Loss Factors
- Recommended Messaging

**Event Formats:**
```python
# Generate new battle card
{"action": "generate", "user_id": "uuid", "competitor_ids": ["uuid1", "uuid2"]}

# Retrieve existing card
{"action": "get", "user_id": "uuid", "battle_card_id": "uuid"}

# List all cards
{"action": "list", "user_id": "uuid", "limit": 20}
```

#### `src/handlers/migrations.py` - **🔄 Database Management**
**Entry Point:** Manual Lambda invocation for database operations

**Key Functions:**
- **`run_migrations()`**: Create database schema and tables
- **`create_test_user()`**: Initialize test data for development
- **Health check functions**: Verify database connectivity

**Usage Scenarios:**
- Initial deployment setup
- Database schema updates
- Development environment setup
- Production health monitoring

---

### **🔧 Configuration & Setup**

#### `src/requirements.txt` - **Python Dependencies**
**Purpose:** Defines all Python packages required by Lambda functions

**Key Dependencies:**
```txt
# Database
sqlalchemy==2.0.23      # Async ORM
asyncpg==0.29.0         # PostgreSQL async driver

# Web Scraping
beautifulsoup4==4.12.2  # HTML parsing
aiohttp==3.9.1          # Async HTTP client

# AI/ML
langchain==0.0.350      # LLM framework
openai==1.3.7           # GPT-4 integration

# AWS
boto3==1.34.0           # AWS SDK
```

#### `env.example` - **Environment Configuration Template**
**Purpose:** Template for local development environment variables

**Key Variables:**
```bash
DATABASE_URL="postgresql+asyncpg://..."  # Database connection
OPENAI_API_KEY="sk-..."                 # GPT-4 access
SCRAPINGBEE_API_KEY="..."               # Web scraping service
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

**Usage Examples:**
```bash
./scripts/deploy.sh --guided                    # Interactive setup
./scripts/deploy.sh --stack-name my-stack       # Direct deployment
```

#### `scripts/test_local.py` - **Local Testing Framework**
**Purpose:** Comprehensive testing and validation for local setup
**Entry Point:** `python scripts/test_local.py`

**Test Coverage:**
- Database connectivity
- Migration execution
- User creation
- Competitor management
- Handler initialization
- Data cleanup

**Test Output:**
```
✅ Database Connection      PASS
✅ Database Migrations      PASS
✅ Test User Creation       PASS
✅ Competitor Management    PASS
✅ Scraping Handler        PASS
✅ Battle Card Handler     PASS
```

---

## 🎯 Feature Entry Points Summary

### **1. Competitor Management**
- **Primary Entry:** `GET/POST/PUT/DELETE /competitors`
- **Handler:** `src/handlers/competitor_management.py`
- **Core Logic:** CRUD operations with user isolation
- **Database:** `Competitor` model in `src/models.py`

### **2. Web Scraping**
- **Primary Entry:** `POST /scrape` or CloudWatch scheduled events
- **Handler:** `src/handlers/scrape_competitor.py`
- **Core Logic:** ScrapingBee API + BeautifulSoup parsing
- **Database:** `ScrapeResult` and `ScrapeJob` models

### **3. AI Battle Cards**
- **Primary Entry:** `POST /battle-card`
- **Handler:** `src/handlers/battle_card.py`
- **Core Logic:** LangChain + GPT-4 competitive analysis
- **Database:** `BattleCard` model with JSONB content

### **4. Database Management**
- **Primary Entry:** Direct Lambda invocation
- **Handler:** `src/handlers/migrations.py`
- **Core Logic:** Schema creation and data seeding
- **Database:** All models in `src/models.py`

---

## 🔄 Data Flow Diagrams

### **Scraping Flow**
```
CloudWatch Event → Lambda → ScrapingBee API → BeautifulSoup → PostgreSQL
      ↓              ↓            ↓               ↓              ↓
  Schedule    Extract URL    Fetch HTML     Parse Data    Store Results
```

### **Battle Card Generation Flow**
```
API Request → Lambda → Database Query → GPT-4 API → Format Response → Store & Return
     ↓         ↓           ↓              ↓            ↓               ↓
  User Input  Validate   Get Competitor   Generate     Process        Save Card
                        History          Analysis     Markdown
```

### **Competitor Management Flow**
```
API Gateway → Lambda → Input Validation → Database Operation → JSON Response
     ↓         ↓            ↓                    ↓                ↓
  HTTP Req   Route      Check User Auth      CRUD Action      Success/Error
```

---

## 🔌 Integration Points

### **External APIs**
- **ScrapingBee**: `https://app.scrapingbee.com/api/v1/`
  - Used in: `src/handlers/scrape_competitor.py`
  - Purpose: Web scraping with proxy and JS rendering
  
- **OpenAI GPT-4**: `https://api.openai.com/v1/`
  - Used in: `src/handlers/battle_card.py`
  - Purpose: AI-powered competitive analysis

### **AWS Services**
- **API Gateway**: RESTful API endpoints
- **Lambda**: Serverless function execution
- **RDS PostgreSQL**: Managed database service
- **CloudWatch**: Logging and scheduled events
- **VPC**: Network isolation and security

### **Database Connections**
- **Async Engine**: SQLAlchemy 2.0 with asyncpg driver
- **Connection Pooling**: Optimized for Lambda cold starts
- **Session Management**: Context managers for proper cleanup

---

## 🛠️ Development Workflow

### **Adding New Features**
1. **Define Model**: Add to `src/models.py`
2. **Create Handler**: New file in `src/handlers/`
3. **Update Template**: Add Lambda function to `template.yaml`
4. **Add Tests**: Extend `scripts/test_local.py`
5. **Deploy**: Use `scripts/deploy.sh`

### **Modifying Existing Features**
1. **Update Handler**: Modify business logic
2. **Database Changes**: Update models and run migrations
3. **Test Locally**: Run `scripts/test_local.py`
4. **Deploy Changes**: Use `sam deploy`

### **Debugging Issues**
1. **Local**: Check Docker logs and database connections
2. **AWS**: Use CloudWatch logs and SAM CLI tools
3. **Database**: Connect directly to verify data integrity

---

## 📊 Monitoring & Observability

### **Log Locations**
- **Local Development**: Docker Compose logs
- **AWS Lambda**: CloudWatch Logs groups
- **Database**: RDS logs and performance insights

### **Health Checks**
- **Database**: Connection validation in `src/database.py`
- **API**: Response status codes and error handling
- **External APIs**: Rate limiting and error handling

### **Performance Metrics**
- **Lambda Duration**: Function execution time
- **Database Queries**: Query performance and connection pooling
- **API Response Times**: End-to-end request processing

---

This documentation provides a complete technical overview of the system architecture, file purposes, and feature entry points. Each component is designed to be modular, testable, and maintainable while following serverless best practices. 