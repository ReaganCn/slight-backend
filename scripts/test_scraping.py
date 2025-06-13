#!/usr/bin/env python3
"""
Test script for the flexible scraping architecture.
Demonstrates how to use both Playwright and ScrapingBee scrapers.
"""

import asyncio
import os
import sys
from typing import Dict, Any

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from scrapers.factory import ScraperFactory, ScraperType, get_scraper_from_env
from scrapers.playwright_scraper import PlaywrightScraper
from scrapers.scrapingbee_scraper import ScrapingBeeScraper

async def test_scraper_info():
    """Test getting information about available scrapers"""
    print("🔍 Available Scrapers:")
    print("=" * 50)
    
    available = ScraperFactory.get_available_scrapers()
    for name, info in available.items():
        status_icon = "✅" if info['available'] else "❌"
        print(f"{status_icon} {info['name']}: {info['status']}")
        if info['available']:
            print(f"   Type: {info.get('type', 'unknown')}")
            print(f"   Cost: {info.get('cost', 'unknown')}")
            print(f"   JavaScript: {info.get('javascript_support', False)}")
            print(f"   Proxy: {info.get('proxy_support', False)}")
    print()

async def test_playwright_scraper():
    """Test Playwright scraper directly"""
    print("🎭 Testing Playwright Scraper:")
    print("=" * 50)
    
    try:
        async with PlaywrightScraper() as scraper:
            # Test with a simple page
            url = "https://httpbin.org/html"
            result = await scraper.scrape_url(url, "HttpBin Test")
            
            print(f"✅ Playwright test successful!")
            print(f"   URL: {url}")
            print(f"   Method: {result['metadata_']['scrape_method']}")
            print(f"   Response time: {result['metadata_']['response_time']:.2f}s")
            print(f"   Page title: {result['metadata_']['page_title']}")
            
    except Exception as e:
        print(f"❌ Playwright test failed: {e}")
    print()

async def test_scrapingbee_scraper():
    """Test ScrapingBee scraper (if API key available)"""
    print("🐝 Testing ScrapingBee Scraper:")
    print("=" * 50)
    
    if not os.getenv('SCRAPINGBEE_API_KEY'):
        print("⚠️  SCRAPINGBEE_API_KEY not found - skipping ScrapingBee test")
        print("   Set SCRAPINGBEE_API_KEY environment variable to test")
        print()
        return
    
    try:
        async with ScrapingBeeScraper() as scraper:
            # Test with a simple page
            url = "https://httpbin.org/html"
            result = await scraper.scrape_url(url, "HttpBin Test")
            
            print(f"✅ ScrapingBee test successful!")
            print(f"   URL: {url}")
            print(f"   Method: {result['metadata_']['scrape_method']}")
            print(f"   Response time: {result['metadata_']['response_time']:.2f}s")
            print(f"   API cost: {result['metadata_']['api_cost']} credits")
            print(f"   Proxy country: {result['metadata_']['proxy_country']}")
            
    except Exception as e:
        print(f"❌ ScrapingBee test failed: {e}")
    print()

async def test_auto_scraper():
    """Test auto-detection scraper"""
    print("🤖 Testing Auto-Detection Scraper:")
    print("=" * 50)
    
    try:
        async with get_scraper_from_env() as scraper:
            info = scraper.get_scraper_info()
            print(f"Auto-detected scraper: {info['name']}")
            
            # Test with a simple page
            url = "https://httpbin.org/html"
            result = await scraper.scrape_url(url, "HttpBin Test")
            
            print(f"✅ Auto-detection test successful!")
            print(f"   Selected: {info['name']} ({info['cost']})")
            print(f"   URL: {url}")
            print(f"   Response time: {result['metadata_']['response_time']:.2f}s")
            
    except Exception as e:
        print(f"❌ Auto-detection test failed: {e}")
    print()

async def test_factory_creation():
    """Test creating scrapers through the factory"""
    print("🏭 Testing Scraper Factory:")
    print("=" * 50)
    
    test_cases = [
        ("auto", "Auto-detection"),
        ("playwright", "Explicit Playwright"),
        ("scrapingbee", "Explicit ScrapingBee (if available)")
    ]
    
    for scraper_type, description in test_cases:
        try:
            if scraper_type == "scrapingbee" and not os.getenv('SCRAPINGBEE_API_KEY'):
                print(f"⚠️  {description}: Skipped (no API key)")
                continue
                
            scraper = ScraperFactory.create_from_string(scraper_type)
            info = scraper.get_scraper_info()
            print(f"✅ {description}: {info['name']} ({info['cost']})")
            
        except Exception as e:
            print(f"❌ {description}: Failed - {e}")
    print()

async def test_pricing_page():
    """Test scraping a real pricing page"""
    print("💰 Testing Real Pricing Page:")
    print("=" * 50)
    
    # Use a simple pricing page for testing
    test_urls = [
        ("https://httpbin.org/html", "HttpBin Test Page"),
        # Add more test URLs here if needed
    ]
    
    for url, name in test_urls:
        try:
            async with get_scraper_from_env() as scraper:
                info = scraper.get_scraper_info()
                print(f"Scraping {name} with {info['name']}...")
                
                result = await scraper.scrape_url(url, name)
                
                prices = result.get('prices', {})
                features = result.get('features', {})
                
                print(f"✅ {name}:")
                print(f"   Scraper: {info['name']}")
                print(f"   Prices found: {len(prices.get('raw_prices', []))}")
                print(f"   Features found: {len(features.get('plans', []))}")
                print(f"   Response time: {result['metadata_']['response_time']:.2f}s")
                
        except Exception as e:
            print(f"❌ {name}: Failed - {e}")
    print()

async def demonstrate_switching():
    """Demonstrate switching between scrapers"""
    print("🔄 Demonstrating Scraper Switching:")
    print("=" * 50)
    
    # Show how to explicitly choose different scrapers
    scrapers_to_test = []
    
    # Always test Playwright (free)
    scrapers_to_test.append(("playwright", "🎭 Playwright (FREE)"))
    
    # Test ScrapingBee if available
    if os.getenv('SCRAPINGBEE_API_KEY'):
        scrapers_to_test.append(("scrapingbee", "🐝 ScrapingBee (PAID)"))
    
    url = "https://httpbin.org/html"
    
    for scraper_type, description in scrapers_to_test:
        try:
            scraper = ScraperFactory.create_from_string(scraper_type)
            async with scraper:
                result = await scraper.scrape_url(url, "Comparison Test")
                
                print(f"{description}:")
                print(f"   Response time: {result['metadata_']['response_time']:.2f}s")
                print(f"   Page title: {result['metadata_'].get('page_title', 'N/A')}")
                
                if scraper_type == "scrapingbee":
                    print(f"   API cost: {result['metadata_'].get('api_cost', 'N/A')} credits")
                
        except Exception as e:
            print(f"{description}: ❌ Failed - {e}")
    print()

def print_environment_info():
    """Print relevant environment information"""
    print("🌍 Environment Information:")
    print("=" * 50)
    
    env_vars = [
        ("PREFERRED_SCRAPER", "Scraper preference"),
        ("SCRAPINGBEE_API_KEY", "ScrapingBee API key"),
        ("PLAYWRIGHT_BROWSERS_PATH", "Playwright browsers path")
    ]
    
    for var, description in env_vars:
        value = os.getenv(var)
        if var == "SCRAPINGBEE_API_KEY" and value:
            value = f"{value[:8]}..." if len(value) > 8 else "***"
        
        status = "✅ Set" if value else "❌ Not set"
        print(f"{description}: {status}")
        if value and var != "SCRAPINGBEE_API_KEY":
            print(f"   Value: {value}")
    print()

async def main():
    """Run all tests"""
    print("🕷️  Flexible Scraping Architecture Test Suite")
    print("=" * 60)
    print()
    
    # Environment info
    print_environment_info()
    
    # Test scraper information
    await test_scraper_info()
    
    # Test factory creation
    await test_factory_creation()
    
    # Test individual scrapers
    await test_playwright_scraper()
    await test_scrapingbee_scraper()
    
    # Test auto-detection
    await test_auto_scraper()
    
    # Test real pricing page
    await test_pricing_page()
    
    # Demonstrate switching
    await demonstrate_switching()
    
    print("🎉 Testing complete!")
    print()
    print("💡 Tips:")
    print("   • Set PREFERRED_SCRAPER=playwright to use free Playwright")
    print("   • Set PREFERRED_SCRAPER=scrapingbee to use paid ScrapingBee")
    print("   • Set PREFERRED_SCRAPER=auto for automatic detection")
    print("   • Add SCRAPINGBEE_API_KEY to enable ScrapingBee option")

if __name__ == "__main__":
    asyncio.run(main()) 