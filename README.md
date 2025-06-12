# 🚀 Competitor Tracking SaaS Backend

A **serverless Python backend** for tracking competitor pricing and generating AI-powered competitive intelligence. Built with AWS Lambda, PostgreSQL, and flexible web scraping architecture.

## 🎯 Key Features

- **🕷️ Flexible Web Scraping**: Choose between Playwright (FREE) or ScrapingBee (PAID)
- **🤖 AI Battle Cards**: GPT-4 powered competitive analysis and positioning
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
                        └─────────────────┘
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

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/competitors` | List competitors |
| `POST` | `/competitors` | Create competitor |
| `PUT` | `/competitors/{id}` | Update competitor |
| `DELETE` | `/competitors/{id}` | Delete competitor |
| `POST` | `/scrape` | Trigger scraping |
| `POST` | `/battle-card` | Generate AI analysis |

## 🔧 Environment Configuration

```bash
# Database
DATABASE_URL="postgresql+asyncpg://..."

# Scraping (Choose your option)
PREFERRED_SCRAPER="playwright"     # Free option
PREFERRED_SCRAPER="scrapingbee"    # Paid option  
PREFERRED_SCRAPER="auto"           # Smart detection

# API Keys
OPENAI_API_KEY="sk-your-key"
SCRAPINGBEE_API_KEY="your-key"     # Optional
```

## 📊 Usage Examples

### Scraping with Auto-Detection
```python
from handlers.scrape_competitor import CompetitorScraper

# Automatically chooses best available scraper
async with CompetitorScraper() as scraper:
    result = await scraper.scrape_url(
        "https://competitor.com/pricing", 
        "Competitor Name"
    )
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
# Test all scraping options
python scripts/test_scraping.py

# Test specific scraper
PREFERRED_SCRAPER=playwright python scripts/test_scraping.py

# Compare performance
python scripts/test_local.py
```

## 📁 Project Structure

```
├── src/
│   ├── handlers/           # Lambda function handlers
│   ├── scrapers/           # Flexible scraping implementations
│   ├── models.py           # Database models
│   ├── database.py         # Database connections
│   └── requirements.txt    # Python dependencies
├── scripts/                # Deployment and testing scripts
├── template.yaml           # AWS SAM template
├── docker-compose.yml      # Local development
├── DOCUMENTATION.md        # Technical documentation
└── RUN.md                  # Setup and deployment guide
```

## 💰 Cost Analysis

### Free Tier (Playwright)
- **Scraping**: $0
- **Lambda**: ~$1-5/month (depends on usage)
- **RDS**: ~$13/month (db.t3.micro)
- **Total**: ~$14-18/month

### Premium Tier (ScrapingBee)
- **Scraping**: $29-199/month
- **Lambda**: ~$1-3/month (lower memory usage)
- **RDS**: ~$13/month
- **Total**: ~$43-215/month

## 🔍 Monitoring & Logs

```bash
# View Lambda logs
sam logs -n ScrapeCompetitorFunction --tail

# Check database
docker exec -it postgres psql -U postgres -d competitordb

# Monitor scraping jobs
# SELECT * FROM scrape_results ORDER BY scraped_at DESC;
```

## 🔐 Security Features

- **VPC Isolation**: Database in private subnets
- **IAM Least Privilege**: Minimal required permissions
- **API Key Management**: Secure environment variables
- **Input Validation**: Sanitized database operations
- **Multi-tenant**: User-isolated data access

## 📚 Documentation

- **[DOCUMENTATION.md](DOCUMENTATION.md)**: Complete technical documentation
- **[RUN.md](RUN.md)**: Step-by-step setup and deployment guide

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

For questions or issues:
1. Check the documentation files
2. Review the testing scripts
3. Examine CloudFormation events for deployment issues
4. Check Lambda logs for runtime errors

---

**Built with ❤️ for competitive intelligence and business strategy**