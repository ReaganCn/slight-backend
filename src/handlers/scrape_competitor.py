"""
Flexible competitor scraping handler supporting multiple scraper implementations.
Automatically chooses between Playwright (free) and ScrapingBee (paid) based on environment.
"""

import json
import logging
import os
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import uuid

from sqlalchemy import select, update

from database import get_session, ensure_connection
from models import Competitor, ScrapeResult, ScrapeJob
from scrapers.factory import get_scraper_from_env, ScraperFactory

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class CompetitorScraper:
    """
    Flexible competitor data scraper that supports multiple scraping implementations:
    
    🎭 Playwright (FREE): Full JavaScript support, no API costs
    🐝 ScrapingBee (PAID): Premium proxy rotation, anti-bot features
    
    Automatically chooses the best available scraper based on environment variables:
    - PREFERRED_SCRAPER: 'playwright' or 'scrapingbee' 
    - SCRAPINGBEE_API_KEY: If present, enables ScrapingBee option
    
    Easy to switch between implementations without changing application logic!
    """
    
    def __init__(self, scraper_type: str = "auto", config: Optional[Dict[str, Any]] = None):
        """
        Initialize scraper with configurable backend
        
        Args:
            scraper_type: 'auto', 'playwright', or 'scrapingbee'
            config: Optional configuration for the scraper
        """
        self.scraper_type = scraper_type
        self.scraper_config = config or {}
        self.scraper = None
        self.scraper_info = None
    
    async def __aenter__(self):
        """Initialize the chosen scraper"""
        try:
            if self.scraper_type == "auto":
                self.scraper = get_scraper_from_env(self.scraper_config)
            else:
                self.scraper = ScraperFactory.create_from_string(self.scraper_type, self.scraper_config)
            
            # Initialize the scraper
            await self.scraper.__aenter__()
            
            # Log which scraper is being used
            self.scraper_info = self.scraper.get_scraper_info()
            logger.info(f"✅ Initialized {self.scraper_info['name']} scraper (cost: {self.scraper_info['cost']})")
            
            return self
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize scraper: {e}")
            raise
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup scraper resources"""
        if self.scraper:
            await self.scraper.__aexit__(exc_type, exc_val, exc_tb)
    
    async def scrape_url(self, url: str, competitor_name: str) -> Dict[str, Any]:
        """
        Scrape a competitor's pricing page using the configured scraper
        
        Args:
            url: The URL to scrape
            competitor_name: Name of the competitor for context
            
        Returns:
            Dictionary containing extracted pricing and feature data
        """
        if not self.scraper:
            raise RuntimeError("Scraper not initialized. Use async context manager.")
        
        logger.info(f"🔍 Scraping {competitor_name}: {url}")
        
        try:
            # Delegate to the configured scraper implementation
            result = await self.scraper.scrape_url(url, competitor_name)
            
            # Add some additional context to the result
            if 'metadata' in result:
                result['metadata']['competitor_name'] = competitor_name
                result['metadata']['scraper_info'] = {
                    'name': self.scraper_info['name'],
                    'type': self.scraper_info['type'],
                    'cost': self.scraper_info['cost']
                }
            
            logger.info(f"✅ Successfully scraped {competitor_name} using {self.scraper_info['name']}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to scrape {competitor_name}: {e}")
            raise
    
    def get_scraper_info(self) -> Dict[str, Any]:
        """Get information about the current scraper"""
        if self.scraper:
            return self.scraper.get_scraper_info()
        return {"status": "not_initialized"}

async def scrape_single_competitor(competitor_id: str) -> Dict[str, Any]:
    """Scrape a single competitor and save results"""
    async with get_session() as session:
        # Get competitor details
        result = await session.execute(
            select(Competitor).where(Competitor.id == competitor_id)
        )
        competitor = result.scalar_one_or_none()
        
        if not competitor:
            raise ValueError(f"Competitor {competitor_id} not found")
        
        if not competitor.pricing_url:
            raise ValueError(f"No pricing URL configured for {competitor.name}")
        
        # Create scrape job
        scrape_job = ScrapeJob(
            competitor_id=competitor.id,
            job_type="manual",
            status="running",
            started_at=datetime.now(timezone.utc)
        )
        session.add(scrape_job)
        await session.commit()
        
        try:
            # Perform scraping
            async with CompetitorScraper() as scraper:
                scraped_data = await scraper.scrape_url(
                    competitor.pricing_url, 
                    competitor.name
                )
            
            # Save scrape result
            scrape_result = ScrapeResult(
                competitor_id=competitor.id,
                prices=scraped_data.get('prices', {}),
                features=scraped_data.get('features', {}),
                metadata=scraped_data.get('metadata', {}),
                raw_html_snippet=scraped_data.get('raw_html_snippet', ''),
                scrape_status="success",
                scraped_at=datetime.now(timezone.utc)
            )
            session.add(scrape_result)
            
            # Update competitor last scraped time
            await session.execute(
                update(Competitor)
                .where(Competitor.id == competitor.id)
                .values(last_scraped_at=datetime.now(timezone.utc))
            )
            
            # Update scrape job
            scrape_job.status = "completed"
            scrape_job.completed_at = datetime.now(timezone.utc)
            scrape_job.result_id = scrape_result.id
            
            await session.commit()
            
            return {
                'success': True,
                'competitor_id': str(competitor.id),
                'competitor_name': competitor.name,
                'scrape_result_id': str(scrape_result.id),
                'data_summary': {
                    'prices_found': len(scraped_data.get('prices', {}).get('raw_prices', [])),
                    'plans_found': len(scraped_data.get('features', {}).get('plans', [])),
                }
            }
            
        except Exception as e:
            # Update scrape job with error
            scrape_job.status = "failed"
            scrape_job.completed_at = datetime.now(timezone.utc)
            scrape_job.error_message = str(e)
            
            # Save error result
            error_result = ScrapeResult(
                competitor_id=competitor.id,
                prices={},
                features={},
                metadata={'error': str(e)},
                scrape_status="failed",
                error_message=str(e),
                scraped_at=datetime.now(timezone.utc)
            )
            session.add(error_result)
            scrape_job.result_id = error_result.id
            
            await session.commit()
            
            logger.error(f"Failed to scrape competitor {competitor.name}: {e}")
            raise

async def scrape_all_active_competitors() -> Dict[str, Any]:
    """Scrape all active competitors"""
    async with get_session() as session:
        result = await session.execute(
            select(Competitor).where(Competitor.is_active == True)
        )
        competitors = result.scalars().all()
        
        results = []
        errors = []
        
        for competitor in competitors:
            try:
                result = await scrape_single_competitor(str(competitor.id))
                results.append(result)
            except Exception as e:
                error_info = {
                    'competitor_id': str(competitor.id),
                    'competitor_name': competitor.name,
                    'error': str(e)
                }
                errors.append(error_info)
                logger.error(f"Failed to scrape {competitor.name}: {e}")
        
        return {
            'success': True,
            'total_competitors': len(competitors),
            'successful_scrapes': len(results),
            'failed_scrapes': len(errors),
            'results': results,
            'errors': errors
        }

def handler(event, context):
    """
    Lambda handler for competitor scraping
    
    Event formats:
    1. Manual scrape: {"competitor_id": "uuid"}
    2. Scrape all: {"action": "scrape_all"}
    3. Scheduled scrape: {"action": "scheduled_scrape"}
    """
    async def async_handler():
        await ensure_connection()
        
        # Parse event
        if isinstance(event, str):
            event = json.loads(event)
        
        competitor_id = event.get('competitor_id')
        action = event.get('action', 'manual')
        
        if competitor_id:
            # Scrape single competitor
            result = await scrape_single_competitor(competitor_id)
        elif action in ['scrape_all', 'scheduled_scrape']:
            # Scrape all active competitors
            result = await scrape_all_active_competitors()
        else:
            raise ValueError("Invalid event format. Provide 'competitor_id' or 'action'")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(result, default=str)
        }
    
    # Run async handler
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(async_handler())
    except Exception as e:
        logger.error(f"Handler error: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }
    finally:
        loop.close() 