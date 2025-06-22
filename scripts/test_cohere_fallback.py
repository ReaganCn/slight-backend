#!/usr/bin/env python3
"""
Test script to verify Cohere fallback functionality when OpenAI quota is exceeded.
This script tests the AI categorization fallback chain: OpenAI -> Cohere -> Pattern matching
"""

import asyncio
import sys
import os
from typing import Dict, Any

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from services.url_discovery import URLDiscoveryService

async def test_ai_fallback_chain():
    """Test the AI categorization fallback chain"""
    print("🧪 Testing AI Categorization Fallback Chain")
    print("=" * 50)
    
    # Test data - sample URL discovery results
    test_results = [
        {
            'url': 'https://example.com/pricing',
            'title': 'Pricing Plans - Example Company',
            'snippet': 'Choose from our flexible pricing plans starting at $9/month',
            'source': 'google_search'
        },
        {
            'url': 'https://example.com/features',
            'title': 'Product Features - Example Company',
            'snippet': 'Discover powerful features that help you work faster',
            'source': 'brave_search'
        },
        {
            'url': 'https://example.com/blog/new-update',
            'title': 'New Product Update - Example Blog',
            'snippet': 'We are excited to announce our latest product updates',
            'source': 'sitemap'
        }
    ]
    
    # Test different API key scenarios
    scenarios = [
        {
            'name': 'OpenAI Available',
            'openai_key': os.getenv('OPENAI_API_KEY'),
            'cohere_key': None,
            'expected_method': 'openai_enhanced' if os.getenv('OPENAI_API_KEY') else 'pattern_matching'
        },
        {
            'name': 'OpenAI Quota Exceeded (Cohere Fallback)',
            'openai_key': 'invalid-key-to-trigger-error',
            'cohere_key': os.getenv('COHERE_API_KEY'),
            'expected_method': 'cohere_enhanced' if os.getenv('COHERE_API_KEY') else 'pattern_matching'
        },
        {
            'name': 'No AI Keys (Pattern Matching)',
            'openai_key': None,
            'cohere_key': None,
            'expected_method': 'pattern_matching'
        }
    ]
    
    for scenario in scenarios:
        print(f"\n🔧 Scenario: {scenario['name']}")
        print("-" * 30)
        
        try:
            # Initialize service with scenario-specific keys
            discovery_service = URLDiscoveryService(
                openai_api_key=scenario['openai_key'],
                cohere_api_key=scenario['cohere_key']
            )
            
            # Check AI status
            ai_status = discovery_service.get_ai_status()
            print(f"AI Status: {ai_status}")
            
            # Test categorization for each URL
            for i, result in enumerate(test_results, 1):
                print(f"\n  Test {i}: {result['url']}")
                
                try:
                    category, confidence, method = await discovery_service._ai_categorize_url_with_fallback(
                        result, "Example Company"
                    )
                    
                    print(f"    ✅ Category: {category}")
                    print(f"    ✅ Confidence: {confidence:.2f}")
                    print(f"    ✅ Method: {method}")
                    
                    # Verify expected method
                    if method == scenario['expected_method']:
                        print(f"    ✅ Expected method used: {method}")
                    else:
                        print(f"    ⚠️ Expected {scenario['expected_method']}, got {method}")
                        
                except Exception as e:
                    print(f"    ❌ Categorization failed: {e}")
                    
        except Exception as e:
            print(f"❌ Scenario setup failed: {e}")

async def test_cohere_direct():
    """Test Cohere client directly"""
    print("\n🔧 Testing Cohere Client Directly")
    print("=" * 40)
    
    try:
        from scrapers.cohere import get_cohere_client
        
        cohere_key = os.getenv('COHERE_API_KEY')
        if not cohere_key:
            print("⚠️ No Cohere API key found - skipping direct test")
            return
        
        print("✅ Cohere imports successful")
        
        client = get_cohere_client()
        print("✅ Cohere client initialized")
        
        # Test a simple prompt
        test_prompt = """
        Analyze this URL and content for competitor research on Example Company:
        
        URL: https://example.com/pricing
        Title: Pricing Plans - Example Company
        Snippet: Choose from our flexible pricing plans starting at $9/month
        
        Categorize this as one of: pricing, features, blog, about, contact, social, or general
        Also provide a confidence score from 0.0 to 1.0 for how relevant this is for competitive analysis.
        
        Respond in format: "Category: [category], Confidence: [score]"
        """
        
        response = client.invoke(test_prompt)
        print(f"✅ Cohere response: {response}")
        
    except ImportError as e:
        print(f"❌ Cohere import failed: {e}")
        print("💡 Make sure langchain-cohere is installed: pip install langchain-cohere")
    except Exception as e:
        print(f"❌ Cohere test failed: {e}")

async def test_error_handling():
    """Test specific error handling scenarios"""
    print("\n🛡️ Testing Error Handling")
    print("=" * 30)
    
    # Test OpenAI quota error simulation
    print("1. Testing OpenAI quota error handling...")
    
    try:
        discovery_service = URLDiscoveryService(
            openai_api_key="sk-invalid-key-to-trigger-quota-error",
            cohere_api_key=os.getenv('COHERE_API_KEY')
        )
        
        test_result = {
            'url': 'https://example.com/pricing',
            'title': 'Test Pricing Page',
            'snippet': 'Test pricing information'
        }
        
        category, confidence, method = await discovery_service._ai_categorize_url_with_fallback(
            test_result, "Test Company"
        )
        
        print(f"✅ Fallback successful: {method} -> {category} ({confidence:.2f})")
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")

def check_environment():
    """Check environment setup"""
    print("🔍 Environment Check")
    print("=" * 20)
    
    api_keys = {
        'OpenAI': os.getenv('OPENAI_API_KEY'),
        'Cohere': os.getenv('COHERE_API_KEY'),
        'Google CSE': os.getenv('GOOGLE_CSE_API_KEY'),
        'Brave Search': os.getenv('BRAVE_API_KEY')
    }
    
    for service, key in api_keys.items():
        status = "✅ Available" if key else "❌ Missing"
        masked_key = f"{key[:8]}..." if key and len(key) > 8 else "None"
        print(f"{service}: {status} ({masked_key})")
    
    print("\n💡 Recommendations:")
    if not api_keys['OpenAI'] and not api_keys['Cohere']:
        print("- Add at least one AI API key (OpenAI or Cohere) for enhanced categorization")
    if not api_keys['Google CSE'] and not api_keys['Brave Search']:
        print("- Add at least one search API key (Google CSE or Brave) for better URL discovery")
    if api_keys['OpenAI'] and api_keys['Cohere']:
        print("- Perfect! You have both AI services for robust fallback")

async def main():
    """Run all tests"""
    print("🚀 Cohere Fallback Test Suite")
    print("=" * 50)
    
    # Environment check
    check_environment()
    
    # Test Cohere directly
    await test_cohere_direct()
    
    # Test AI fallback chain
    await test_ai_fallback_chain()
    
    # Test error handling
    await test_error_handling()
    
    print("\n🎉 Test suite completed!")
    print("\n💡 Key Points:")
    print("- OpenAI quota errors are now handled gracefully")
    print("- Cohere provides AI categorization when OpenAI fails")
    print("- Pattern matching is the final fallback")
    print("- System continues working even with API failures")

if __name__ == "__main__":
    asyncio.run(main()) 