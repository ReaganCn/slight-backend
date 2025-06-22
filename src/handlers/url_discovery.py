"""
URL Discovery Lambda Handler
Handles URL discovery and confirmation workflow for competitor pages.
"""

import json
import logging
import asyncio
import os
from datetime import datetime, timezone
from typing import Dict, Any, List
import uuid

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from database import get_session, ensure_connection
from models import Competitor, CompetitorUrl
from services.url_discovery import URLDiscoveryService

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

async def discover_urls(competitor_id: str) -> Dict[str, Any]:
    """
    Main URL discovery function:
    1. Get competitor details
    2. Use LangChain to find relevant URLs
    3. Save discovered URLs with confidence scores
    4. Return categorized results for user confirmation
    """
    logger.info(f"🔍 Starting URL discovery for competitor {competitor_id}")
    
    async with get_session() as session:
        try:
            # Get competitor details
            result = await session.execute(
                select(Competitor).where(Competitor.id == competitor_id)
            )
            competitor = result.scalar_one_or_none()
            
            if not competitor:
                raise ValueError(f"Competitor {competitor_id} not found")
            
            if not competitor.website:
                raise ValueError(f"No website configured for competitor {competitor.name}")
            
            # Update discovery status
            await session.execute(
                update(Competitor)
                .where(Competitor.id == competitor_id)
                .values(
                    url_discovery_status="running",
                    urls_discovered_at=datetime.now(timezone.utc)
                )
            )
            await session.commit()
            
            # Initialize URL discovery service with AI fallback support
            openai_api_key = os.getenv('OPENAI_API_KEY')
            google_cse_api_key = os.getenv('GOOGLE_CSE_API_KEY')
            google_cse_id = os.getenv('GOOGLE_CSE_ID')
            brave_api_key = os.getenv('BRAVE_API_KEY')
            cohere_api_key = os.getenv('COHERE_API_KEY')
            
            discovery_service = URLDiscoveryService(
                openai_api_key=openai_api_key,
                google_cse_api_key=google_cse_api_key,
                google_cse_id=google_cse_id,
                brave_api_key=brave_api_key,
                cohere_api_key=cohere_api_key
            )
            
            # Discover URLs
            discovered_urls = await discovery_service.discover_competitor_urls(
                competitor.name,
                competitor.website
            )
            
            # Save discovered URLs to database
            saved_urls = {}
            total_saved = 0
            
            # Group URLs by category
            for url_data in discovered_urls:
                category = url_data.get('category', 'general')
                if category not in saved_urls:
                    saved_urls[category] = []
                try:
                    # Create CompetitorUrl record
                    competitor_url = CompetitorUrl(
                        competitor_id=competitor.id,
                        url_type=category,
                        url=url_data['url'],
                        title=url_data.get('title', ''),
                        confidence_score=url_data.get('confidence_score', 0.5),
                        discovery_method=url_data.get('discovery_method', 'unknown'),
                        discovered_by=url_data.get('source', 'langchain_search'),
                        status='pending',
                        metadata_=url_data
                    )
                    
                    session.add(competitor_url)
                    await session.flush()  # Get the ID
                    
                    saved_urls[category].append({
                        'id': str(competitor_url.id),
                        'url': competitor_url.url,
                        'title': competitor_url.title,
                        'confidence_score': competitor_url.confidence_score,
                        'discovery_method': competitor_url.discovery_method,
                        'status': competitor_url.status
                    })
                    
                    total_saved += 1
                    
                except IntegrityError as e:
                    logger.warning(f"URL already exists: {url_data['url']}")
                    await session.rollback()
                    continue
                except Exception as e:
                    logger.error(f"Failed to save URL {url_data['url']}: {e}")
                    continue
            
            # Update competitor status
            await session.execute(
                update(Competitor)
                .where(Competitor.id == competitor_id)
                .values(url_discovery_status="completed")
            )
            
            await session.commit()
            
            logger.info(f"✅ URL discovery completed for {competitor.name}: {total_saved} URLs saved")
            
            return {
                'success': True,
                'competitor_id': competitor_id,
                'competitor_name': competitor.name,
                'total_urls_found': total_saved,
                'discovered_urls': saved_urls,
                'discovery_summary': {
                    category: len(urls) for category, urls in saved_urls.items()
                }
            }
            
        except Exception as e:
            # Update competitor status to failed
            try:
                await session.execute(
                    update(Competitor)
                    .where(Competitor.id == competitor_id)
                    .values(url_discovery_status="failed")
                )
                await session.commit()
            except:
                pass
            
            logger.error(f"❌ URL discovery failed for competitor {competitor_id}: {e}")
            raise

async def confirm_urls(competitor_id: str, url_confirmations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Process user confirmations:
    1. Update URL statuses (confirmed/rejected)
    2. Save confirmed URLs to competitor record
    3. Return updated competitor data
    """
    logger.info(f"📝 Processing URL confirmations for competitor {competitor_id}")
    
    async with get_session() as session:
        try:
            # Verify competitor exists
            result = await session.execute(
                select(Competitor).where(Competitor.id == competitor_id)
            )
            competitor = result.scalar_one_or_none()
            
            if not competitor:
                raise ValueError(f"Competitor {competitor_id} not found")
            
            confirmed_count = 0
            rejected_count = 0
            updated_urls = []
            
            # Process each confirmation
            for confirmation in url_confirmations:
                url_id = confirmation.get('url_id')
                status = confirmation.get('status')  # 'confirmed' or 'rejected'
                
                if not url_id or status not in ['confirmed', 'rejected']:
                    logger.warning(f"Invalid confirmation: {confirmation}")
                    continue
                
                try:
                    # Update URL status
                    await session.execute(
                        update(CompetitorUrl)
                        .where(
                            CompetitorUrl.id == url_id,
                            CompetitorUrl.competitor_id == competitor_id
                        )
                        .values(
                            status=status,
                            confirmed_at=datetime.now(timezone.utc)
                        )
                    )
                    
                    # Get updated URL data
                    url_result = await session.execute(
                        select(CompetitorUrl).where(CompetitorUrl.id == url_id)
                    )
                    updated_url = url_result.scalar_one_or_none()
                    
                    if updated_url:
                        updated_urls.append({
                            'id': str(updated_url.id),
                            'url': updated_url.url,
                            'url_type': updated_url.url_type,
                            'title': updated_url.title,
                            'status': updated_url.status,
                            'confidence_score': updated_url.confidence_score,
                            'confirmed_at': updated_url.confirmed_at.isoformat() if updated_url.confirmed_at else None
                        })
                        
                        if status == 'confirmed':
                            confirmed_count += 1
                        else:
                            rejected_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to update URL {url_id}: {e}")
                    continue
            
            await session.commit()
            
            # Get summary of all URLs for this competitor
            all_urls_result = await session.execute(
                select(CompetitorUrl)
                .where(CompetitorUrl.competitor_id == competitor_id)
                .order_by(CompetitorUrl.confidence_score.desc())
            )
            all_urls = all_urls_result.scalars().all()
            
            # Group by status and type
            url_summary = {
                'confirmed': {},
                'rejected': {},
                'pending': {}
            }
            
            for url in all_urls:
                status = url.status
                url_type = url.url_type
                
                if url_type not in url_summary[status]:
                    url_summary[status][url_type] = []
                
                url_summary[status][url_type].append({
                    'id': str(url.id),
                    'url': url.url,
                    'title': url.title,
                    'confidence_score': url.confidence_score
                })
            
            logger.info(f"✅ URL confirmations processed: {confirmed_count} confirmed, {rejected_count} rejected")
            
            return {
                'success': True,
                'competitor_id': competitor_id,
                'competitor_name': competitor.name,
                'confirmed_count': confirmed_count,
                'rejected_count': rejected_count,
                'updated_urls': updated_urls,
                'url_summary': url_summary,
                'total_urls': len(all_urls)
            }
            
        except Exception as e:
            logger.error(f"❌ URL confirmation failed for competitor {competitor_id}: {e}")
            raise

async def get_discovered_urls(competitor_id: str, status_filter: str = None) -> Dict[str, Any]:
    """
    Get discovered URLs for a competitor
    
    Args:
        competitor_id: UUID of the competitor
        status_filter: Optional filter by status ('pending', 'confirmed', 'rejected')
    """
    logger.info(f"📋 Getting discovered URLs for competitor {competitor_id}")
    
    async with get_session() as session:
        try:
            # Get competitor
            result = await session.execute(
                select(Competitor).where(Competitor.id == competitor_id)
            )
            competitor = result.scalar_one_or_none()
            
            if not competitor:
                raise ValueError(f"Competitor {competitor_id} not found")
            
            # Build query
            query = select(CompetitorUrl).where(CompetitorUrl.competitor_id == competitor_id)
            
            if status_filter:
                query = query.where(CompetitorUrl.status == status_filter)
            
            query = query.order_by(CompetitorUrl.confidence_score.desc())
            
            # Execute query
            urls_result = await session.execute(query)
            urls = urls_result.scalars().all()
            
            # Group by URL type
            categorized_urls = {}
            for url in urls:
                url_type = url.url_type
                if url_type not in categorized_urls:
                    categorized_urls[url_type] = []
                
                categorized_urls[url_type].append({
                    'id': str(url.id),
                    'url': url.url,
                    'title': url.title,
                    'confidence_score': url.confidence_score,
                    'discovery_method': url.discovery_method,
                    'discovered_by': url.discovered_by,
                    'status': url.status,
                    'discovered_at': url.discovered_at.isoformat(),
                    'confirmed_at': url.confirmed_at.isoformat() if url.confirmed_at else None,
                    'metadata': url.metadata_
                })
            
            return {
                'success': True,
                'competitor_id': competitor_id,
                'competitor_name': competitor.name,
                'url_discovery_status': competitor.url_discovery_status,
                'urls_discovered_at': competitor.urls_discovered_at.isoformat() if competitor.urls_discovered_at else None,
                'categorized_urls': categorized_urls,
                'total_urls': len(urls),
                'summary': {
                    category: len(urls) for category, urls in categorized_urls.items()
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get URLs for competitor {competitor_id}: {e}")
            raise

def handler(event, context):
    """
    Lambda handler for URL discovery
    
    Event formats:
    1. Discover: {"action": "discover", "competitor_id": "uuid"}
    2. Confirm: {"action": "confirm", "competitor_id": "uuid", "confirmations": [...]}
    3. Get URLs: {"action": "get_urls", "competitor_id": "uuid", "status": "pending"}
    """
    async def async_handler():
        await ensure_connection()
        
        # Parse event
        if isinstance(event, str):
            event_data = json.loads(event)
        else:
            event_data = event
        
        action = event_data.get('action')
        competitor_id = event_data.get('competitor_id')
        
        if not action or not competitor_id:
            raise ValueError("Missing required parameters: action and competitor_id")
        
        try:
            if action == 'discover':
                result = await discover_urls(competitor_id)
            elif action == 'confirm':
                confirmations = event_data.get('confirmations', [])
                if not confirmations:
                    raise ValueError("No confirmations provided")
                result = await confirm_urls(competitor_id, confirmations)
            elif action == 'get_urls':
                status_filter = event_data.get('status')
                result = await get_discovered_urls(competitor_id, status_filter)
            else:
                raise ValueError(f"Unknown action: {action}")
            
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