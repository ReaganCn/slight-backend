#!/usr/bin/env python3
"""
🧪 Simple URL Discovery Test with LLM Selection Options & Confidence Validation
==============================================================================
Test the simplified workflow: Search → LLM Rank → LLM Select
Enhanced with confidence validation to prevent wrong results for lesser-known companies

Key Features:
• Search engines do implicit categorization
• LLM ranks top 10 most relevant URLs per category  
• LLM selects single best URL from top 10
• Configurable LLM selection for each step
• Confidence validation prevents wrong results for unknown companies
"""

import asyncio
import os
import sys
sys.path.insert(0, 'src')

from services.url_discovery import URLDiscoveryService

# Test configuration with confidence validation examples
COMPANY_NAME = "Cursor"  # AI code editor startup - good test case for confidence validation
BASE_URL = "https://www.cursor.com"
CATEGORIES = ['pricing', 'features', 'blog']

# Test confidence thresholds
CONFIDENCE_THRESHOLDS = [0.3, 0.6, 0.8]  # Low, Medium, High

async def test_confidence_validation():
    """Test confidence validation with different thresholds."""
    print("🛡️ **Confidence Validation Test**")
    print("=================================")
    print("Testing how confidence thresholds prevent wrong results for lesser-known companies")
    print(f"Company: {COMPANY_NAME} (AI code editor startup)")
    print(f"Website: {BASE_URL}")
    print()
    
    # Check API keys
    cohere_key = os.getenv('COHERE_API_KEY')
    openai_key = os.getenv('OPENAI_API_KEY')
    
    if not cohere_key and not openai_key:
        print("❌ No AI API keys found. Confidence validation requires COHERE_API_KEY or OPENAI_API_KEY")
        print("💡 This feature validates brand recognition and filters unreliable results")
        return
    
    # Initialize service
    service = URLDiscoveryService(
        cohere_api_key=cohere_key,
        openai_api_key=openai_key,
        brave_api_key=os.getenv('BRAVE_API_KEY')
    )
    
    results = {}
    
    print("🔍 Testing different confidence thresholds:")
    print("-" * 50)
    
    for threshold in CONFIDENCE_THRESHOLDS:
        print(f"\n🎯 **Confidence Threshold: {threshold}**")
        print(f"   {'LOW' if threshold <= 0.4 else 'MEDIUM' if threshold <= 0.7 else 'HIGH'} confidence requirement")
        
        try:
            discovered_urls = await service.discover_competitor_urls(
                competitor_name=COMPANY_NAME,
                base_url=BASE_URL,
                search_depth="standard",
                categories=CATEGORIES,
                ranking_llm="cohere",
                selection_llm="cohere",
                min_confidence_threshold=threshold
            )
            
            if discovered_urls:
                print(f"   ✅ **PASSED** - Found {len(discovered_urls)} URLs")
                for url in discovered_urls:
                    category = url.get('category', 'unknown')
                    confidence = url.get('confidence_score', 0)
                    brand_conf = url.get('brand_confidence', 0)
                    print(f"      📄 {category}: {url.get('url')}")
                    print(f"         Overall: {confidence:.2f} | Brand: {brand_conf:.2f}")
                
                results[threshold] = {
                    'passed': True,
                    'count': len(discovered_urls),
                    'avg_confidence': sum(url.get('confidence_score', 0) for url in discovered_urls) / len(discovered_urls)
                }
            else:
                print(f"   ⚠️ **FILTERED OUT** - No URLs met confidence threshold")
                print(f"      This protects against potentially wrong results")
                results[threshold] = {'passed': False, 'reason': 'Below confidence threshold'}
                
        except Exception as e:
            print(f"   ❌ **ERROR**: {e}")
            results[threshold] = {'passed': False, 'reason': str(e)}
    
    # Summary
    print("\n📊 **Confidence Validation Summary**")
    print("===================================")
    
    for threshold, result in results.items():
        status = "✅ PASS" if result.get('passed') else "⚠️ FILTER"
        confidence_level = "LOW" if threshold <= 0.4 else "MEDIUM" if threshold <= 0.7 else "HIGH"
        
        print(f"{confidence_level:6} ({threshold}): {status}")
        if result.get('passed'):
            print(f"        Found {result['count']} URLs, avg confidence: {result['avg_confidence']:.2f}")
        else:
            print(f"        {result.get('reason', 'Unknown')}")
    
    print("\n💡 **Key Insights:**")
    print("   • Higher thresholds = fewer but more reliable results")
    print("   • Lower thresholds = more results but potentially less reliable")
    print("   • System protects against wrong results for unknown companies")
    print("   • Better to return no results than completely wrong results")

async def test_llm_combinations():
    """Test different LLM combinations for ranking and selection."""
    print("\n🤖 **LLM Combination Test**")
    print("==========================")
    print("Testing different LLM combinations for ranking and selection steps")
    print()
    
    # Check API keys
    cohere_key = os.getenv('COHERE_API_KEY')
    openai_key = os.getenv('OPENAI_API_KEY')
    
    if not cohere_key and not openai_key:
        print("❌ No AI API keys found for LLM testing")
        return
    
    # Test combinations
    combinations = []
    if cohere_key and openai_key:
        combinations = [
            ("cohere", "cohere", "Cohere → Cohere (cost-effective)"),
            ("cohere", "openai", "Cohere → OpenAI (hybrid approach)"),
            ("openai", "cohere", "OpenAI → Cohere (premium ranking)"),
            ("openai", "openai", "OpenAI → OpenAI (premium quality)")
        ]
    elif cohere_key:
        combinations = [("cohere", "cohere", "Cohere → Cohere (available)")]
    elif openai_key:
        combinations = [("openai", "openai", "OpenAI → OpenAI (available)")]
    
    service = URLDiscoveryService(
        cohere_api_key=cohere_key,
        openai_api_key=openai_key,
        brave_api_key=os.getenv('BRAVE_API_KEY')
    )
    
    for ranking_llm, selection_llm, description in combinations:
        print(f"🔍 Testing: {description}")
        
        try:
            discovered_urls = await service.discover_competitor_urls(
                competitor_name=COMPANY_NAME,
                base_url=BASE_URL,
                search_depth="standard",
                categories=['pricing'],  # Just test one category for speed
                ranking_llm=ranking_llm,
                selection_llm=selection_llm,
                min_confidence_threshold=0.6  # Medium confidence
            )
            
            if discovered_urls:
                url = discovered_urls[0]
                print(f"   ✅ Found: {url.get('url')}")
                print(f"   📊 Confidence: {url.get('confidence_score', 0):.2f}")
                print(f"   🤖 Ranking: {url.get('ranking_llm')} | Selection: {url.get('selection_llm')}")
            else:
                print(f"   ⚠️ No results (filtered by confidence validation)")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()

async def main():
    """Main test runner."""
    print("🚀 **Enhanced URL Discovery Test Suite**")
    print("========================================")
    print("Testing simplified workflow with confidence validation")
    print("Workflow: Search → LLM Rank → LLM Select → Confidence Filter")
    print()
    
    await test_confidence_validation()
    await test_llm_combinations()
    
    print("\n🎉 **Test completed!**")
    print("\n🛡️ **Confidence Validation Benefits:**")
    print("   • Prevents wrong results for lesser-known companies")
    print("   • Validates brand recognition before URL discovery")
    print("   • Uses confidence thresholds to filter unreliable results")
    print("   • Configurable thresholds for different use cases")
    print("   • Better user experience with reliable results")
    print("\n🤖 **LLM Selection Benefits:**")
    print("   • Choose different AI models for ranking vs selection")
    print("   • Cost optimization (Cohere for ranking, OpenAI for final selection)")
    print("   • Quality optimization (OpenAI for both steps)")
    print("   • Fallback support (automatic switching on API failures)")

if __name__ == "__main__":
    asyncio.run(main()) 