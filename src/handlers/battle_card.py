import json
import logging
import os
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List
import uuid

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain_community.callbacks.manager import get_openai_callback
from sqlalchemy import select, desc

from database import get_session, ensure_connection
from models import User, Competitor, ScrapeResult, BattleCard

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class BattleCardGenerator:
    """Generate AI-powered battle cards using competitor data"""
    
    def __init__(self):
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not configured")
        
        self.llm = ChatOpenAI(
            model_name="gpt-4",
            temperature=0.1,
            openai_api_key=OPENAI_API_KEY,
            max_tokens=2000
        )
    
    async def generate_battle_card(self, user_id: str, competitor_ids: List[str] = None) -> Dict[str, Any]:
        """Generate a comprehensive battle card"""
        async with get_session() as session:
            # Get user info
            user_result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = user_result.scalar_one_or_none()
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            # Get competitors data
            if competitor_ids:
                competitors_query = select(Competitor).where(
                    Competitor.user_id == user_id,
                    Competitor.id.in_(competitor_ids),
                    Competitor.is_active == True
                )
            else:
                competitors_query = select(Competitor).where(
                    Competitor.user_id == user_id,
                    Competitor.is_active == True
                )
            
            competitors_result = await session.execute(competitors_query)
            competitors = competitors_result.scalars().all()
            
            if not competitors:
                raise ValueError("No competitors found for battle card generation")
            
            # Gather recent scrape data for each competitor
            competitor_data = []
            for competitor in competitors:
                # Get latest scrape results
                scrape_results_query = (
                    select(ScrapeResult)
                    .where(ScrapeResult.competitor_id == competitor.id)
                    .order_by(desc(ScrapeResult.scraped_at))
                    .limit(3)  # Get last 3 scrapes for trend analysis
                )
                scrape_results = await session.execute(scrape_results_query)
                recent_scrapes = scrape_results.scalars().all()
                
                competitor_info = {
                    'id': str(competitor.id),
                    'name': competitor.name,
                    'website': competitor.website,
                    'description': competitor.description,
                    'scrape_data': []
                }
                
                for scrape in recent_scrapes:
                    competitor_info['scrape_data'].append({
                        'scraped_at': scrape.scraped_at.isoformat(),
                        'prices': scrape.prices,
                        'features': scrape.features,
                        'status': scrape.scrape_status
                    })
                
                competitor_data.append(competitor_info)
            
            # Generate battle card content
            battle_card_content = await self._generate_content(competitor_data, user.name)
            
            # Save battle card
            battle_card = BattleCard(
                user_id=user.id,
                title=f"Competitive Analysis - {datetime.now().strftime('%Y-%m-%d')}",
                content=battle_card_content['content'],
                competitor_ids=[comp['id'] for comp in competitor_data],
                ai_model_used="gpt-4",
                generation_prompt=battle_card_content['prompt_used'],
                status="generated",
                generated_at=datetime.now(timezone.utc)
            )
            
            session.add(battle_card)
            await session.commit()
            
            return {
                'success': True,
                'battle_card_id': str(battle_card.id),
                'title': battle_card.title,
                'competitors_analyzed': len(competitor_data),
                'generation_metadata': {
                    'model_used': battle_card.ai_model_used,
                    'generated_at': battle_card.generated_at.isoformat(),
                    'token_usage': battle_card_content.get('token_usage', {})
                }
            }
    
    async def _generate_content(self, competitor_data: List[Dict], user_name: str) -> Dict[str, Any]:
        """Generate battle card content using GPT-4"""
        
        # Prepare competitor data summary for the prompt
        competitor_summary = []
        for comp in competitor_data:
            summary = f"**{comp['name']}**\n"
            if comp['website']:
                summary += f"Website: {comp['website']}\n"
            if comp['description']:
                summary += f"Description: {comp['description']}\n"
            
            # Add pricing data
            if comp['scrape_data']:
                latest_scrape = comp['scrape_data'][0]
                if latest_scrape['prices']:
                    summary += f"Pricing Data: {json.dumps(latest_scrape['prices'], indent=2)}\n"
                if latest_scrape['features']:
                    summary += f"Features: {json.dumps(latest_scrape['features'], indent=2)}\n"
            
            competitor_summary.append(summary)
        
        competitor_text = "\n\n".join(competitor_summary)
        
        # Create the battle card generation prompt
        system_prompt = """You are a competitive intelligence analyst creating a comprehensive battle card. 
        Your goal is to help sales teams understand the competitive landscape and position against competitors effectively.
        
        Create a detailed, actionable battle card in Markdown format that includes:
        1. Executive Summary
        2. Competitive Positioning Matrix
        3. Pricing Comparison & Analysis
        4. Feature Gaps & Advantages
        5. Sales Objection Handling
        6. Win/Loss Factors
        7. Recommended Messaging
        
        Be specific, data-driven, and focus on actionable insights."""
        
        user_prompt = f"""
        Generate a comprehensive battle card for {user_name}'s sales team based on the following competitor data:

        {competitor_text}

        Please provide:
        1. A clear competitive positioning analysis
        2. Pricing strategy recommendations
        3. Key differentiators to emphasize
        4. Common objections and responses
        5. Tactical advice for sales conversations

        Format the output as professional Markdown suitable for sales team reference.
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        try:
            with get_openai_callback() as cb:
                response = await self.llm.agenerate([messages])
                battle_card_content = response.generations[0][0].text
                
                return {
                    'content': battle_card_content,
                    'prompt_used': user_prompt,
                    'token_usage': {
                        'total_tokens': cb.total_tokens,
                        'prompt_tokens': cb.prompt_tokens,
                        'completion_tokens': cb.completion_tokens,
                        'total_cost': cb.total_cost
                    }
                }
        except Exception as e:
            logger.error(f"Failed to generate battle card content: {e}")
            raise

async def get_battle_card(battle_card_id: str, user_id: str) -> Dict[str, Any]:
    """Retrieve a specific battle card"""
    async with get_session() as session:
        result = await session.execute(
            select(BattleCard).where(
                BattleCard.id == battle_card_id,
                BattleCard.user_id == user_id
            )
        )
        battle_card = result.scalar_one_or_none()
        
        if not battle_card:
            raise ValueError(f"Battle card {battle_card_id} not found")
        
        return {
            'id': str(battle_card.id),
            'title': battle_card.title,
            'content': battle_card.content,
            'competitor_ids': battle_card.competitor_ids,
            'ai_model_used': battle_card.ai_model_used,
            'status': battle_card.status,
            'generated_at': battle_card.generated_at.isoformat(),
            'updated_at': battle_card.updated_at.isoformat() if battle_card.updated_at else None
        }

async def list_battle_cards(user_id: str, limit: int = 20) -> Dict[str, Any]:
    """List battle cards for a user"""
    async with get_session() as session:
        result = await session.execute(
            select(BattleCard)
            .where(BattleCard.user_id == user_id)
            .order_by(desc(BattleCard.generated_at))
            .limit(limit)
        )
        battle_cards = result.scalars().all()
        
        cards_data = []
        for card in battle_cards:
            cards_data.append({
                'id': str(card.id),
                'title': card.title,
                'status': card.status,
                'competitor_count': len(card.competitor_ids) if card.competitor_ids else 0,
                'generated_at': card.generated_at.isoformat(),
                'ai_model_used': card.ai_model_used
            })
        
        return {
            'battle_cards': cards_data,
            'total': len(cards_data)
        }

def handler(event, context):
    """
    Lambda handler for battle card generation and retrieval
    
    Event formats:
    1. Generate: {"action": "generate", "user_id": "uuid", "competitor_ids": ["uuid1", "uuid2"]}
    2. Get card: {"action": "get", "battle_card_id": "uuid", "user_id": "uuid"}
    3. List cards: {"action": "list", "user_id": "uuid", "limit": 20}
    """
    async def async_handler():
        await ensure_connection()
        
        # Parse event
        if isinstance(event, str):
            event = json.loads(event)
        
        action = event.get('action', 'generate')
        user_id = event.get('user_id')
        
        if not user_id:
            raise ValueError("user_id is required")
        
        if action == 'generate':
            competitor_ids = event.get('competitor_ids')
            generator = BattleCardGenerator()
            result = await generator.generate_battle_card(user_id, competitor_ids)
            
        elif action == 'get':
            battle_card_id = event.get('battle_card_id')
            if not battle_card_id:
                raise ValueError("battle_card_id is required for get action")
            result = await get_battle_card(battle_card_id, user_id)
            
        elif action == 'list':
            limit = event.get('limit', 20)
            result = await list_battle_cards(user_id, limit)
            
        else:
            raise ValueError(f"Invalid action: {action}")
        
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