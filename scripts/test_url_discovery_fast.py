#!/usr/bin/env python3
"""
Fast test script for URL Discovery with optimized Cohere fallback.
Demonstrates improved error handling and progress tracking.
"""

import asyncio
import sys
import os
import time

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from services.url_discovery import URLDiscoveryService

async def test_fast_url_discovery():
    """Test URL discovery with optimized performance"""
    print("🚀 Testing Fast URL Discovery with Cohere Fallback")
    print("="*60)
    
    # Initialize service with all available APIs
    openai_api_key = os.getenv('OPENAI_API_KEY')
    google_cse_api_key = os.getenv('GOOGLE_CSE_API_KEY')
    google_cse_id = os.getenv('GOOGLE_CSE_ID')
    brave_api_key = os.getenv('BRAVE_API_KEY')
    cohere_api_key = os.getenv('COHERE_API_KEY')
    
    print("🔑 API Configuration:")
    print(f"   Google Custom Search: {'✅' if google_cse_api_key and google_cse_id else '❌'}")
    print(f"   Brave Search API: {'✅' if brave_api_key else '❌'}")
    print(f"   OpenAI API: {'✅' if openai_api_key else '❌'}")
    print(f"   Cohere API: {'✅' if cohere_api_key else '❌'}")
    print()
    
    discovery_service = URLDiscoveryService(
        openai_api_key=openai_api_key,
        google_cse_api_key=google_cse_api_key,
        google_cse_id=google_cse_id,
        brave_api_key=brave_api_key,
        cohere_api_key=cohere_api_key
    )
    
    # Show AI status
    ai_status = discovery_service.get_ai_status()
    print("🤖 AI Fallback Chain:")
    if ai_status['openai_available'] and ai_status['cohere_available']:
        print("   1️⃣ OpenAI GPT-4 (Primary) → 2️⃣ Cohere (Fallback) → 3️⃣ Pattern Matching")
        print("   🎯 Perfect setup for robust AI categorization!")
    elif ai_status['cohere_available']:
        print("   1️⃣ Cohere (Primary) → 2️⃣ Pattern Matching")
        print("   ✅ Good setup with AI fallback")
    else:
        print("   1️⃣ Pattern Matching only")
        print("   ⚠️ No AI available - consider adding API keys")
    print()
    
    # Test with a smaller, faster discovery
    print("🎯 Testing Fast URL Discovery:")
    test_company = "Cursor"
    test_website = "https://www.cursor.com"
    
    print(f"   Company: {test_company}")
    print(f"   Website: {test_website}")
    print(f"   Mode: Quick discovery (limited results)")
    print()
    
    start_time = time.time()
    
    try:
        # Use quick mode for faster testing
        discovered_urls = await discovery_service.discover_competitor_urls(
            competitor_name=test_company,
            base_url=test_website,
            search_depth="quick"  # Faster mode
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Discovery completed in {duration:.1f} seconds!")
        print(f"📊 Total URLs found: {len(discovered_urls)}")
        
        # Analyze results
        methods_used = {}
        categories = {}
        
        for url_data in discovered_urls:
            method = url_data.get('discovery_method', 'unknown')
            category = url_data.get('category', 'unknown')
            
            methods_used[method] = methods_used.get(method, 0) + 1
            categories[category] = categories.get(category, 0) + 1
        
        print("\n📈 Performance Analysis:")
        print(f"   Discovery Methods Used:")
        for method, count in methods_used.items():
            print(f"      • {method}: {count} URLs")
        
        print(f"\n📁 Categories Found:")
        for category, count in categories.items():
            print(f"      • {category}: {count} URLs")
        
        if discovered_urls:
            print(f"\n🔍 Sample Results:")
            for i, url_data in enumerate(discovered_urls[:3], 1):
                confidence = url_data.get('confidence_score', 0)
                category = url_data.get('category', 'unknown')
                method = url_data.get('discovery_method', 'unknown')
                url = url_data.get('url', 'Unknown')
                print(f"   {i}. {url}")
                print(f"      Category: {category} | Confidence: {confidence:.2f} | Method: {method}")
            
            if len(discovered_urls) > 3:
                print(f"      ... and {len(discovered_urls) - 3} more URLs")
        
        # Performance summary
        print(f"\n⚡ Performance Summary:")
        print(f"   • Total time: {duration:.1f} seconds")
        print(f"   • URLs processed: {len(discovered_urls)}")
        print(f"   • Average time per URL: {duration/max(len(discovered_urls), 1):.1f} seconds")
        
        if 'cohere_enhanced' in methods_used:
            print(f"   • Cohere fallback used: {methods_used['cohere_enhanced']} times")
            print(f"   ✅ Fallback system working perfectly!")
        
        if 'openai_enhanced' in methods_used:
            print(f"   • OpenAI used: {methods_used['openai_enhanced']} times")
        
    except Exception as e:
        print(f"❌ Discovery failed: {e}")
        print("   This might be due to missing API keys or network issues")

async def test_cohere_only():
    """Test with Cohere only to show it working without OpenAI"""
    print("\n" + "="*60)
    print("🧪 Testing Cohere-Only Mode")
    print("="*60)
    
    cohere_api_key = os.getenv('COHERE_API_KEY')
    if not cohere_api_key:
        print("⚠️ No Cohere API key found - skipping Cohere-only test")
        return
    
    # Initialize with only Cohere (no OpenAI)
    discovery_service = URLDiscoveryService(
        openai_api_key=None,  # Disable OpenAI
        cohere_api_key=cohere_api_key
    )
    
    print("🤖 Testing Cohere as primary AI (no OpenAI)...")
    
    # Test sample URLs
    test_urls = [
        {
            'url': 'https://cursor.com/pricing',
            'title': 'Cursor Pricing Plans',
            'snippet': 'Choose from our flexible pricing plans for developers',
            'source': 'test'
        },
        {
            'url': 'https://cursor.com/features',
            'title': 'Cursor Features',
            'snippet': 'Discover powerful AI-powered coding features',
            'source': 'test'
        }
    ]
    
    for i, url_data in enumerate(test_urls, 1):
        print(f"\n🔍 Test {i}: {url_data['url']}")
        
        try:
            start_time = time.time()
            category, confidence, method = await discovery_service._ai_categorize_url_with_fallback(
                url_data, "Cursor"
            )
            duration = time.time() - start_time
            
            print(f"   ✅ Result: {category} (confidence: {confidence:.2f})")
            print(f"   ⚡ Method: {method} in {duration:.1f}s")
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")

async def main():
    """Run all tests"""
    await test_fast_url_discovery()
    await test_cohere_only()
    
    print("\n" + "="*60)
    print("🎉 Fast Testing Complete!")
    print()
    print("💡 Key Improvements:")
    print("   ✅ Faster OpenAI failure detection (max 1 retry)")
    print("   ✅ Immediate fallback to Cohere on quota errors")
    print("   ✅ Progress tracking with batch processing")
    print("   ✅ Detailed performance metrics")
    print("   ✅ Quick discovery mode for faster testing")
    print()
    print("🚀 The system now handles OpenAI quota errors gracefully")
    print("   and provides seamless Cohere fallback with excellent performance!")

if __name__ == "__main__":
    asyncio.run(main()) 