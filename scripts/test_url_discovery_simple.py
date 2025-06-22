#!/usr/bin/env python3
"""
Simple test script for URL Discovery with reliable search APIs.
Demonstrates Google Custom Search and Brave Search working without DuckDuckGo.
"""

import asyncio
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from services.url_discovery import URLDiscoveryService

async def test_reliable_url_discovery():
    """Test URL discovery with reliable search backends (no DuckDuckGo)"""
    print("🔍 Testing Reliable URL Discovery Service")
    print("="*50)
    
    # Initialize service with reliable search APIs
    openai_api_key = os.getenv('OPENAI_API_KEY')
    google_cse_api_key = os.getenv('GOOGLE_CSE_API_KEY')
    google_cse_id = os.getenv('GOOGLE_CSE_ID')
    brave_api_key = os.getenv('BRAVE_API_KEY')
    
    print("🔑 Search API Configuration:")
    print(f"   Google Custom Search: {'✅ Configured' if google_cse_api_key and google_cse_id else '❌ Missing'}")
    print(f"   Brave Search API: {'✅ Configured' if brave_api_key else '❌ Missing'}")
    print(f"   OpenAI API: {'✅ Configured' if openai_api_key else '❌ Missing'}")
    print()
    
    discovery_service = URLDiscoveryService(
        openai_api_key=openai_api_key,
        google_cse_api_key=google_cse_api_key,
        google_cse_id=google_cse_id,
        brave_api_key=brave_api_key
    )
    
    # Show available search backends
    backends = discovery_service.get_available_search_backends()
    backend_info = discovery_service.get_search_backend_info()
    
    print("🔧 Available Search Backends:")
    for backend in backends:
        info = backend_info.get(backend, {})
        priority = info.get('priority', '?')
        daily_limit = info.get('daily_limit', '?')
        if daily_limit == float('inf'):
            daily_limit = 'Unlimited'
        print(f"   {priority}. {backend.replace('_', ' ').title()}: {daily_limit} queries/day")
    print()
    
    # Test URL discovery
    print("🎯 Testing URL Discovery:")
    test_company = "Cursor"
    test_website = "https://www.cursor.com"
    
    print(f"   Company: {test_company}")
    print(f"   Website: {test_website}")
    print("   Discovering URLs...")
    
    try:
        discovered_urls = await discovery_service.discover_competitor_urls(
            competitor_name=test_company,
            base_url=test_website,
            search_depth="standard"
        )
        
        print(f"✅ Discovery completed successfully!")
        print(f"📊 Total URLs found: {len(discovered_urls)}")
        
        # Group by category
        categories = {}
        for url_data in discovered_urls:
            category = url_data.get('category', 'unknown')
            if category not in categories:
                categories[category] = []
            categories[category].append(url_data)
        
        if categories:
            print("\n📁 URLs by Category:")
            for category, urls in categories.items():
                print(f"   {category.title()}: {len(urls)} URLs")
                for url_data in urls[:2]:  # Show first 2 URLs
                    confidence = url_data.get('confidence_score', 0)
                    source = url_data.get('source', 'unknown')
                    print(f"      • {url_data.get('url', 'N/A')}")
                    print(f"        Confidence: {confidence:.2f}, Source: {source}")
                if len(urls) > 2:
                    print(f"        ... and {len(urls) - 2} more")
        else:
            print("   No URLs discovered (likely due to API configuration)")
            
    except Exception as e:
        print(f"❌ Discovery failed: {e}")
        print("   This might be due to missing API keys or network issues")
    
    print("\n" + "="*50)
    print("🎉 Testing Complete!")
    print()
    print("💡 Key Benefits of New Architecture:")
    print("   • No more DuckDuckGo reliability issues")
    print("   • Google Custom Search: Premium quality results")
    print("   • Brave Search: Independent, privacy-focused alternative")
    print("   • Intelligent fallback mechanisms")
    print("   • Consistent performance and reliability")
    print()
    print("🔧 Setup Instructions:")
    if not google_cse_api_key or not google_cse_id:
        print("   1. Get Google Custom Search API:")
        print("      • Visit: https://developers.google.com/custom-search/v1/introduction")
        print("      • Create custom search engine: https://cse.google.com/cse/create/new")
        print("      • Add keys to .env file")
    if not brave_api_key:
        print("   2. Get Brave Search API:")
        print("      • Visit: https://brave.com/search/api/")
        print("      • Sign up for free account (2,000 queries/month)")
        print("      • Add key to .env file")

if __name__ == "__main__":
    asyncio.run(test_reliable_url_discovery()) 