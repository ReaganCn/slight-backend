#!/usr/bin/env python3
"""
🎯 Confidence Validation Test Script
==================================
Test the confidence validation system with different types of companies:
- Well-known companies (should pass)
- Lesser-known startups (may fail confidence checks)
- Fictional companies (should fail validation)
"""

import asyncio
import os
import sys
sys.path.insert(0, 'src')

from services.url_discovery import URLDiscoveryService

# Test companies with different recognition levels
TEST_COMPANIES = [
    {
        'name': 'Notion',
        'website': 'https://www.notion.so',
        'expected': 'HIGH_CONFIDENCE',
        'description': 'Well-known productivity software'
    },
    {
        'name': 'Cursor',
        'website': 'https://www.cursor.com',
        'expected': 'MEDIUM_CONFIDENCE',
        'description': 'AI code editor startup'
    },
    {
        'name': 'FakeCompanyXYZ',
        'website': 'https://www.fakecompanyxyz.com',
        'expected': 'LOW_CONFIDENCE',
        'description': 'Fictional company for testing'
    },
    {
        'name': 'Linear',
        'website': 'https://linear.app',
        'expected': 'MEDIUM_CONFIDENCE',
        'description': 'Project management tool'
    }
]

async def test_confidence_validation():
    """Test confidence validation with different company types."""
    print("🎯 Confidence Validation Test")
    print("============================")
    print("Testing how the system handles companies with different recognition levels")
    print()
    
    # Check API keys
    cohere_key = os.getenv('COHERE_API_KEY')
    openai_key = os.getenv('OPENAI_API_KEY')
    
    if not cohere_key and not openai_key:
        print("❌ No AI API keys found. Please set COHERE_API_KEY or OPENAI_API_KEY")
        return
    
    # Initialize service
    service = URLDiscoveryService(
        cohere_api_key=cohere_key,
        openai_api_key=openai_key,
        brave_api_key=os.getenv('BRAVE_API_KEY')
    )
    
    results = {}
    
    for company in TEST_COMPANIES:
        print(f"🔍 Testing: {company['name']}")
        print(f"   Website: {company['website']}")
        print(f"   Expected: {company['expected']}")
        print(f"   Description: {company['description']}")
        
        try:
            # Test with different confidence thresholds
            for threshold in [0.3, 0.6, 0.8]:
                print(f"\n   🎯 Testing with confidence threshold: {threshold}")
                
                discovered_urls = await service.discover_competitor_urls(
                    competitor_name=company['name'],
                    base_url=company['website'],
                    search_depth="standard",
                    categories=['pricing'],  # Just test one category for speed
                    ranking_llm="cohere",
                    selection_llm="cohere",
                    min_confidence_threshold=threshold
                )
                
                if discovered_urls:
                    url = discovered_urls[0]
                    overall_confidence = url.get('confidence_score', 0)
                    brand_confidence = url.get('brand_confidence', 0)
                    
                    print(f"      ✅ Found URL: {url.get('url')}")
                    print(f"      📊 Overall confidence: {overall_confidence:.2f}")
                    print(f"      🏢 Brand confidence: {brand_confidence:.2f}")
                    
                    results[f"{company['name']}_threshold_{threshold}"] = {
                        'success': True,
                        'confidence': overall_confidence,
                        'url': url.get('url')
                    }
                else:
                    print(f"      ⚠️ No URLs found (below confidence threshold)")
                    results[f"{company['name']}_threshold_{threshold}"] = {
                        'success': False,
                        'reason': 'Below confidence threshold'
                    }
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results[company['name']] = {'error': str(e)}
        
        print()
    
    # Summary
    print("📊 Confidence Validation Summary")
    print("===============================")
    
    for company in TEST_COMPANIES:
        print(f"\n{company['name']} ({company['expected']}):")
        
        for threshold in [0.3, 0.6, 0.8]:
            key = f"{company['name']}_threshold_{threshold}"
            if key in results:
                result = results[key]
                if result.get('success'):
                    conf = result['confidence']
                    status = "✅ PASS" if conf >= threshold else "⚠️ LOW"
                    print(f"   Threshold {threshold}: {status} (confidence: {conf:.2f})")
                else:
                    print(f"   Threshold {threshold}: ❌ FAIL ({result.get('reason', 'Unknown')})")
    
    print("\n💡 Key Insights:")
    print("   • Well-known companies should pass most confidence thresholds")
    print("   • Startups may pass lower thresholds but fail higher ones")
    print("   • Fictional companies should fail validation entirely")
    print("   • System protects against returning wrong results for unknown companies")

async def test_brand_recognition_only():
    """Test just the brand recognition validation step."""
    print("\n🏢 Brand Recognition Test")
    print("========================")
    print("Testing the brand recognition validation step independently")
    print()
    
    # Check API keys
    cohere_key = os.getenv('COHERE_API_KEY')
    openai_key = os.getenv('OPENAI_API_KEY')
    
    if not cohere_key and not openai_key:
        print("❌ No AI API keys found. Skipping brand recognition test")
        return
    
    service = URLDiscoveryService(
        cohere_api_key=cohere_key,
        openai_api_key=openai_key
    )
    
    for company in TEST_COMPANIES:
        print(f"🔍 Testing brand recognition: {company['name']}")
        
        try:
            validation_result = await service._validate_brand_recognition(
                company['name'], 
                company['website']
            )
            
            recognized = validation_result['is_recognized']
            confidence = validation_result['confidence']
            reason = validation_result['reason']
            
            status = "✅" if recognized else "❌"
            print(f"   {status} Recognized: {recognized}")
            print(f"   📊 Confidence: {confidence:.2f}")
            print(f"   💭 Reason: {reason}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()

async def main():
    """Main test runner."""
    print("🚀 Confidence Validation Test Suite")
    print("===================================")
    print("Testing the enhanced confidence validation system")
    print("This prevents wrong results for lesser-known companies")
    print()
    
    await test_brand_recognition_only()
    await test_confidence_validation()
    
    print("\n🎉 Test completed!")
    print("\n🛡️ Confidence Validation Benefits:")
    print("   • Prevents wrong results for unknown companies")
    print("   • Validates brand recognition before searching")
    print("   • Uses confidence thresholds to filter unreliable results")
    print("   • Better to return no results than wrong results")

if __name__ == "__main__":
    asyncio.run(main()) 