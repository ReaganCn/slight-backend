#!/usr/bin/env python3
"""
Modular URL Discovery Test Script with Cohere-First AI Strategy
===============================================================

This script allows you to run different tests by commenting/uncommenting them.
The system is configured to use Cohere as the primary AI with OpenAI as fallback.

Available Tests:
- test_configuration_status()      # Check API keys and service status
- test_cohere_primary_discovery()  # Full URL discovery with Cohere-first
- test_ai_categorization_only()    # Test just the AI categorization
- test_search_backends_only()      # Test just the search APIs
- test_performance_comparison()    # Compare different AI configurations
"""

import asyncio
import sys
import os
import time
from typing import Dict, Any

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from services.url_discovery import URLDiscoveryService

# =============================================================================
# TEST CONFIGURATION - Comment/Uncomment tests you want to run
# =============================================================================

# ✅ QUICK TEST (Recommended for development)
TESTS_TO_RUN = [
    "test_configuration_status",      # Always good to run first
    "test_cohere_primary_discovery",  # Main test with Cohere-first
]

# 🧠 AI-ONLY TESTS (Uncomment to test just AI categorization)
# TESTS_TO_RUN = [
#     "test_configuration_status",
#     "test_ai_categorization_only",
# ]

# 🔍 SEARCH-ONLY TESTS (Uncomment to test just search backends)
# TESTS_TO_RUN = [
#     "test_configuration_status", 
#     "test_search_backends_only",
# ]

# ⚡ PERFORMANCE COMPARISON (Uncomment to compare AI configurations)
# TESTS_TO_RUN = [
#     "test_configuration_status",
#     "test_performance_comparison",
# ]

# 🚀 FULL TEST SUITE (Uncomment to run everything - takes longer)
# TESTS_TO_RUN = [
#     "test_configuration_status",
#     "test_cohere_primary_discovery", 
#     "test_ai_categorization_only",
#     "test_search_backends_only", 
#     "test_performance_comparison",
# ]

# 🎯 CUSTOM TEST SELECTION (Edit this list to create your own combination)
# TESTS_TO_RUN = [
#     "test_configuration_status",
#     # Add any combination of tests you want
# ]

# =============================================================================
# TEST FUNCTIONS
# =============================================================================

async def test_configuration_status():
    """Test 1: Check API configuration and service status"""
    print("🔧 Test 1: Configuration & Service Status")
    print("--------------------------------------------------")
    
    # API Key Status
    api_keys = {
        'Google Custom Search': os.getenv('GOOGLE_CSE_API_KEY') and os.getenv('GOOGLE_CSE_ID'),
        'Brave Search API': os.getenv('BRAVE_API_KEY'),
        'OpenAI API': os.getenv('OPENAI_API_KEY'),
        'Cohere API': os.getenv('COHERE_API_KEY')
    }
    
    print("🔑 API Key Status:")
    for service, available in api_keys.items():
        status = "✅" if available else "❌"
        print(f"   {service}: {status}")
    
    # Initialize service to get configuration details
    service = URLDiscoveryService(
        openai_api_key=os.getenv('OPENAI_API_KEY'),
        google_cse_api_key=os.getenv('GOOGLE_CSE_API_KEY'),
        google_cse_id=os.getenv('GOOGLE_CSE_ID'),
        brave_api_key=os.getenv('BRAVE_API_KEY'),
        cohere_api_key=os.getenv('COHERE_API_KEY')
    )
    
    # Show predefined categories
    categories = service.get_predefined_categories()
    print(f"\n🏷️ Predefined Categories ({len(categories)} total):")
    for cat_name, cat_config in categories.items():
        desc = cat_config['description']
        patterns = len(cat_config['patterns'])
        print(f"   • {cat_name}: {desc} ({patterns} patterns)")
    
    # AI Strategy
    ai_status = service.get_ai_status()
    print(f"\n🤖 AI Configuration (Cohere-First):")
    if ai_status['cohere_available'] and ai_status['openai_available']:
        print("   1️⃣ Cohere (Primary) → 2️⃣ OpenAI (Fallback) → 3️⃣ Pattern Matching")
    elif ai_status['cohere_available']:
        print("   1️⃣ Cohere (Primary) → 2️⃣ Pattern Matching")
        print("   🎯 Cohere-first configuration active!")
    elif ai_status['openai_available']:
        print("   1️⃣ OpenAI → 2️⃣ Pattern Matching")
    else:
        print("   1️⃣ Pattern Matching Only")
    
    # Search Backends
    backends = service.get_available_search_backends()
    print(f"\n🔍 Search Backend Status:")
    for backend in backends:
        print(f"   {backend}: ✅")
    
    print("\n✅ Configuration test complete!")

async def test_cohere_primary_discovery():
    """Test 2: Full URL discovery with Cohere as primary AI"""
    print("🚀 Test 2: Cohere-Primary URL Discovery")
    print("-" * 50)
    
    # Initialize with Cohere-first (no OpenAI)
    discovery_service = URLDiscoveryService(
        openai_api_key=None,  # Disable OpenAI
        google_cse_api_key=os.getenv('GOOGLE_CSE_API_KEY'),
        google_cse_id=os.getenv('GOOGLE_CSE_ID'),
        brave_api_key=os.getenv('BRAVE_API_KEY'),
        cohere_api_key=os.getenv('COHERE_API_KEY')
    )
    
    # Test parameters
    test_company = "Notion"
    test_website = "https://www.notion.so"
    
    print(f"🎯 Testing Company: {test_company}")
    print(f"🌐 Website: {test_website}")
    print("🤖 AI Strategy: Cohere-First (OpenAI disabled)")
    print()
    
    start_time = time.time()
    
    try:
        # Run discovery with quick mode for faster testing
        discovered_urls = await discovery_service.discover_competitor_urls(
            competitor_name=test_company,
            base_url=test_website,
            search_depth="quick"  # Faster for testing
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Discovery completed in {duration:.1f} seconds!")
        print(f"📊 Total URLs discovered: {len(discovered_urls)}")
        
        # Analyze results
        methods_used = {}
        categories = {}
        confidence_scores = []
        
        for url_data in discovered_urls:
            method = url_data.get('discovery_method', 'unknown')
            category = url_data.get('category', 'unknown')
            confidence = url_data.get('confidence_score', 0)
            
            methods_used[method] = methods_used.get(method, 0) + 1
            categories[category] = categories.get(category, 0) + 1
            confidence_scores.append(confidence)
        
        print(f"\n📈 Results Analysis:")
        print(f"   AI Methods Used:")
        for method, count in methods_used.items():
            print(f"      • {method}: {count} URLs")
        
        print(f"\n📁 Categories Discovered:")
        for category, count in categories.items():
            print(f"      • {category}: {count} URLs")
        
        if confidence_scores:
            avg_confidence = sum(confidence_scores) / len(confidence_scores)
            print(f"\n🎯 Quality Metrics:")
            print(f"   • Average confidence: {avg_confidence:.2f}")
            print(f"   • Confidence range: {min(confidence_scores):.2f} - {max(confidence_scores):.2f}")
        
        # Show sample results
        if discovered_urls:
            print(f"\n🔍 Sample Discovered URLs:")
            for i, url_data in enumerate(discovered_urls[:3], 1):
                url = url_data.get('url', 'Unknown')
                category = url_data.get('category', 'unknown')
                confidence = url_data.get('confidence_score', 0)
                method = url_data.get('discovery_method', 'unknown')
                print(f"   {i}. {url}")
                print(f"      📂 {category} | 🎯 {confidence:.2f} | 🤖 {method}")
            
            if len(discovered_urls) > 3:
                print(f"      ... and {len(discovered_urls) - 3} more URLs")
        
        # Performance summary
        print(f"\n⚡ Performance Summary:")
        print(f"   • Total time: {duration:.1f} seconds")
        print(f"   • URLs per second: {len(discovered_urls)/duration:.1f}")
        print(f"   • Average time per URL: {duration/max(len(discovered_urls), 1):.1f} seconds")
        
        if 'cohere_enhanced' in methods_used:
            print(f"   🎉 Cohere processed {methods_used['cohere_enhanced']} URLs successfully!")
        
    except Exception as e:
        print(f"❌ Discovery failed: {e}")
        print("   Check your API keys and network connection")
    
    print("\n✅ Cohere-primary discovery test complete!\n")

async def test_ai_categorization_only():
    """Test 3: Test AI categorization without full discovery"""
    print("🧠 Test 3: AI Categorization Only")
    print("-" * 50)
    
    # Initialize with Cohere-first
    discovery_service = URLDiscoveryService(
        openai_api_key=None,  # Cohere-first
        cohere_api_key=os.getenv('COHERE_API_KEY')
    )
    
    # Test URLs for categorization
    test_urls = [
        {
            'url': 'https://notion.so/pricing',
            'title': 'Notion Pricing Plans - Choose Your Plan',
            'snippet': 'Flexible pricing for teams of all sizes. Free plan available.',
            'source': 'manual_test'
        },
        {
            'url': 'https://notion.so/product',
            'title': 'Notion Features - All-in-one workspace',
            'snippet': 'Discover powerful features for notes, docs, and collaboration.',
            'source': 'manual_test'
        },
        {
            'url': 'https://notion.so/blog',
            'title': 'Notion Blog - Updates and Insights',
            'snippet': 'Latest updates, tips, and insights from the Notion team.',
            'source': 'manual_test'
        }
    ]
    
    print("🤖 Testing Cohere AI categorization on sample URLs...")
    print()
    
    for i, url_data in enumerate(test_urls, 1):
        print(f"🔍 Test {i}: {url_data['url']}")
        
        try:
            start_time = time.time()
            category, confidence, method = await discovery_service._ai_categorize_url_with_fallback(
                url_data, "Notion"
            )
            duration = time.time() - start_time
            
            print(f"   ✅ Category: {category}")
            print(f"   🎯 Confidence: {confidence:.2f}")
            print(f"   🤖 Method: {method}")
            print(f"   ⚡ Time: {duration:.2f}s")
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")
        
        print()
    
    print("✅ AI categorization test complete!\n")

async def test_search_backends_only():
    """Test 4: Test search backends without AI processing"""
    print("🔍 Test 4: Search Backends Only")
    print("-" * 50)
    
    discovery_service = URLDiscoveryService(
        google_cse_api_key=os.getenv('GOOGLE_CSE_API_KEY'),
        google_cse_id=os.getenv('GOOGLE_CSE_ID'),
        brave_api_key=os.getenv('BRAVE_API_KEY')
    )
    
    test_queries = [
        "Notion pricing",
        "site:notion.so features"
    ]
    
    print("🔍 Testing search backends with sample queries...")
    print()
    
    for i, query in enumerate(test_queries, 1):
        print(f"Query {i}: '{query}'")
        
        # Test Google Custom Search
        if os.getenv('GOOGLE_CSE_API_KEY') and os.getenv('GOOGLE_CSE_ID'):
            try:
                start_time = time.time()
                results = await discovery_service._google_custom_search(query, 5)
                duration = time.time() - start_time
                print(f"   ✅ Google Custom Search: {len(results)} results in {duration:.1f}s")
            except Exception as e:
                print(f"   ❌ Google Custom Search failed: {e}")
        
        # Test Brave Search
        if os.getenv('BRAVE_API_KEY'):
            try:
                start_time = time.time()
                results = await discovery_service._brave_search_api(query, 5)
                duration = time.time() - start_time
                print(f"   ✅ Brave Search: {len(results)} results in {duration:.1f}s")
            except Exception as e:
                print(f"   ❌ Brave Search failed: {e}")
        
        print()
    
    print("✅ Search backends test complete!\n")

async def test_performance_comparison():
    """Test 5: Compare different AI configurations"""
    print("⚡ Test 5: Performance Comparison")
    print("-" * 50)
    
    test_url = {
        'url': 'https://notion.so/pricing',
        'title': 'Notion Pricing Plans',
        'snippet': 'Choose the right plan for your team',
        'source': 'performance_test'
    }
    
    configurations = [
        ("Cohere Only", {"cohere_api_key": os.getenv('COHERE_API_KEY')}),
        ("OpenAI Only", {"openai_api_key": os.getenv('OPENAI_API_KEY')}),
        ("Cohere + OpenAI", {
            "cohere_api_key": os.getenv('COHERE_API_KEY'),
            "openai_api_key": os.getenv('OPENAI_API_KEY')
        })
    ]
    
    print("🏁 Comparing AI configuration performance...")
    print()
    
    for config_name, config_params in configurations:
        print(f"Testing: {config_name}")
        
        try:
            service = URLDiscoveryService(**config_params)
            
            start_time = time.time()
            category, confidence, method = await service._ai_categorize_url_with_fallback(
                test_url, "Notion"
            )
            duration = time.time() - start_time
            
            print(f"   ✅ Result: {category} ({confidence:.2f})")
            print(f"   🤖 Method: {method}")
            print(f"   ⚡ Time: {duration:.2f}s")
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")
        
        print()
    
    print("✅ Performance comparison complete!\n")

# =============================================================================
# MAIN EXECUTION
# =============================================================================

async def main():
    """Run selected tests"""
    print("🚀 Modular URL Discovery Test Suite")
    print("=" * 60)
    print("🎯 Configuration: Cohere-First AI Strategy")
    print("📝 Edit TESTS_TO_RUN list to select which tests to run")
    print("=" * 60)
    print()
    
    # Map test names to functions
    test_functions = {
        "test_configuration_status": test_configuration_status,
        "test_cohere_primary_discovery": test_cohere_primary_discovery,
        "test_ai_categorization_only": test_ai_categorization_only,
        "test_search_backends_only": test_search_backends_only,
        "test_performance_comparison": test_performance_comparison,
    }
    
    # Run selected tests
    for test_name in TESTS_TO_RUN:
        if test_name in test_functions:
            await test_functions[test_name]()
        else:
            print(f"⚠️ Unknown test: {test_name}")
    
    print("=" * 60)
    print("🎉 All selected tests completed!")
    print()
    print("💡 Tips:")
    print("   • Edit TESTS_TO_RUN to run different test combinations")
    print("   • Cohere is configured as primary AI (OpenAI as fallback)")
    print("   • Use 'quick' search depth for faster testing")
    print("   • Check logs for detailed AI fallback behavior")

if __name__ == "__main__":
    asyncio.run(main()) 