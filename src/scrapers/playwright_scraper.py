"""
Playwright-based scraper implementation.
Free alternative to ScrapingBee with full JavaScript support.
"""

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Dict, Any
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

from .base import BaseScraper

logger = logging.getLogger(__name__)

class PlaywrightScraper(BaseScraper):
    """
    FREE scraper using Playwright for JavaScript rendering
    
    Pros:
    - Full JavaScript support (React/Vue/Angular apps)
    - Fast and reliable
    - Works well in Lambda with proper configuration
    - No API costs
    
    Cons:
    - Larger Lambda package size
    - Higher memory/CPU usage
    - No built-in proxy rotation
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.playwright = None
        self.browser = None
        self.context = None
        
        # Default configuration
        self.default_config = {
            'headless': True,
            'timeout': 30000,
            'wait_time': 3000,
            'viewport': {'width': 1920, 'height': 1080},
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'browser_args': [
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding'
            ]
        }
        
        # Merge with user config
        self.config = {**self.default_config, **self.config}
    
    async def __aenter__(self):
        """Initialize Playwright browser"""
        try:
            self.playwright = await async_playwright().start()
            
            # Use Chromium for best compatibility
            self.browser = await self.playwright.chromium.launch(
                headless=self.config['headless'],
                args=self.config['browser_args']
            )
            
            # Create browser context with realistic settings
            self.context = await self.browser.new_context(
                viewport=self.config['viewport'],
                user_agent=self.config['user_agent']
            )
            
            logger.info("Playwright browser initialized successfully")
            return self
            
        except Exception as e:
            logger.error(f"Failed to initialize Playwright: {e}")
            await self._cleanup()
            raise
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup Playwright resources"""
        await self._cleanup()
    
    async def _cleanup(self):
        """Internal cleanup method"""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            logger.warning(f"Error during Playwright cleanup: {e}")
    
    async def scrape_url(self, url: str, competitor_name: str) -> Dict[str, Any]:
        """
        Scrape a competitor's pricing page using Playwright
        """
        if not self.validate_url(url):
            raise ValueError(f"Invalid URL: {url}")
        
        start_time = datetime.now()
        page = None
        
        try:
            # Create new page
            page = await self.context.new_page()
            
            # Set additional page settings
            await page.set_extra_http_headers({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            })
            
            # Navigate to the page
            logger.info(f"Navigating to {url}")
            response = await page.goto(
                url, 
                wait_until='networkidle',
                timeout=self.config['timeout']
            )
            
            if not response or response.status >= 400:
                raise Exception(f"Failed to load page: HTTP {response.status if response else 'No response'}")
            
            # Wait for dynamic content to load
            await page.wait_for_timeout(self.config['wait_time'])
            
            # Try to wait for common pricing selectors (but don't fail if not found)
            pricing_selectors = [
                '[class*="price"]',
                '[class*="plan"]',
                '.pricing',
                '[data-testid*="price"]',
                '[data-testid*="plan"]'
            ]
            
            for selector in pricing_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    logger.debug(f"Found pricing selector: {selector}")
                    break
                except:
                    continue
            
            # Get the full page content after JS execution
            html_content = await page.content()
            page_title = await page.title()
            response_time = (datetime.now() - start_time).total_seconds()
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract pricing and features
            extracted_data = await self._extract_data(soup, competitor_name, url)
            
            # Add metadata
            extracted_data['metadata'] = {
                'scrape_method': 'playwright',
                'page_title': page_title,
                'response_time': response_time,
                'scraped_at': datetime.now(timezone.utc).isoformat(),
                'url': url,
                'status_code': response.status if response else 0,
                'user_agent': self.config['user_agent'],
                'viewport': self.config['viewport'],
                'browser': 'chromium'
            }
            
            # Log successful scrape
            self.log_scrape_attempt(url, True, response_time)
            
            return extracted_data
            
        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds()
            error_msg = f"Failed to scrape {url} with Playwright: {e}"
            logger.error(error_msg)
            
            # Log failed scrape
            self.log_scrape_attempt(url, False, response_time, str(e))
            raise
            
        finally:
            if page:
                await page.close()
    
    async def _extract_data(self, soup: BeautifulSoup, competitor_name: str, url: str) -> Dict[str, Any]:
        """
        Enhanced data extraction with comprehensive selectors
        """
        data = {
            'prices': {},
            'features': {},
            'raw_html_snippet': ''
        }
        
        # Enhanced price extraction patterns
        price_selectors = [
            # Class-based selectors
            '[class*="price"]:not([class*="old"]):not([class*="original"])',
            '[class*="cost"]',
            '[class*="pricing"]',
            '[class*="amount"]',
            '[class*="rate"]',
            
            # Data attribute selectors
            '[data-testid*="price"]',
            '[data-price]',
            '[data-cost]',
            
            # Semantic selectors
            '.plan-price, .subscription-price, .tier-price',
            '.price-value, .cost-value, .amount-value',
            '.monthly-price, .annual-price',
            
            # Generic but targeted
            '.pricing-card [class*="price"]',
            '.plan-card [class*="price"]',
            '.tier [class*="price"]'
        ]
        
        prices_found = []
        for selector in price_selectors:
            try:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text(strip=True)
                    # Enhanced price validation
                    if self._is_likely_price(text):
                        prices_found.append(text)
            except Exception as e:
                logger.debug(f"Price selector {selector} failed: {e}")
                continue
        
        # Enhanced plan/feature extraction
        plan_selectors = [
            # Plan containers
            '[class*="plan"]:not([class*="background"])',
            '[class*="tier"]',
            '[class*="package"]',
            '[class*="subscription"]',
            
            # Data attributes
            '[data-testid*="plan"]',
            '[data-plan]',
            
            # Semantic selectors
            '.pricing-card, .plan-card, .tier-card',
            '.feature-list, .features, .plan-features',
            '.benefits, .inclusions',
            
            # Table-based pricing
            '.pricing-table tr',
            'table[class*="pricing"] tr'
        ]
        
        plans_found = []
        for selector in plan_selectors:
            try:
                elements = soup.select(selector)[:8]  # Limit to prevent spam
                for element in elements:
                    plan_text = element.get_text(separator=' | ', strip=True)
                    if self._is_likely_plan(plan_text):
                        plans_found.append(plan_text)
            except Exception as e:
                logger.debug(f"Plan selector {selector} failed: {e}")
                continue
        
        # Structure the extracted data
        if prices_found:
            # Remove duplicates while preserving order
            unique_prices = list(dict.fromkeys(prices_found))
            data['prices'] = {
                'raw_prices': unique_prices[:20],  # Limit to prevent spam
                'extracted_count': len(unique_prices),
                'pricing_patterns': self.extract_price_patterns(unique_prices)
            }
        
        if plans_found:
            unique_plans = list(dict.fromkeys(plans_found))
            data['features'] = {
                'plans': unique_plans[:8],  # Limit to reasonable number
                'plan_count': len(unique_plans)
            }
        
        # Store targeted HTML snippet for analysis
        data['raw_html_snippet'] = self._extract_relevant_html(soup)
        
        return data
    
    def _is_likely_price(self, text: str) -> bool:
        """Check if text looks like a price"""
        if not text or len(text) > 100:  # Too long to be a price
            return False
        
        text = text.strip().lower()
        
        # Must contain price indicators
        price_indicators = ['$', '€', '£', '¥', 'usd', 'eur', 'gbp', 'free', 'trial']
        has_price_indicator = any(indicator in text for indicator in price_indicators)
        
        # Or contain pricing keywords
        pricing_keywords = ['month', 'year', 'annual', 'monthly', 'per user', '/mo', '/yr']
        has_pricing_keyword = any(keyword in text for keyword in pricing_keywords)
        
        return has_price_indicator or has_pricing_keyword
    
    def _is_likely_plan(self, text: str) -> bool:
        """Check if text looks like a plan description"""
        if not text or len(text) < 20 or len(text) > 2000:  # Too short or too long
            return False
        
        # Should contain plan-related keywords
        plan_keywords = [
            'plan', 'tier', 'package', 'subscription', 'features', 'includes',
            'users', 'storage', 'support', 'access', 'unlimited', 'limited'
        ]
        
        text_lower = text.lower()
        keyword_count = sum(1 for keyword in plan_keywords if keyword in text_lower)
        
        return keyword_count >= 2  # At least 2 plan-related keywords
    
    def _extract_relevant_html(self, soup: BeautifulSoup) -> str:
        """Extract the most relevant HTML snippet for pricing"""
        # Try to find pricing-specific sections
        pricing_sections = soup.find_all(['div', 'section', 'main'], 
                                       class_=lambda x: x and any(
                                           word in x.lower() for word in [
                                               'price', 'plan', 'tier', 'subscription', 
                                               'pricing', 'cost', 'package'
                                           ]
                                       ))
        
        if pricing_sections:
            # Return the first pricing section
            return str(pricing_sections[0])[:5000]  # Limit size
        
        # Fallback: get body content around pricing keywords
        body = soup.find('body')
        if body:
            body_text = str(body)
            # Look for pricing indicators and extract surrounding content
            for indicator in ['$', 'pricing', 'plans']:
                if indicator in body_text.lower():
                    return body_text[:3000]  # Return first part
        
        return ""
    
    def get_scraper_info(self) -> Dict[str, Any]:
        """Get information about this scraper implementation"""
        return {
            'name': 'Playwright',
            'type': 'browser_automation',
            'javascript_support': True,
            'proxy_support': False,
            'cost': 'free',
            'performance': 'medium',
            'reliability': 'high',
            'lambda_friendly': True,
            'requirements': ['playwright', 'beautifulsoup4'],
            'lambda_memory_recommended': '1024MB',
            'lambda_timeout_recommended': '60s',
            'pros': [
                'Full JavaScript support',
                'Free to use',
                'Reliable and fast',
                'Good debugging tools',
                'Active development'
            ],
            'cons': [
                'Larger Lambda package',
                'Higher memory usage',
                'No built-in proxy rotation',
                'Requires browser installation'
            ]
        } 