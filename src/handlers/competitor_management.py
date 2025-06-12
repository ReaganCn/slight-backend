import json
import logging
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import uuid

from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError

from database import get_session, ensure_connection
from models import User, Competitor

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

async def create_competitor(user_id: str, competitor_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new competitor"""
    async with get_session() as session:
        # Verify user exists
        user_result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Create new competitor
        competitor = Competitor(
            user_id=user.id,
            name=competitor_data['name'],
            website=competitor_data.get('website'),
            pricing_url=competitor_data.get('pricing_url'),
            description=competitor_data.get('description'),
            scrape_frequency_hours=competitor_data.get('scrape_frequency_hours', '6'),
            is_active=competitor_data.get('is_active', True)
        )
        
        session.add(competitor)
        
        try:
            await session.commit()
            await session.refresh(competitor)
            
            return {
                'success': True,
                'competitor': {
                    'id': str(competitor.id),
                    'name': competitor.name,
                    'website': competitor.website,
                    'pricing_url': competitor.pricing_url,
                    'description': competitor.description,
                    'scrape_frequency_hours': competitor.scrape_frequency_hours,
                    'is_active': competitor.is_active,
                    'created_at': competitor.created_at.isoformat(),
                    'last_scraped_at': competitor.last_scraped_at.isoformat() if competitor.last_scraped_at else None
                }
            }
        except IntegrityError as e:
            await session.rollback()
            logger.error(f"Failed to create competitor: {e}")
            raise ValueError("Failed to create competitor - data validation error")

async def get_competitors(user_id: str, active_only: bool = True) -> Dict[str, Any]:
    """Get all competitors for a user"""
    async with get_session() as session:
        query = select(Competitor).where(Competitor.user_id == user_id)
        if active_only:
            query = query.where(Competitor.is_active == True)
        
        result = await session.execute(query)
        competitors = result.scalars().all()
        
        competitors_data = []
        for competitor in competitors:
            competitors_data.append({
                'id': str(competitor.id),
                'name': competitor.name,
                'website': competitor.website,
                'pricing_url': competitor.pricing_url,
                'description': competitor.description,
                'scrape_frequency_hours': competitor.scrape_frequency_hours,
                'is_active': competitor.is_active,
                'created_at': competitor.created_at.isoformat(),
                'updated_at': competitor.updated_at.isoformat() if competitor.updated_at else None,
                'last_scraped_at': competitor.last_scraped_at.isoformat() if competitor.last_scraped_at else None
            })
        
        return {
            'success': True,
            'competitors': competitors_data,
            'total': len(competitors_data)
        }

async def get_competitor(competitor_id: str, user_id: str) -> Dict[str, Any]:
    """Get a specific competitor"""
    async with get_session() as session:
        result = await session.execute(
            select(Competitor).where(
                Competitor.id == competitor_id,
                Competitor.user_id == user_id
            )
        )
        competitor = result.scalar_one_or_none()
        
        if not competitor:
            raise ValueError(f"Competitor {competitor_id} not found")
        
        # Get recent scrape results count
        from models import ScrapeResult
        scrape_count_result = await session.execute(
            select(ScrapeResult).where(ScrapeResult.competitor_id == competitor.id)
        )
        scrape_results = scrape_count_result.scalars().all()
        
        return {
            'success': True,
            'competitor': {
                'id': str(competitor.id),
                'name': competitor.name,
                'website': competitor.website,
                'pricing_url': competitor.pricing_url,
                'description': competitor.description,
                'scrape_frequency_hours': competitor.scrape_frequency_hours,
                'is_active': competitor.is_active,
                'created_at': competitor.created_at.isoformat(),
                'updated_at': competitor.updated_at.isoformat() if competitor.updated_at else None,
                'last_scraped_at': competitor.last_scraped_at.isoformat() if competitor.last_scraped_at else None,
                'total_scrapes': len(scrape_results)
            }
        }

async def update_competitor(competitor_id: str, user_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update a competitor"""
    async with get_session() as session:
        # Check if competitor exists and belongs to user
        result = await session.execute(
            select(Competitor).where(
                Competitor.id == competitor_id,
                Competitor.user_id == user_id
            )
        )
        competitor = result.scalar_one_or_none()
        
        if not competitor:
            raise ValueError(f"Competitor {competitor_id} not found")
        
        # Update allowed fields
        allowed_fields = [
            'name', 'website', 'pricing_url', 'description', 
            'scrape_frequency_hours', 'is_active'
        ]
        
        update_values = {}
        for field, value in update_data.items():
            if field in allowed_fields and value is not None:
                update_values[field] = value
        
        if not update_values:
            raise ValueError("No valid fields to update")
        
        # Add updated timestamp
        update_values['updated_at'] = datetime.now(timezone.utc)
        
        # Perform update
        await session.execute(
            update(Competitor)
            .where(Competitor.id == competitor_id)
            .values(**update_values)
        )
        
        await session.commit()
        
        # Fetch updated competitor
        updated_result = await session.execute(
            select(Competitor).where(Competitor.id == competitor_id)
        )
        updated_competitor = updated_result.scalar_one()
        
        return {
            'success': True,
            'competitor': {
                'id': str(updated_competitor.id),
                'name': updated_competitor.name,
                'website': updated_competitor.website,
                'pricing_url': updated_competitor.pricing_url,
                'description': updated_competitor.description,
                'scrape_frequency_hours': updated_competitor.scrape_frequency_hours,
                'is_active': updated_competitor.is_active,
                'created_at': updated_competitor.created_at.isoformat(),
                'updated_at': updated_competitor.updated_at.isoformat() if updated_competitor.updated_at else None,
                'last_scraped_at': updated_competitor.last_scraped_at.isoformat() if updated_competitor.last_scraped_at else None
            }
        }

async def delete_competitor(competitor_id: str, user_id: str) -> Dict[str, Any]:
    """Delete a competitor (soft delete by setting is_active=False)"""
    async with get_session() as session:
        # Check if competitor exists and belongs to user
        result = await session.execute(
            select(Competitor).where(
                Competitor.id == competitor_id,
                Competitor.user_id == user_id
            )
        )
        competitor = result.scalar_one_or_none()
        
        if not competitor:
            raise ValueError(f"Competitor {competitor_id} not found")
        
        # Soft delete by setting is_active = False
        await session.execute(
            update(Competitor)
            .where(Competitor.id == competitor_id)
            .values(
                is_active=False,
                updated_at=datetime.now(timezone.utc)
            )
        )
        
        await session.commit()
        
        return {
            'success': True,
            'message': f"Competitor {competitor.name} has been deactivated"
        }

def handler(event, context):
    """
    Lambda handler for competitor management operations
    
    Supported operations:
    - POST /competitors: Create competitor
    - GET /competitors: List competitors
    - GET /competitors/{id}: Get specific competitor
    - PUT /competitors/{id}: Update competitor
    - DELETE /competitors/{id}: Delete (deactivate) competitor
    """
    async def async_handler():
        await ensure_connection()
        
        # Parse event
        http_method = event.get('httpMethod', 'GET')
        path_parameters = event.get('pathParameters') or {}
        query_parameters = event.get('queryStringParameters') or {}
        body = event.get('body')
        
        # Parse body if present
        if body:
            try:
                body_data = json.loads(body)
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON in request body")
        else:
            body_data = {}
        
        # Extract user_id (in real app, this would come from authentication)
        user_id = body_data.get('user_id') or query_parameters.get('user_id')
        if not user_id:
            raise ValueError("user_id is required")
        
        competitor_id = path_parameters.get('competitor_id')
        
        # Route to appropriate handler
        if http_method == 'POST' and not competitor_id:
            # Create competitor
            required_fields = ['name']
            for field in required_fields:
                if field not in body_data:
                    raise ValueError(f"Field '{field}' is required")
            
            result = await create_competitor(user_id, body_data)
            
        elif http_method == 'GET' and not competitor_id:
            # List competitors
            active_only = query_parameters.get('active_only', 'true').lower() == 'true'
            result = await get_competitors(user_id, active_only)
            
        elif http_method == 'GET' and competitor_id:
            # Get specific competitor
            result = await get_competitor(competitor_id, user_id)
            
        elif http_method == 'PUT' and competitor_id:
            # Update competitor
            if not body_data:
                raise ValueError("Request body is required for updates")
            
            result = await update_competitor(competitor_id, user_id, body_data)
            
        elif http_method == 'DELETE' and competitor_id:
            # Delete competitor
            result = await delete_competitor(competitor_id, user_id)
            
        else:
            raise ValueError(f"Unsupported operation: {http_method} {event.get('resource', '')}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
            },
            'body': json.dumps(result, default=str)
        }
    
    # Handle CORS preflight requests
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
            },
            'body': ''
        }
    
    # Run async handler
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(async_handler())
    except Exception as e:
        logger.error(f"Handler error: {e}")
        return {
            'statusCode': 400 if isinstance(e, ValueError) else 500,
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