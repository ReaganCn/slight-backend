"""
Flexible competitor scraping handler supporting multiple scraper implementations.
Automatically chooses between Playwright (free) and ScrapingBee (paid) based on environment.
Enhanced with URL discovery support.
"""

import json
import logging
import os
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import uuid

from sqlalchemy import select, update

from database import get_session, ensure_connection
from models import Competitor, ScrapeResult, ScrapeJob, CompetitorUrl
from scrapers.factory import get_scraper_from_env, ScraperFactory

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class CompetitorScraper:
    """
    Flexible competitor scraper that automatically chooses the best available scraper.
    Supports Playwright (free) and ScrapingBee (paid) implementations.
    """
    
    def __init__(self, scraper_type: str = "auto", config: Optional[Dict[str, Any]] = None):
        """
        Initialize scraper with specified type or auto-detection.
        
        Args:
            scraper_type: 'auto', 'playwright', or 'scrapingbee'
            config: Optional configuration dictionary
        """
        self.scraper_type = scraper_type
        self.config = config or {}
        self.scraper = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        if self.scraper_type == "auto":
            self.scraper = get_scraper_from_env(self.config)
        else:
            self.scraper = ScraperFactory.create_from_string(self.scraper_type, self.config)
        
        # Initialize scraper if it has async setup
        if hasattr(self.scraper, '__aenter__'):
            await self.scraper.__aenter__()
        elif hasattr(self.scraper, 'setup'):
            await self.scraper.setup()
            
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if hasattr(self.scraper, '__aexit__'):
            await self.scraper.__aexit__(exc_type, exc_val, exc_tb)
        elif hasattr(self.scraper, 'cleanup'):
            await self.scraper.cleanup()
    
    async def scrape_url(self, url: str, competitor_name: str) -> Dict[str, Any]:
        """
        Scrape a single URL using the configured scraper.
        
        Args:
            url: URL to scrape
            competitor_name: Name of competitor for context
            
        Returns:
            Scraped data dictionary
        """
        if not self.scraper:
            raise RuntimeError("Scraper not initialized. Use async context manager.")
        
        try:
            # Use the scraper to fetch and parse the URL
            scraped_data = await self.scraper.scrape_url(url, competitor_name)
            
            # Add metadata about scraper used
            if 'metadata_' not in scraped_data:
                scraped_data['metadata_'] = {}
            
            scraped_data['metadata_']['scraper_type'] = self.scraper.__class__.__name__
            scraped_data['metadata_']['scraper_config'] = self.config
            
            return scraped_data
            
        except Exception as e:
            logger.error(f"Scraping failed for {url}: {e}")
            raise
    
    def get_scraper_info(self) -> Dict[str, Any]:
        """Get information about the current scraper"""
        if self.scraper:
            return self.scraper.get_info()
        return {"name": "Not initialized", "cost": "Unknown"}


class EnhancedCompetitorScraper(CompetitorScraper):
    """
    Enhanced scraper that works with discovered URLs
    """
    
    async def scrape_all_competitor_urls(self, competitor_id: str) -> Dict[str, Any]:
        """
        Scrape all confirmed URLs for a competitor:
        1. Get all confirmed URLs (pricing, features, blog)
        2. Scrape each URL with appropriate strategy
        3. Store results with URL categorization
        4. Return comprehensive results
        """
        logger.info(f"🔍 Scraping all URLs for competitor {competitor_id}")
        
        async with get_session() as session:
            # Get competitor
            result = await session.execute(
                select(Competitor).where(Competitor.id == competitor_id)
            )
            competitor = result.scalar_one_or_none()
            
            if not competitor:
                raise ValueError(f"Competitor {competitor_id} not found")
            
            # Get all confirmed URLs (excluding social media)
            urls_result = await session.execute(
                select(CompetitorUrl)
                .where(
                    CompetitorUrl.competitor_id == competitor_id,
                    CompetitorUrl.status == 'confirmed',
                    ~CompetitorUrl.url_type.like('social_%')  # Exclude social media URLs
                )
                .order_by(CompetitorUrl.confidence_score.desc())
            )
            confirmed_urls = urls_result.scalars().all()
            
            if not confirmed_urls:
                return {
                    'success': True,
                    'competitor_id': competitor_id,
                    'competitor_name': competitor.name,
                    'message': 'No confirmed URLs found to scrape',
                    'results': {},
                    'summary': {
                        'total_urls': 0,
                        'successful_scrapes': 0,
                        'failed_scrapes': 0
                    }
                }
            
            # Create overall scrape job
            scrape_job = ScrapeJob(
                competitor_id=competitor.id,
                job_type="url_discovery",
                status="running",
                started_at=datetime.now(timezone.utc)
            )
            session.add(scrape_job)
            await session.commit()
            
            scrape_results = {}
            successful_scrapes = 0
            failed_scrapes = 0
            
            try:
                # Scrape each URL
                for url_record in confirmed_urls:
                    try:
                        logger.info(f"🔍 Scraping {url_record.url_type}: {url_record.url}")
                        
                        # Perform scraping
                        scraped_data = await self.scrape_url(url_record.url, competitor.name)
                        
                        # Save scrape result
                        scrape_result = ScrapeResult(
                            competitor_id=competitor.id,
                            competitor_url_id=url_record.id,
                            prices=scraped_data.get('prices', {}),
                            features=scraped_data.get('features', {}),
                            metadata_={
                                **scraped_data.get('metadata_', {}),
                                'url_type': url_record.url_type,
                                'url_title': url_record.title,
                                'confidence_score': url_record.confidence_score
                            },
                            raw_html_snippet=scraped_data.get('raw_html_snippet', ''),
                            scrape_status="success",
                            scraped_at=datetime.now(timezone.utc)
                        )
                        session.add(scrape_result)
                        await session.flush()
                        
                        # Update URL last scraped time
                        await session.execute(
                            update(CompetitorUrl)
                            .where(CompetitorUrl.id == url_record.id)
                            .values(last_scraped_at=datetime.now(timezone.utc))
                        )
                        
                        # Store result
                        scrape_results[url_record.url_type] = {
                            'url': url_record.url,
                            'title': url_record.title,
                            'scrape_result_id': str(scrape_result.id),
                            'status': 'success',
                            'data_summary': {
                                'prices_found': len(scraped_data.get('prices', {}).get('raw_prices', [])),
                                'features_found': len(scraped_data.get('features', {}).get('plans', [])),
                            },
                            'scraped_at': scrape_result.scraped_at.isoformat()
                        }
                        
                        successful_scrapes += 1
                        
                    except Exception as e:
                        logger.error(f"❌ Failed to scrape {url_record.url}: {e}")
                        
                        # Save error result
                        error_result = ScrapeResult(
                            competitor_id=competitor.id,
                            competitor_url_id=url_record.id,
                            prices={},
                            features={},
                            metadata_={
                                'error': str(e),
                                'url_type': url_record.url_type,
                                'url_title': url_record.title
                            },
                            scrape_status="failed",
                            error_message=str(e),
                            scraped_at=datetime.now(timezone.utc)
                        )
                        session.add(error_result)
                        
                        scrape_results[url_record.url_type] = {
                            'url': url_record.url,
                            'title': url_record.title,
                            'status': 'failed',
                            'error': str(e)
                        }
                        
                        failed_scrapes += 1
                
                # Update competitor last scraped time
                await session.execute(
                    update(Competitor)
                    .where(Competitor.id == competitor.id)
                    .values(last_scraped_at=datetime.now(timezone.utc))
                )
                
                # Update scrape job
                scrape_job.status = "completed"
                scrape_job.completed_at = datetime.now(timezone.utc)
                
                await session.commit()
                
                logger.info(f"✅ Scraping completed for {competitor.name}: {successful_scrapes} successful, {failed_scrapes} failed")
                
                return {
                    'success': True,
                    'competitor_id': competitor_id,
                    'competitor_name': competitor.name,
                    'results': scrape_results,
                    'summary': {
                        'total_urls': len(confirmed_urls),
                        'successful_scrapes': successful_scrapes,
                        'failed_scrapes': failed_scrapes
                    },
                    'scrape_job_id': str(scrape_job.id)
                }
                
            except Exception as e:
                # Update scrape job with error
                scrape_job.status = "failed"
                scrape_job.completed_at = datetime.now(timezone.utc)
                scrape_job.error_message = str(e)
                await session.commit()
                
                logger.error(f"❌ Comprehensive scraping failed for {competitor.name}: {e}")
                raise
    
    async def scrape_by_category(self, competitor_id: str, url_category: str) -> Dict[str, Any]:
        """
        Scrape specific category of URLs (e.g., just pricing pages)
        
        Args:
            competitor_id: UUID of the competitor
            url_category: Category to scrape ('pricing', 'features', 'blog', etc.)
        """
        logger.info(f"🔍 Scraping {url_category} URLs for competitor {competitor_id}")
        
        async with get_session() as session:
            # Get competitor
            result = await session.execute(
                select(Competitor).where(Competitor.id == competitor_id)
            )
            competitor = result.scalar_one_or_none()
            
            if not competitor:
                raise ValueError(f"Competitor {competitor_id} not found")
            
            # Get confirmed URLs for the specific category
            urls_result = await session.execute(
                select(CompetitorUrl)
                .where(
                    CompetitorUrl.competitor_id == competitor_id,
                    CompetitorUrl.status == 'confirmed',
                    CompetitorUrl.url_type == url_category
                )
                .order_by(CompetitorUrl.confidence_score.desc())
            )
            category_urls = urls_result.scalars().all()
            
            if not category_urls:
                return {
                    'success': True,
                    'competitor_id': competitor_id,
                    'competitor_name': competitor.name,
                    'category': url_category,
                    'message': f'No confirmed {url_category} URLs found',
                    'results': []
                }
            
            # Create scrape job
            scrape_job = ScrapeJob(
                competitor_id=competitor.id,
                job_type="manual",
                target_url_type=url_category,
                status="running",
                started_at=datetime.now(timezone.utc)
            )
            session.add(scrape_job)
            await session.commit()
            
            results = []
            
            try:
                # Scrape each URL in the category
                for url_record in category_urls:
                    try:
                        logger.info(f"🔍 Scraping {url_record.url}")
                        
                        # Perform scraping
                        scraped_data = await self.scrape_url(url_record.url, competitor.name)
                        
                        # Save scrape result
                        scrape_result = ScrapeResult(
                            competitor_id=competitor.id,
                            competitor_url_id=url_record.id,
                            prices=scraped_data.get('prices', {}),
                            features=scraped_data.get('features', {}),
                            metadata_={
                                **scraped_data.get('metadata_', {}),
                                'url_type': url_record.url_type,
                                'url_title': url_record.title,
                                'confidence_score': url_record.confidence_score
                            },
                            raw_html_snippet=scraped_data.get('raw_html_snippet', ''),
                            scrape_status="success",
                            scraped_at=datetime.now(timezone.utc)
                        )
                        session.add(scrape_result)
                        await session.flush()
                        
                        # Update URL last scraped time
                        await session.execute(
                            update(CompetitorUrl)
                            .where(CompetitorUrl.id == url_record.id)
                            .values(last_scraped_at=datetime.now(timezone.utc))
                        )
                        
                        results.append({
                            'url_id': str(url_record.id),
                            'url': url_record.url,
                            'title': url_record.title,
                            'scrape_result_id': str(scrape_result.id),
                            'status': 'success',
                            'data_summary': {
                                'prices_found': len(scraped_data.get('prices', {}).get('raw_prices', [])),
                                'features_found': len(scraped_data.get('features', {}).get('plans', [])),
                            },
                            'scraped_at': scrape_result.scraped_at.isoformat()
                        })
                        
                    except Exception as e:
                        logger.error(f"❌ Failed to scrape {url_record.url}: {e}")
                        
                        # Save error result
                        error_result = ScrapeResult(
                            competitor_id=competitor.id,
                            competitor_url_id=url_record.id,
                            prices={},
                            features={},
                            metadata_={
                                'error': str(e),
                                'url_type': url_record.url_type,
                                'url_title': url_record.title
                            },
                            scrape_status="failed",
                            error_message=str(e),
                            scraped_at=datetime.now(timezone.utc)
                        )
                        session.add(error_result)
                        
                        results.append({
                            'url_id': str(url_record.id),
                            'url': url_record.url,
                            'title': url_record.title,
                            'status': 'failed',
                            'error': str(e)
                        })
                
                # Update scrape job
                scrape_job.status = "completed"
                scrape_job.completed_at = datetime.now(timezone.utc)
                
                await session.commit()
                
                successful_count = len([r for r in results if r['status'] == 'success'])
                
                logger.info(f"✅ {url_category} scraping completed for {competitor.name}: {successful_count}/{len(results)} successful")
                
                return {
                    'success': True,
                    'competitor_id': competitor_id,
                    'competitor_name': competitor.name,
                    'category': url_category,
                    'results': results,
                    'summary': {
                        'total_urls': len(results),
                        'successful_scrapes': successful_count,
                        'failed_scrapes': len(results) - successful_count
                    },
                    'scrape_job_id': str(scrape_job.id)
                }
                
            except Exception as e:
                # Update scrape job with error
                scrape_job.status = "failed"
                scrape_job.completed_at = datetime.now(timezone.utc)
                scrape_job.error_message = str(e)
                await session.commit()
                
                logger.error(f"❌ {url_category} scraping failed for {competitor.name}: {e}")
                raise



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
                metadata_=scraped_data.get('metadata_', {}),
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
                metadata_={'error': str(e)},
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
    4. Scrape all URLs: {"action": "scrape_all_urls", "competitor_id": "uuid"}
    5. Scrape by category: {"action": "scrape_category", "competitor_id": "uuid", "category": "pricing"}
    """
    async def async_handler():
        await ensure_connection()
        
        # Parse event
        if isinstance(event, str):
            event_data = json.loads(event)
        else:
            event_data = event
        
        competitor_id = event_data.get('competitor_id')
        action = event_data.get('action', 'manual')
        category = event_data.get('category')
        
        try:
            if competitor_id and action == 'scrape_all_urls':
                # Scrape all confirmed URLs for a competitor
                async with EnhancedCompetitorScraper() as scraper:
                    result = await scraper.scrape_all_competitor_urls(competitor_id)
            elif competitor_id and action == 'scrape_category':
                # Scrape specific category of URLs
                if not category:
                    raise ValueError("Category parameter required for scrape_category action")
                async with EnhancedCompetitorScraper() as scraper:
                    result = await scraper.scrape_by_category(competitor_id, category)
            elif competitor_id:
                # Scrape single competitor (legacy mode)
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
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type, Authorization'
                },
                'body': json.dumps(result, default=str)
            }
            
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': False,
                    'error': str(e),
                    'error_type': 'validation_error'
                })
            }
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
                    'error': str(e),
                    'error_type': 'internal_error'
                })
            }
    
    # Run async handler
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(async_handler())
    finally:
        loop.close() 