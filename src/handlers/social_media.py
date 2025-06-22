"""
Social Media Lambda Handler
Handles fetching and storing social media data for competitors.
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
from models import Competitor, CompetitorUrl, SocialMediaData
from services.social_media import SocialMediaFetcher

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

async def fetch_social_data(competitor_id: str) -> Dict[str, Any]:
    """
    Fetch social media data for confirmed social URLs:
    1. Get confirmed social media URLs
    2. Fetch data from each platform
    3. Save to SocialMediaData table
    4. Return aggregated results
    """
    logger.info(f"📱 Starting social media fetch for competitor {competitor_id}")
    
    async with get_session() as session:
        try:
            # Get competitor details
            result = await session.execute(
                select(Competitor).where(Competitor.id == competitor_id)
            )
            competitor = result.scalar_one_or_none()
            
            if not competitor:
                raise ValueError(f"Competitor {competitor_id} not found")
            
            # Get confirmed social media URLs
            social_urls_result = await session.execute(
                select(CompetitorUrl)
                .where(
                    CompetitorUrl.competitor_id == competitor_id,
                    CompetitorUrl.status == 'confirmed',
                    CompetitorUrl.url_type.like('social_%')
                )
            )
            social_urls = social_urls_result.scalars().all()
            
            if not social_urls:
                return {
                    'success': True,
                    'competitor_id': competitor_id,
                    'competitor_name': competitor.name,
                    'message': 'No confirmed social media URLs found',
                    'platforms_data': {},
                    'summary': {
                        'total_platforms': 0,
                        'successful_fetches': 0,
                        'failed_fetches': 0
                    }
                }
            
            # Prepare social media configuration
            social_config = {
                'TWITTER_BEARER_TOKEN': os.getenv('TWITTER_BEARER_TOKEN'),
                'LINKEDIN_EMAIL': os.getenv('LINKEDIN_EMAIL'),
                'LINKEDIN_PASSWORD': os.getenv('LINKEDIN_PASSWORD'),
                'INSTAGRAM_USERNAME': os.getenv('INSTAGRAM_USERNAME'),
                'INSTAGRAM_PASSWORD': os.getenv('INSTAGRAM_PASSWORD')
            }
            
            # Initialize social media fetcher
            social_fetcher = SocialMediaFetcher(config=social_config)
            
            # Convert URLs to expected format
            url_data = []
            for url in social_urls:
                platform_name = url.url_type.replace('social_', '')  # Remove 'social_' prefix
                url_data.append({
                    'platform': url.url_type,
                    'url': url.url,
                    'url_id': str(url.id),
                    'platform_name': platform_name
                })
            
            # Fetch social media data
            fetch_results = await social_fetcher.fetch_all_platforms(competitor_id, url_data)
            
            # Save results to database
            saved_platforms = {}
            
            for platform, platform_data in fetch_results['platforms'].items():
                try:
                    # Check if social media data already exists for this platform
                    existing_result = await session.execute(
                        select(SocialMediaData)
                        .where(
                            SocialMediaData.competitor_id == competitor_id,
                            SocialMediaData.platform == platform
                        )
                    )
                    existing_data = existing_result.scalar_one_or_none()
                    
                    if existing_data:
                        # Update existing record
                        await session.execute(
                            update(SocialMediaData)
                            .where(
                                SocialMediaData.competitor_id == competitor_id,
                                SocialMediaData.platform == platform
                            )
                            .values(
                                profile_url=platform_data.get('profile_url', ''),
                                username=platform_data.get('username', ''),
                                followers_count=platform_data.get('followers_count', 0),
                                following_count=platform_data.get('following_count', 0),
                                posts_count=platform_data.get('posts_count', 0),
                                latest_posts=platform_data.get('latest_posts', []),
                                profile_info=platform_data,
                                engagement_metrics=platform_data.get('engagement_metrics', {}),
                                last_updated_at=datetime.now(timezone.utc),
                                fetch_status='success',
                                error_message=None
                            )
                        )
                        
                        logger.info(f"✅ Updated {platform} data for {competitor.name}")
                    else:
                        # Create new record
                        social_data = SocialMediaData(
                            competitor_id=competitor.id,
                            platform=platform,
                            profile_url=platform_data.get('profile_url', ''),
                            username=platform_data.get('username', ''),
                            followers_count=platform_data.get('followers_count', 0),
                            following_count=platform_data.get('following_count', 0),
                            posts_count=platform_data.get('posts_count', 0),
                            latest_posts=platform_data.get('latest_posts', []),
                            profile_info=platform_data,
                            engagement_metrics=platform_data.get('engagement_metrics', {}),
                            fetch_status='success'
                        )
                        
                        session.add(social_data)
                        logger.info(f"✅ Created {platform} data for {competitor.name}")
                    
                    saved_platforms[platform] = {
                        'username': platform_data.get('username', ''),
                        'followers_count': platform_data.get('followers_count', 0),
                        'posts_count': platform_data.get('posts_count', 0),
                        'engagement_rate': platform_data.get('engagement_metrics', {}).get('engagement_rate', 0),
                        'fetched_at': platform_data.get('fetched_at', '')
                    }
                    
                except Exception as e:
                    logger.error(f"Failed to save {platform} data: {e}")
                    
                    # Save error record
                    try:
                        error_data = SocialMediaData(
                            competitor_id=competitor.id,
                            platform=platform,
                            profile_url='',
                            fetch_status='failed',
                            error_message=str(e)
                        )
                        session.add(error_data)
                    except:
                        pass
            
            await session.commit()
            
            # Prepare response
            response_data = {
                'success': True,
                'competitor_id': competitor_id,
                'competitor_name': competitor.name,
                'platforms_data': saved_platforms,
                'summary': fetch_results['summary'],
                'fetched_at': fetch_results['fetched_at'],
                'total_social_urls': len(social_urls)
            }
            
            logger.info(f"✅ Social media fetch completed for {competitor.name}: {len(saved_platforms)} platforms")
            return response_data
            
        except Exception as e:
            logger.error(f"❌ Social media fetch failed for competitor {competitor_id}: {e}")
            raise

async def fetch_platform_data(competitor_id: str, platform: str) -> Dict[str, Any]:
    """
    Fetch data from a specific social media platform
    
    Args:
        competitor_id: UUID of the competitor
        platform: Platform name ('linkedin', 'twitter', 'instagram', 'tiktok')
    """
    logger.info(f"📱 Fetching {platform} data for competitor {competitor_id}")
    
    async with get_session() as session:
        try:
            # Get competitor
            result = await session.execute(
                select(Competitor).where(Competitor.id == competitor_id)
            )
            competitor = result.scalar_one_or_none()
            
            if not competitor:
                raise ValueError(f"Competitor {competitor_id} not found")
            
            # Get confirmed social URL for the specific platform
            platform_url_type = f"social_{platform}"
            url_result = await session.execute(
                select(CompetitorUrl)
                .where(
                    CompetitorUrl.competitor_id == competitor_id,
                    CompetitorUrl.status == 'confirmed',
                    CompetitorUrl.url_type == platform_url_type
                )
            )
            platform_url = url_result.scalar_one_or_none()
            
            if not platform_url:
                raise ValueError(f"No confirmed {platform} URL found for {competitor.name}")
            
            # Initialize social media fetcher
            social_config = {
                'TWITTER_BEARER_TOKEN': os.getenv('TWITTER_BEARER_TOKEN'),
                'LINKEDIN_EMAIL': os.getenv('LINKEDIN_EMAIL'),
                'LINKEDIN_PASSWORD': os.getenv('LINKEDIN_PASSWORD'),
                'INSTAGRAM_USERNAME': os.getenv('INSTAGRAM_USERNAME'),
                'INSTAGRAM_PASSWORD': os.getenv('INSTAGRAM_PASSWORD')
            }
            
            social_fetcher = SocialMediaFetcher(config=social_config)
            
            # Fetch platform-specific data
            if platform == 'linkedin':
                platform_data = await social_fetcher.fetch_linkedin_data(platform_url.url)
            elif platform == 'twitter':
                platform_data = await social_fetcher.fetch_twitter_data(platform_url.url)
            elif platform == 'instagram':
                platform_data = await social_fetcher.fetch_instagram_data(platform_url.url)
            elif platform == 'tiktok':
                platform_data = await social_fetcher.fetch_tiktok_data(platform_url.url)
            else:
                raise ValueError(f"Unsupported platform: {platform}")
            
            # Save to database
            existing_result = await session.execute(
                select(SocialMediaData)
                .where(
                    SocialMediaData.competitor_id == competitor_id,
                    SocialMediaData.platform == platform_url_type
                )
            )
            existing_data = existing_result.scalar_one_or_none()
            
            if existing_data:
                # Update existing record
                await session.execute(
                    update(SocialMediaData)
                    .where(
                        SocialMediaData.competitor_id == competitor_id,
                        SocialMediaData.platform == platform_url_type
                    )
                    .values(
                        profile_url=platform_data.get('profile_url', ''),
                        username=platform_data.get('username', ''),
                        followers_count=platform_data.get('followers_count', 0),
                        following_count=platform_data.get('following_count', 0),
                        posts_count=platform_data.get('posts_count', 0),
                        latest_posts=platform_data.get('latest_posts', []),
                        profile_info=platform_data,
                        engagement_metrics=platform_data.get('engagement_metrics', {}),
                        last_updated_at=datetime.now(timezone.utc),
                        fetch_status='success',
                        error_message=None
                    )
                )
            else:
                # Create new record
                social_data = SocialMediaData(
                    competitor_id=competitor.id,
                    platform=platform_url_type,
                    profile_url=platform_data.get('profile_url', ''),
                    username=platform_data.get('username', ''),
                    followers_count=platform_data.get('followers_count', 0),
                    following_count=platform_data.get('following_count', 0),
                    posts_count=platform_data.get('posts_count', 0),
                    latest_posts=platform_data.get('latest_posts', []),
                    profile_info=platform_data,
                    engagement_metrics=platform_data.get('engagement_metrics', {}),
                    fetch_status='success'
                )
                session.add(social_data)
            
            await session.commit()
            
            return {
                'success': True,
                'competitor_id': competitor_id,
                'competitor_name': competitor.name,
                'platform': platform,
                'data': platform_data
            }
            
        except Exception as e:
            logger.error(f"❌ {platform} fetch failed for competitor {competitor_id}: {e}")
            raise

async def get_social_data(competitor_id: str) -> Dict[str, Any]:
    """
    Get stored social media data for a competitor
    
    Args:
        competitor_id: UUID of the competitor
    """
    logger.info(f"📊 Getting social media data for competitor {competitor_id}")
    
    async with get_session() as session:
        try:
            # Get competitor
            result = await session.execute(
                select(Competitor).where(Competitor.id == competitor_id)
            )
            competitor = result.scalar_one_or_none()
            
            if not competitor:
                raise ValueError(f"Competitor {competitor_id} not found")
            
            # Get all social media data
            social_data_result = await session.execute(
                select(SocialMediaData)
                .where(SocialMediaData.competitor_id == competitor_id)
                .order_by(SocialMediaData.last_updated_at.desc())
            )
            social_data_records = social_data_result.scalars().all()
            
            # Format response
            platforms_data = {}
            total_followers = 0
            
            for record in social_data_records:
                platform_name = record.platform.replace('social_', '')
                
                platforms_data[platform_name] = {
                    'id': str(record.id),
                    'platform': record.platform,
                    'profile_url': record.profile_url,
                    'username': record.username,
                    'followers_count': record.followers_count or 0,
                    'following_count': record.following_count or 0,
                    'posts_count': record.posts_count or 0,
                    'latest_posts': record.latest_posts or [],
                    'engagement_metrics': record.engagement_metrics or {},
                    'fetch_status': record.fetch_status,
                    'fetched_at': record.fetched_at.isoformat() if record.fetched_at else None,
                    'last_updated_at': record.last_updated_at.isoformat() if record.last_updated_at else None,
                    'error_message': record.error_message
                }
                
                if record.followers_count:
                    total_followers += record.followers_count
            
            return {
                'success': True,
                'competitor_id': competitor_id,
                'competitor_name': competitor.name,
                'platforms_data': platforms_data,
                'summary': {
                    'total_platforms': len(platforms_data),
                    'total_followers': total_followers,
                    'platforms_with_data': len([p for p in platforms_data.values() if p['fetch_status'] == 'success'])
                },
                'last_updated': max([p.get('last_updated_at', '') for p in platforms_data.values()]) if platforms_data else None
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get social data for competitor {competitor_id}: {e}")
            raise

def handler(event, context):
    """
    Lambda handler for social media data fetching
    
    Event formats:
    1. Fetch all: {"action": "fetch_all", "competitor_id": "uuid"}  
    2. Fetch specific: {"action": "fetch_platform", "competitor_id": "uuid", "platform": "linkedin"}
    3. Get data: {"action": "get_data", "competitor_id": "uuid"}
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
            if action == 'fetch_all':
                result = await fetch_social_data(competitor_id)
            elif action == 'fetch_platform':
                platform = event_data.get('platform')
                if not platform:
                    raise ValueError("Platform parameter required for fetch_platform action")
                result = await fetch_platform_data(competitor_id, platform)
            elif action == 'get_data':
                result = await get_social_data(competitor_id)
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