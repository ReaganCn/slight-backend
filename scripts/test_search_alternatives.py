#!/usr/bin/env python3

"""
Test script showing reliable search alternatives to replace DuckDuckGo.
Demonstrates Google Custom Search and Brave Search API working together.
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from services.url_discovery import URLDiscoveryService

async def test_reliable_search_alternatives():
    """Test reliable search API alternatives (no DuckDuckGo)."""
    print("🔍 Testing Reliable Search API Alternatives")
    print("=" * 60)
    
    # Get API keys from environment
    openai_key = os.getenv('OPENAI_API_KEY')
    google_cse_key = os.getenv('GOOGLE_CSE_API_KEY')
    google_cse_id = os.getenv('GOOGLE_CSE_ID')
    brave_key = os.getenv('BRAVE_API_KEY')
    
    print("🔑 API Key Status:")
    print(f"   OpenAI API: {'✅ Configured' if openai_key else '❌ Missing'}")
    print(f"   Google CSE API: {'✅ Configured' if google_cse_key else '❌ Missing'}")
    print(f"   Google CSE ID: {'✅ Configured' if google_cse_id else '❌ Missing'}")
    print(f"   Brave Search API: {'✅ Configured' if brave_key else '❌ Missing'}")
    print()
    
    # Initialize URL discovery service
    discovery_service = URLDiscoveryService(
        openai_api_key=openai_key,
        google_cse_api_key=google_cse_key,
        google_cse_id=google_cse_id,
        brave_api_key=brave_key
    )
    
    # Show available backends
    available_backends = discovery_service.get_available_search_backends()
    backend_info = discovery_service.get_search_backend_info()
    
    print("🔧 Available Search Backends:")
    for backend in available_backends:
        info = backend_info.get(backend, {})
        priority = info.get('priority', '?')
        daily_limit = info.get('daily_limit', '?')
        if daily_limit == float('inf'):
            daily_limit = 'Unlimited'
        print(f"   {priority}. {backend.replace('_', ' ').title()}: {daily_limit} queries/day")
    print()
    
    # Test competitor URL discovery
    test_competitors = [
        ("Slack", "https://slack.com"),
        ("Notion", "https://notion.so"),
        ("Airtable", "https://airtable.com")
    ]
    
    print("🎯 Testing URL Discovery for Competitors:")
    print("-" * 50)
    
    for competitor_name, website in test_competitors:
        print(f"\n🏢 Testing: {competitor_name} ({website})")
        
        try:
            start_time = datetime.now()
            
            # Discover URLs
            discovered_urls = await discovery_service.discover_competitor_urls(
                competitor_name=competitor_name,
                base_url=website,
                search_depth="standard"
            )
            
            duration = (datetime.now() - start_time).total_seconds()
            
            print(f"   ⏱️  Discovery time: {duration:.2f}s")
            print(f"   📊 URLs found: {len(discovered_urls)}")
            
            # Show results by category
            categories = {}
            for url_data in discovered_urls:
                category = url_data.get('category', 'unknown')
                if category not in categories:
                    categories[category] = []
                categories[category].append(url_data)
            
            for category, urls in categories.items():
                print(f"   📁 {category.title()}: {len(urls)} URLs")
                for url_data in urls[:2]:  # Show first 2 URLs per category
                    confidence = url_data.get('confidence_score', 0)
                    source = url_data.get('source', 'unknown')
                    print(f"      • {url_data.get('url', 'N/A')} (confidence: {confidence:.2f}, source: {source})")
                if len(urls) > 2:
                    print(f"      ... and {len(urls) - 2} more")
            
            print(f"   ✅ Discovery successful for {competitor_name}")
            
        except Exception as e:
            print(f"   ❌ Discovery failed for {competitor_name}: {e}")
        
        # Add delay between tests to respect rate limits
        await asyncio.sleep(1)
    
    print("\n" + "=" * 60)
    print("🎉 Search Alternative Testing Complete!")
    print()
    
    # Show recommendations
    print("💡 Recommendations:")
    if google_cse_key and google_cse_id:
        print("   ✅ Google Custom Search API is configured - excellent choice!")
        print("      • 100 free queries/day")
        print("      • High-quality search results")
        print("      • Reliable and fast")
    else:
        print("   🔧 Consider setting up Google Custom Search API:")
        print("      • Visit: https://developers.google.com/custom-search/v1/introduction")
        print("      • Get API key and create custom search engine")
        print("      • 100 free queries/day with excellent quality")
    
    if brave_key:
        print("   ✅ Brave Search API is configured - great backup!")
        print("      • 2,000 free queries/month")
        print("      • Independent search index")
        print("      • Privacy-focused")
    else:
        print("   🔧 Consider setting up Brave Search API:")
        print("      • Visit: https://brave.com/search/api/")
        print("      • 2,000 free queries/month")
        print("      • Good quality independent search")
    
    print("\n   ⚠️  DuckDuckGo has been removed due to reliability issues:")
    print("      • Frequent timeouts and rate limiting")
    print("      • Inconsistent results")
    print("      • Better alternatives now available")

async def test_individual_search_backends():
    """Test each search backend individually."""
    print("\n🧪 Testing Individual Search Backends:")
    print("=" * 50)
    
    # Get API keys
    openai_key = os.getenv('OPENAI_API_KEY')
    google_cse_key = os.getenv('GOOGLE_CSE_API_KEY')
    google_cse_id = os.getenv('GOOGLE_CSE_ID')
    brave_key = os.getenv('BRAVE_API_KEY')
    
    discovery_service = URLDiscoveryService(
        openai_api_key=openai_key,
        google_cse_api_key=google_cse_key,
        google_cse_id=google_cse_id,
        brave_api_key=brave_key
    )
    
    test_query = "Slack pricing plans"
    
    # Test Google Custom Search
    if google_cse_key and google_cse_id:
        print(f"\n🔍 Testing Google Custom Search with query: '{test_query}'")
        try:
            start_time = datetime.now()
            results = await discovery_service._google_custom_search(test_query, 5)
            duration = (datetime.now() - start_time).total_seconds()
            
            print(f"   ⏱️  Response time: {duration:.2f}s")
            print(f"   📊 Results found: {len(results)}")
            
            for i, result in enumerate(results[:3], 1):
                print(f"   {i}. {result.get('title', 'No title')}")
                print(f"      URL: {result.get('url', 'No URL')}")
                print(f"      Snippet: {result.get('snippet', 'No snippet')[:100]}...")
            
            print("   ✅ Google Custom Search working perfectly!")
            
        except Exception as e:
            print(f"   ❌ Google Custom Search failed: {e}")
    else:
        print("\n⚠️  Google Custom Search API not configured")
    
    # Test Brave Search
    if brave_key:
        print(f"\n🦁 Testing Brave Search API with query: '{test_query}'")
        try:
            start_time = datetime.now()
            results = await discovery_service._brave_search_api(test_query, 5)
            duration = (datetime.now() - start_time).total_seconds()
            
            print(f"   ⏱️  Response time: {duration:.2f}s")
            print(f"   📊 Results found: {len(results)}")
            
            for i, result in enumerate(results[:3], 1):
                print(f"   {i}. {result.get('title', 'No title')}")
                print(f"      URL: {result.get('url', 'No URL')}")
                print(f"      Snippet: {result.get('snippet', 'No snippet')[:100]}...")
            
            print("   ✅ Brave Search API working perfectly!")
            
        except Exception as e:
            print(f"   ❌ Brave Search API failed: {e}")
    else:
        print("\n⚠️  Brave Search API not configured")
    
    # Test Sitemap Fallback
    print(f"\n🗺️  Testing Sitemap Fallback with Slack")
    try:
        start_time = datetime.now()
        results = await discovery_service._sitemap_fallback_search("https://slack.com", 5)
        duration = (datetime.now() - start_time).total_seconds()
        
        print(f"   ⏱️  Response time: {duration:.2f}s")
        print(f"   📊 URLs found: {len(results)}")
        
        for i, result in enumerate(results[:3], 1):
            print(f"   {i}. {result.get('title', 'No title')}")
            print(f"      URL: {result.get('url', 'No URL')}")
        
        print("   ✅ Sitemap fallback working as expected!")
        
    except Exception as e:
        print(f"   ❌ Sitemap fallback failed: {e}")

async def main():
    """Run all search alternative tests."""
    print("🚀 Starting Comprehensive Search Alternative Tests")
    print("=" * 70)
    print()
    
    await test_reliable_search_alternatives()
    await test_individual_search_backends()
    
    print("\n" + "=" * 70)
    print("🎯 Testing Summary:")
    print("   • DuckDuckGo removed due to reliability issues")
    print("   • Google Custom Search API: Premium quality (100 free/day)")
    print("   • Brave Search API: Great alternative (2,000 free/month)")
    print("   • Sitemap fallback: Always available as last resort")
    print()
    print("💡 Next Steps:")
    print("   1. Set up Google Custom Search API for best results")
    print("   2. Add Brave Search API as reliable backup")
    print("   3. Enjoy consistent, high-quality URL discovery!")

if __name__ == "__main__":
    asyncio.run(main()) 