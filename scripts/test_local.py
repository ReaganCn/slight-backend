#!/usr/bin/env python3
"""
Local testing script for Competitor Tracking SaaS Backend

This script tests the database connection, creates sample data,
and validates all major functionality locally.
"""

import asyncio
import json
import os
import sys
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

async def test_database_connection():
    """Test database connection"""
    print("🔗 Testing database connection...")
    
    try:
        from database import check_database_connection, ensure_connection
        
        await ensure_connection()
        result = await check_database_connection()
        
        if result:
            print("✅ Database connection successful")
            return True
        else:
            print("❌ Database connection failed")
            return False
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

async def run_migrations():
    """Run database migrations"""
    print("📦 Running database migrations...")
    
    try:
        from handlers.migrations import run_migrations
        
        result = await run_migrations()
        
        if result['success']:
            print("✅ Database migrations completed")
            return True
        else:
            print(f"❌ Migration failed: {result.get('error', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"❌ Migration error: {e}")
        return False

async def create_test_user():
    """Create a test user"""
    print("👤 Creating test user...")
    
    try:
        from handlers.migrations import create_test_user
        
        result = await create_test_user()
        
        if result['success']:
            print(f"✅ Test user created: {result.get('user_id')}")
            return result['user_id']
        else:
            print(f"❌ User creation failed: {result.get('error', 'Unknown error')}")
            return None
    except Exception as e:
        print(f"❌ User creation error: {e}")
        return None

async def test_competitor_management(user_id):
    """Test competitor CRUD operations"""
    print("🏢 Testing competitor management...")
    
    try:
        from handlers.competitor_management import create_competitor, get_competitors
        
        # Create test competitor
        competitor_data = {
            'name': 'Test Competitor',
            'website': 'https://example.com',
            'pricing_url': 'https://example.com/pricing',
            'description': 'A test competitor for validation',
            'scrape_frequency_hours': '6'
        }
        
        result = await create_competitor(user_id, competitor_data)
        
        if result['success']:
            competitor_id = result['competitor']['id']
            print(f"✅ Competitor created: {competitor_id}")
            
            # Test listing competitors
            competitors = await get_competitors(user_id)
            if competitors['success'] and competitors['total'] > 0:
                print(f"✅ Found {competitors['total']} competitors")
                return competitor_id
            else:
                print("❌ Failed to list competitors")
                return None
        else:
            print("❌ Failed to create competitor")
            return None
            
    except Exception as e:
        print(f"❌ Competitor management error: {e}")
        return None

def test_scraping_handler():
    """Test scraping handler (without actual scraping)"""
    print("🕷️ Testing scraping handler structure...")
    
    try:
        from handlers.scrape_competitor import CompetitorScraper
        
        # Just test class initialization
        scraper = CompetitorScraper()
        print("✅ Scraper class initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Scraping handler error: {e}")
        return False

def test_battle_card_handler():
    """Test battle card handler structure"""
    print("⚔️ Testing battle card handler structure...")
    
    try:
        from handlers.battle_card import BattleCardGenerator
        
        # Check if OpenAI key is configured
        openai_key = os.getenv('OPENAI_API_KEY')
        if not openai_key or openai_key == 'your-openai-api-key-here':
            print("⚠️ OpenAI API key not configured - skipping battle card test")
            return True
        
        # Test class initialization
        generator = BattleCardGenerator()
        print("✅ Battle card generator initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Battle card handler error: {e}")
        return False

async def cleanup_test_data(user_id, competitor_id=None):
    """Clean up test data"""
    print("🧹 Cleaning up test data...")
    
    try:
        if competitor_id:
            from handlers.competitor_management import delete_competitor
            
            result = await delete_competitor(competitor_id, user_id)
            if result['success']:
                print("✅ Test competitor deleted")
            else:
                print("⚠️ Failed to delete test competitor")
        
        print("✅ Cleanup completed")
        return True
    except Exception as e:
        print(f"⚠️ Cleanup error: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 Starting local tests for Competitor Tracking SaaS Backend")
    print("=" * 60)
    
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Environment variables loaded")
    except ImportError:
        print("⚠️ python-dotenv not installed - using system environment")
    
    test_results = []
    user_id = None
    competitor_id = None
    
    try:
        # Test 1: Database connection
        db_result = await test_database_connection()
        test_results.append(("Database Connection", db_result))
        
        if not db_result:
            print("❌ Cannot proceed without database connection")
            return False
        
        # Test 2: Run migrations
        migration_result = await run_migrations()
        test_results.append(("Database Migrations", migration_result))
        
        if not migration_result:
            print("❌ Cannot proceed without successful migration")
            return False
        
        # Test 3: Create test user
        user_id = await create_test_user()
        test_results.append(("Test User Creation", user_id is not None))
        
        if not user_id:
            print("❌ Cannot proceed without test user")
            return False
        
        # Test 4: Competitor management
        competitor_id = await test_competitor_management(user_id)
        test_results.append(("Competitor Management", competitor_id is not None))
        
        # Test 5: Scraping handler
        scraping_result = test_scraping_handler()
        test_results.append(("Scraping Handler", scraping_result))
        
        # Test 6: Battle card handler
        battle_card_result = test_battle_card_handler()
        test_results.append(("Battle Card Handler", battle_card_result))
        
        # Clean up
        await cleanup_test_data(user_id, competitor_id)
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = 0
        total = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name:<25} {status}")
            if result:
                passed += 1
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Your setup is ready for deployment.")
            return True
        else:
            print("⚠️ Some tests failed. Please check the configuration.")
            return False
            
    except Exception as e:
        print(f"❌ Critical error during testing: {e}")
        return False

if __name__ == "__main__":
    # Check if running from correct directory
    if not os.path.exists('src'):
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    # Run tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 