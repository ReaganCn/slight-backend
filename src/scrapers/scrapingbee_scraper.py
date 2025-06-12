"""
ScrapingBee-based scraper implementation.
Premium scraping service with built-in proxy rotation and anti-bot features.
"""

import asyncio
import aiohttp
import logging
import os
from datetime import datetime, timezone
from typing import Dict, Any
from bs4 import BeautifulSoup

from .base import BaseScraper

logger = logging.getLogger(__name__)

class ScrapingBeeScraper(BaseScraper):
    """
    Premium scraper using ScrapingBee API
    
    Pros:
    - Built-in proxy rotation
    - Advanced anti-bot detection bypass
    - JavaScript rendering
    - Professional reliability
    - Geographic targeting
    - Small Lambda package size
    
    Cons:
    - Costs $29-199/month
    - API dependency
    - Rate limits
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.session = None
        self.api_key = None
        
        # Default configuration
        self.default_config = {
            'render_js': True,
            'premium_proxy': True,
            'country_code': 'US',
            'device': 'desktop',
            'wait_browser': 'networkidle',
            'timeout': 35000,
            'block_resources': False,
            'screenshot': False,
            'wait': 3000,
            'window_width': 1920,
            'window_height': 1080
        }
        
        # Merge with user config
        self.config = {**self.default_config, **self.config}
        
        # Get API key from environment or config
        self.api_key = self.config.get('api_key') or os.getenv('SCRAPINGBEE_API_KEY')
        if not self.api_key:
            raise ValueError("ScrapingBee API key not found. Set SCRAPINGBEE_API_KEY environment variable or pass in config.")
    
    async def __aenter__(self):
        """Initialize HTTP session"""
        try:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=60),
                headers={
                    'User-Agent': 'CompetitorTracker/1.0'
                }
            )
            
            logger.info("ScrapingBee session initialized successfully")
            return self
            
        except Exception as e:
            logger.error(f"Failed to initialize ScrapingBee session: {e}")
            await self._cleanup()
            raise
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup HTTP session"""
        await self._cleanup()
    
    async def _cleanup(self):
        """Internal cleanup method"""
        try:
            if self.session:
                await self.session.close()
        except Exception as e:
            logger.warning(f"Error during ScrapingBee cleanup: {e}")
    
    async def scrape_url(self, url: str, competitor_name: str) -> Dict[str, Any]:
        """
        Scrape a competitor's pricing page using ScrapingBee
        """
        if not self.validate_url(url):
            raise ValueError(f"Invalid URL: {url}")
        
        start_time = datetime.now()
        
        try:
            # Prepare ScrapingBee API parameters
            params = {
                'api_key': self.api_key,
                'url': url,
                'render_js': str(self.config['render_js']).lower(),
                'premium_proxy': str(self.config['premium_proxy']).lower(),
                'country_code': self.config['country_code'],
                'device': self.config['device'],
                'wait_browser': self.config['wait_browser'],
                'timeout': self.config['timeout'],
                'wait': self.config['wait'],
                'window_width': self.config['window_width'],
                'window_height': self.config['window_height']
            }
            
            # Add optional parameters
            if self.config['block_resources']:
                params['block_resources'] = 'true'
            
            if self.config['screenshot']:
                params['screenshot'] = 'true'
            
            # Make request to ScrapingBee
            logger.info(f"Scraping {url} with ScrapingBee")
            async with self.session.get(
                'https://app.scrapingbee.com/api/v1/',
                params=params
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"ScrapingBee API error: HTTP {response.status} - {error_text}")
                
                html_content = await response.text()
                response_time = (datetime.now() - start_time).total_seconds()
                
                # Get additional metadata from headers
                spb_cost = response.headers.get('spb-cost', '0')
                spb_country = response.headers.get('spb-country', 'unknown')
                spb_proxy_type = response.headers.get('spb-proxy-type', 'unknown')
                
                # Parse with BeautifulSoup
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Extract pricing and features
                extracted_data = await self._extract_data(soup, competitor_name, url)
                
                # Add metadata
                extracted_data['metadata'] = {
                    'scrape_method': 'scrapingbee',
                    'page_title': soup.title.string if soup.title else '',
                    'response_time': response_time,
                    'scraped_at': datetime.now(timezone.utc).isoformat(),
                    'url': url,
                    'status_code': response.status,
                    'user_agent': 'ScrapingBee',
                    'api_cost': spb_cost,
                    'proxy_country': spb_country,
                    'proxy_type': spb_proxy_type,
                    'render_js': self.config['render_js'],
                    'premium_proxy': self.config['premium_proxy']
                }
                
                # Log successful scrape
                self.log_scrape_attempt(url, True, response_time)
                
                logger.info(f"ScrapingBee scrape completed - Cost: {spb_cost} credits, Country: {spb_country}")
                
                return extracted_data
                
        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds()
            error_msg = f"Failed to scrape {url} with ScrapingBee: {e}"
            logger.error(error_msg)
            
            # Log failed scrape
            self.log_scrape_attempt(url, False, response_time, str(e))
            raise
    
    async def _extract_data(self, soup: BeautifulSoup, competitor_name: str, url: str) -> Dict[str, Any]:
        """
        Enhanced data extraction optimized for ScrapingBee's clean HTML
        """
        data = {
            'prices': {},
            'features': {},
            'raw_html_snippet': ''
        }
        
        # ScrapingBee provides clean HTML, so we can use more precise selectors
        price_selectors = [
            # Modern SaaS pricing selectors
            '[data-testid*="price"]',
            '[data-price]',
            '[aria-label*="price"]',
            
            # Class-based selectors (common patterns)
            '[class*="price"]:not([class*="old"]):not([class*="strike"])',
            '[class*="cost"]',
            '[class*="pricing"]',
            '[class*="amount"]',
            '[class*="rate"]',
            
            # Semantic selectors for modern frameworks
            '.plan-price, .tier-price, .subscription-price',
            '.price-value, .cost-value, .amount-value',
            '.monthly-price, .annual-price, .yearly-price',
            
            # React/Vue component patterns
            '[class*="Price"]',  # PascalCase components
            '[class*="Cost"]',
            '[class*="Plan"]',
            
            # Pricing card patterns
            '.pricing-card [class*="price"]',
            '.plan-card [class*="price"]',
            '.tier-card [class*="price"]',
            
            # Table-based pricing
            'table[class*="pricing"] td',
            '.pricing-table td'
        ]
        
        prices_found = []
        for selector in price_selectors:
            try:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text(strip=True)
                    if self._is_likely_price(text):
                        prices_found.append(text)
            except Exception as e:
                logger.debug(f"Price selector {selector} failed: {e}")
                continue
        
        # Enhanced plan/feature extraction for modern SaaS sites
        plan_selectors = [
            # Data attribute selectors (preferred for modern sites)
            '[data-testid*="plan"]',
            '[data-plan]',
            '[data-tier]',
            '[data-package]',
            
            # Semantic class selectors
            '.plan, .tier, .package, .subscription',
            '.pricing-plan, .pricing-tier, .pricing-package',
            '.plan-card, .tier-card, .pricing-card',
            
            # Feature list selectors
            '.features, .plan-features, .tier-features',
            '.feature-list, .benefits, .inclusions',
            '.plan-benefits, .tier-benefits',
            
            # Modern component patterns
            '[class*="Plan"]',  # React/Vue components
            '[class*="Tier"]',
            '[class*="Package"]',
            
            # Grid/flex layouts common in modern pricing
            '.pricing-grid > div',
            '.plans-grid > div',
            '.tiers-grid > div'
        ]
        
        plans_found = []
        for selector in plan_selectors:
            try:
                elements = soup.select(selector)[:10]  # Limit to prevent spam
                for element in elements:
                    plan_text = element.get_text(separator=' | ', strip=True)
                    if self._is_likely_plan(plan_text):
                        plans_found.append(plan_text)
            except Exception as e:
                logger.debug(f"Plan selector {selector} failed: {e}")
                continue
        
        # Structure the extracted data
        if prices_found:
            unique_prices = list(dict.fromkeys(prices_found))
            data['prices'] = {
                'raw_prices': unique_prices[:25],  # Allow more since ScrapingBee is cleaner
                'extracted_count': len(unique_prices),
                'pricing_patterns': self.extract_price_patterns(unique_prices)
            }
        
        if plans_found:
            unique_plans = list(dict.fromkeys(plans_found))
            data['features'] = {
                'plans': unique_plans[:10],  # Allow more plans
                'plan_count': len(unique_plans)
            }
        
        # Store relevant HTML snippet
        data['raw_html_snippet'] = self._extract_relevant_html(soup)
        
        return data
    
    def _is_likely_price(self, text: str) -> bool:
        """Check if text looks like a price (optimized for clean ScrapingBee output)"""
        if not text or len(text) > 150:  # Slightly more generous for clean output
            return False
        
        text = text.strip().lower()
        
        # Currency indicators
        currency_indicators = ['$', '€', '£', '¥', '₹', 'usd', 'eur', 'gbp', 'jpy', 'inr']
        has_currency = any(indicator in text for indicator in currency_indicators)
        
        # Pricing terms
        pricing_terms = [
            'free', 'trial', 'month', 'year', 'annual', 'monthly', 'yearly',
            'per user', 'per month', 'per year', '/mo', '/yr', '/month', '/year',
            'billed', 'starting', 'from', 'price', 'cost'
        ]
        has_pricing_terms = any(term in text for term in pricing_terms)
        
        # Numeric patterns
        import re
        has_numbers = bool(re.search(r'\d+', text))
        
        # More sophisticated validation for ScrapingBee's clean output
        return (has_currency or has_pricing_terms) and has_numbers
    
    def _is_likely_plan(self, text: str) -> bool:
        """Check if text looks like a plan description (optimized for clean output)"""
        if not text or len(text) < 15 or len(text) > 3000:
            return False
        
        # Plan-related keywords
        plan_keywords = [
            'plan', 'tier', 'package', 'subscription', 'edition',
            'features', 'includes', 'access', 'support', 'users',
            'storage', 'bandwidth', 'requests', 'api', 'integrations',
            'unlimited', 'limited', 'custom', 'enterprise', 'professional',
            'starter', 'basic', 'premium', 'advanced'
        ]
        
        text_lower = text.lower()
        keyword_count = sum(1 for keyword in plan_keywords if keyword in text_lower)
        
        # Also check for structured data indicators
        structure_indicators = ['|', '•', '-', '✓', '✗', 'gb', 'tb', '%']
        has_structure = any(indicator in text for indicator in structure_indicators)
        
        return keyword_count >= 2 or (keyword_count >= 1 and has_structure)
    
    def _extract_relevant_html(self, soup: BeautifulSoup) -> str:
        """Extract the most relevant HTML snippet for pricing"""
        # ScrapingBee provides clean HTML, so we can be more precise
        
        # Look for pricing sections with data attributes first
        pricing_sections = soup.find_all(['div', 'section', 'main'], 
                                       attrs={'data-testid': lambda x: x and 'pricing' in x.lower()})
        
        if not pricing_sections:
            # Fall back to class-based search
            pricing_sections = soup.find_all(['div', 'section', 'main'], 
                                           class_=lambda x: x and any(
                                               word in x.lower() for word in [
                                                   'pricing', 'plans', 'tiers', 'packages',
                                                   'subscription', 'cost'
                                               ]
                                           ))
        
        if pricing_sections:
            return str(pricing_sections[0])[:8000]  # Larger snippet for clean HTML
        
        # Last resort: find any container with pricing content
        for indicator in ['$', 'pricing', 'plans', 'tier']:
            elements = soup.find_all(text=lambda text: text and indicator in str(text).lower())
            if elements:
                parent = elements[0].parent
                if parent:
                    # Walk up to find a meaningful container
                    for _ in range(3):  # Max 3 levels up
                        if parent.parent and parent.parent.name in ['div', 'section', 'main']:
                            parent = parent.parent
                        else:
                            break
                    return str(parent)[:6000]
        
        return ""
    
    def get_scraper_info(self) -> Dict[str, Any]:
        """Get information about this scraper implementation"""
        return {
            'name': 'ScrapingBee',
            'type': 'api_service',
            'javascript_support': True,
            'proxy_support': True,
            'cost': 'paid',
            'pricing': {
                'starter': '$29/month (50k requests)',
                'professional': '$99/month (500k requests)',
                'advanced': '$199/month (2M requests)'
            },
            'performance': 'high',
            'reliability': 'very_high',
            'lambda_friendly': True,
            'requirements': ['aiohttp', 'beautifulsoup4'],
            'lambda_memory_recommended': '512MB',
            'lambda_timeout_recommended': '60s',
            'pros': [
                'Professional proxy rotation',
                'Advanced anti-bot bypass',
                'Geographic targeting',
                'High reliability',
                'Small Lambda package',
                'Excellent for difficult sites'
            ],
            'cons': [
                'Monthly subscription cost',
                'API dependency',
                'Rate limits',
                'Per-request costs'
            ],
            'api_key_required': True
        }
    
    def validate_url(self, url: str) -> bool:
        """Enhanced URL validation for ScrapingBee"""
        if not super().validate_url(url):
            return False
        
        # ScrapingBee has some restrictions
        restricted_domains = [
            'localhost',
            '127.0.0.1',
            '192.168.',
            '10.',
            '172.'
        ]
        
        return not any(domain in url for domain in restricted_domains) 