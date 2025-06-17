"""
Base scraper interface for competitor data extraction.
All scraper implementations must inherit from this base class.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

from .cohere import get_pricing_and_features_with_cohere

logger = logging.getLogger(__name__)

class BaseScraper(ABC):
    """
    Abstract base class for all scraper implementations.
    Ensures consistent interface between ScrapingBee, Playwright, and future scrapers.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize scraper with configuration
        
        Args:
            config: Dictionary containing scraper-specific configuration
        """
        self.config = config or {}
        self.name = self.__class__.__name__
    
    @abstractmethod
    async def __aenter__(self):
        """Async context manager entry - setup resources"""
        pass
    
    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - cleanup resources"""
        pass
    
    @abstractmethod
    async def scrape_url(self, url: str, competitor_name: str) -> Dict[str, Any]:
        """
        Scrape a competitor's pricing page
        
        Args:
            url: The URL to scrape
            competitor_name: Name of the competitor for context
            
        Returns:
            Dictionary containing:
            {
                'prices': {
                    'raw_prices': List[str],
                    'extracted_count': int,
                    'pricing_patterns': Dict
                },
                'features': {
                    'plans': List[str],
                    'plan_count': int
                },
                'metadata_': {
                    'scrape_method': str,
                    'page_title': str,
                    'response_time': float,
                    'scraped_at': str,
                    'url': str,
                    'status_code': int,
                    'user_agent': str
                },
                'raw_html_snippet': str
            }
        """
        pass
    
    @abstractmethod
    def get_scraper_info(self) -> Dict[str, Any]:
        """
        Get information about this scraper implementation
        
        Returns:
            Dictionary with scraper metadata_
        """
        pass
    
    def validate_url(self, url: str) -> bool:
        """
        Validate if URL is scrapeable by this implementation
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL can be scraped, False otherwise
        """
        if not url or not isinstance(url, str):
            return False
        
        if not url.startswith(('http://', 'https://')):
            return False
        
        # Add any scraper-specific validation here
        return True
    
    def extract_price_patterns(self, prices: list) -> Dict[str, Any]:
        """
        Common price pattern analysis for all scrapers
        
        Args:
            prices: List of raw price strings
            
        Returns:
            Dictionary with analyzed pricing patterns
        """
        patterns = {
            'monthly_prices': [],
            'annual_prices': [],
            'free_tier': False,
            'currency': 'USD',
            'price_ranges': {
                'lowest': None,
                'highest': None
            }
        }
        
        for price in prices:
            if not price:
                continue
                
            price_lower = str(price).lower()
            
            # Detect free tier
            if any(term in price_lower for term in ['free', '$0', 'no cost', 'trial']):
                patterns['free_tier'] = True
            
            # Categorize by billing cycle
            if any(term in price_lower for term in ['month', '/mo', 'monthly']):
                patterns['monthly_prices'].append(price)
            elif any(term in price_lower for term in ['year', '/yr', 'annual', 'yearly']):
                patterns['annual_prices'].append(price)
            
            # Extract numeric values for range analysis
            import re
            numbers = re.findall(r'\$?(\d+(?:\.\d{2})?)', price)
            if numbers:
                try:
                    value = float(numbers[0])
                    if patterns['price_ranges']['lowest'] is None or value < patterns['price_ranges']['lowest']:
                        patterns['price_ranges']['lowest'] = value
                    if patterns['price_ranges']['highest'] is None or value > patterns['price_ranges']['highest']:
                        patterns['price_ranges']['highest'] = value
                except ValueError:
                    continue
        
        return patterns
    
    def log_scrape_attempt(self, url: str, success: bool, duration: float, error: str = None):
        """
        Log scraping attempt for monitoring
        
        Args:
            url: URL that was scraped
            success: Whether scraping was successful
            duration: Time taken in seconds
            error: Error message if failed
        """
        status = "SUCCESS" if success else "FAILED"
        log_msg = f"[{self.name}] {status} - {url} ({duration:.2f}s)"
        
        if success:
            logger.info(log_msg)
        else:
            logger.error(f"{log_msg} - Error: {error}") 

    def get_pricing_and_features_with_cohere(self, html_content: str):
        return get_pricing_and_features_with_cohere(html_content)