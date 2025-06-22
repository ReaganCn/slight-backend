#!/usr/bin/env python3
"""
🧪 Simple URL Discovery Test with LLM Selection Options
=====================================================
Test the simplified workflow: Search → LLM Rank → LLM Select

Key Features:
• Search engines do implicit categorization
• LLM ranks top 10 most relevant URLs per category  
• LLM selects single best URL from top 10
• Configurable LLM selection for each step
"""

import asyncio
import os
import sys
sys.path.insert(0, 'src')

from services.url_discovery import URLDiscoveryService

# Test configuration
COMPANY_NAME = "Notion"
BASE_URL = "https://www.notion.so"
CATEGORIES = ['pricing', 'features', 'blog']

async def test_llm_combinations():
    """Test different LLM combinations for ranking and selection."""
    print("🧪 Testing Different LLM Combinations")
    print("=====================================")
    print(f"🏢 Company: {COMPANY_NAME}")
    print(f"🌐 Base URL: {BASE_URL}")
    print(f"🏷️ Categories: {CATEGORIES}")
    print()
    
    # Initialize service
    service = URLDiscoveryService(
        openai_api_key=os.getenv('OPENAI_API_KEY'),
        cohere_api_key=os.getenv('COHERE_API_KEY'),
        google_cse_api_key=os.getenv('GOOGLE_CSE_API_KEY'),
        google_cse_id=os.getenv('GOOGLE_CSE_ID'),
        brave_api_key=os.getenv('BRAVE_API_KEY')
    )
    
    # Test different LLM combinations
    combinations = [
        ("cohere", "cohere", "🚀 Fast & Cost-Effective"),
        ("cohere", "openai", "🎯 Fast Ranking + Premium Selection"),
        ("openai", "cohere", "🔍 Premium Ranking + Fast Selection"),
        ("openai", "openai", "💎 Premium Quality (Higher Cost)")
    ]
    
    results = {}
    
    for ranking_llm, selection_llm, description in combinations:
        print(f"\n🤖 Testing: {ranking_llm.upper()} ranking → {selection_llm.upper()} selection")
        print(f"📝 {description}")
        
        try:
            discovered_urls = await service.discover_competitor_urls(
                competitor_name=COMPANY_NAME,
                base_url=BASE_URL,
                search_depth="standard",
                categories=CATEGORIES,
                ranking_llm=ranking_llm,
                selection_llm=selection_llm
            )
            
            print(f"✅ Found {len(discovered_urls)} URLs:")
            for url in discovered_urls:
                category = url.get('category', 'unknown')
                print(f"   📄 {category}: {url.get('url')}")
            
            results[f"{ranking_llm}→{selection_llm}"] = discovered_urls
            
        except Exception as e:
            print(f"❌ Failed: {e}")
            results[f"{ranking_llm}→{selection_llm}"] = None
    
    # Compare results
    print(f"\n📊 Results Comparison")
    print("====================")
    for combo, urls in results.items():
        if urls:
            categories_found = [url.get('category') for url in urls]
            print(f"{combo}: {len(urls)} URLs - {categories_found}")
        else:
            print(f"{combo}: Failed")
    
    return results

async def test_workflow_steps():
    """Demonstrate the simplified workflow steps."""
    print("\n🔄 Simplified Workflow Demonstration")
    print("===================================")
    print("Step 1: Search engines do implicit categorization")
    print("        - 'Notion pricing' → pricing results")
    print("        - 'Notion features' → features results")
    print("        - 'Notion blog' → blog results")
    print()
    print("Step 2: LLM ranks top 10 most relevant URLs per category")
    print("        - Analyzes URL paths, titles, descriptions")
    print("        - Returns URLs ordered by relevance")
    print()
    print("Step 3: LLM selects single best URL from top 10")
    print("        - Chooses most valuable for competitive analysis")
    print("        - Returns final URL per category")
    print()
    
    # Run a single test to show the workflow
    service = URLDiscoveryService(
        cohere_api_key=os.getenv('COHERE_API_KEY'),
        openai_api_key=os.getenv('OPENAI_API_KEY'),
        brave_api_key=os.getenv('BRAVE_API_KEY')
    )
    
    print("🧪 Running workflow with Cohere ranking + OpenAI selection...")
    try:
        urls = await service.discover_competitor_urls(
            competitor_name=COMPANY_NAME,
            base_url=BASE_URL,
            categories=['pricing'],  # Just test pricing for demo
            ranking_llm="cohere",
            selection_llm="openai"
        )
        
        if urls:
            url = urls[0]
            print(f"✅ Result: {url.get('category')} → {url.get('url')}")
            print(f"   Ranking LLM: {url.get('ranking_llm')}")
            print(f"   Selection LLM: {url.get('selection_llm')}")
            print(f"   Method: {url.get('discovery_method')}")
        else:
            print("⚠️ No URLs found")
            
    except Exception as e:
        print(f"❌ Workflow failed: {e}")

async def main():
    """Main test runner."""
    print("🚀 Simple URL Discovery Test")
    print("============================")
    print("Testing the new simplified workflow with configurable LLM options")
    print()
    
    # Check API keys
    cohere_key = os.getenv('COHERE_API_KEY')
    openai_key = os.getenv('OPENAI_API_KEY')
    
    print("🔑 API Key Status:")
    print(f"   Cohere: {'✅' if cohere_key else '❌'}")
    print(f"   OpenAI: {'✅' if openai_key else '❌'}")
    
    if not cohere_key and not openai_key:
        print("❌ No AI API keys found. Please set COHERE_API_KEY or OPENAI_API_KEY")
        return
    
    # Run tests
    await test_workflow_steps()
    
    if cohere_key and openai_key:
        await test_llm_combinations()
    else:
        print("\n⚠️ Skipping LLM combinations test (need both Cohere and OpenAI keys)")
    
    print("\n🎉 Test completed!")
    print("\n💡 Key Benefits of Simplified Workflow:")
    print("   • Cleaner logic: Search engines handle categorization")
    print("   • Flexible LLM selection: Choose different models for each step")
    print("   • Cost optimization: Use fast models for ranking, premium for selection")
    print("   • High quality: LLM-driven relevance ensures best URL selection")

if __name__ == "__main__":
    asyncio.run(main()) 