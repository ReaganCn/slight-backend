import json
import logging
import asyncio
from typing import Dict, Any

from database import init_database, check_database_connection, ensure_connection
from models import User

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

async def run_migrations() -> Dict[str, Any]:
    """Run database migrations and setup"""
    try:
        # Ensure connection
        await ensure_connection()
        
        # Initialize database schema
        await init_database()
        
        # Verify connection and schema
        connection_ok = await check_database_connection()
        
        if not connection_ok:
            raise Exception("Database connection verification failed")
        
        return {
            'success': True,
            'message': 'Database migrations completed successfully',
            'schema_created': True
        }
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'message': 'Database migration failed'
        }

async def create_test_user() -> Dict[str, Any]:
    """Create a test user for development/testing"""
    from database import get_session
    
    async with get_session() as session:
        # Check if test user already exists
        from sqlalchemy import select
        
        result = await session.execute(
            select(User).where(User.email == "test@example.com")
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            return {
                'success': True,
                'message': 'Test user already exists',
                'user_id': str(existing_user.id)
            }
        
        # Create test user
        test_user = User(
            email="test@example.com",
            name="Test User",
            is_active=True
        )
        
        session.add(test_user)
        await session.commit()
        await session.refresh(test_user)
        
        return {
            'success': True,
            'message': 'Test user created successfully',
            'user_id': str(test_user.id),
            'email': test_user.email
        }

def handler(event, context):
    """
    Lambda handler for database migrations
    
    Event formats:
    1. Run migrations: {"action": "migrate"}
    2. Create test user: {"action": "create_test_user"}
    3. Health check: {"action": "health_check"}
    """
    async def async_handler():
        # Parse event
        if isinstance(event, str):
            event_data = json.loads(event)
        else:
            event_data = event
        
        action = event_data.get('action', 'migrate')
        
        if action == 'migrate':
            result = await run_migrations()
            
        elif action == 'create_test_user':
            # Run migrations first
            migration_result = await run_migrations()
            if not migration_result['success']:
                return migration_result
            
            # Create test user
            result = await create_test_user()
            
        elif action == 'health_check':
            # Just check database connection
            await ensure_connection()
            connection_ok = await check_database_connection()
            
            result = {
                'success': connection_ok,
                'message': 'Database health check completed',
                'database_connected': connection_ok
            }
            
        else:
            raise ValueError(f"Invalid action: {action}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps(result, default=str)
        }
    
    # Run async handler
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(async_handler())
    except Exception as e:
        logger.error(f"Migration handler error: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'message': 'Migration handler failed'
            })
        }
    finally:
        loop.close() 