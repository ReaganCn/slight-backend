"""
Scraper Factory - Easy switching between scraper implementations
"""

import os
import logging
from typing import Dict, Any, Type, Optional
from enum import Enum

from .base import BaseScraper
from .playwright_scraper import PlaywrightScraper
from .scrapingbee_scraper import ScrapingBeeScraper

logger = logging.getLogger(__name__)

class ScraperType(Enum):
    """Available scraper types"""
    PLAYWRIGHT = "playwright"
    SCRAPINGBEE = "scrapingbee"
    AUTO = "auto"  # Automatically choose based on environment

class ScraperFactory:
    """
    Factory for creating scraper instances.
    Allows easy switching between different scraper implementations.
    """
    
    _scrapers: Dict[ScraperType, Type[BaseScraper]] = {
        ScraperType.PLAYWRIGHT: PlaywrightScraper,
        ScraperType.SCRAPINGBEE: ScrapingBeeScraper
    }
    
    @classmethod
    def create_scraper(
        self, 
        scraper_type: Optional[ScraperType] = None, 
        config: Optional[Dict[str, Any]] = None
    ) -> BaseScraper:
        """
        Create a scraper instance
        
        Args:
            scraper_type: Type of scraper to create. If None, will auto-detect.
            config: Configuration dictionary for the scraper
            
        Returns:
            Configured scraper instance
            
        Raises:
            ValueError: If scraper type is not supported or configuration is invalid
        """
        
        # Auto-detect scraper type if not specified
        if scraper_type is None:
            scraper_type = self._auto_detect_scraper_type()
        
        # Handle AUTO type
        if scraper_type == ScraperType.AUTO:
            scraper_type = self._auto_detect_scraper_type()
        
        # Get scraper class
        if scraper_type not in self._scrapers:
            raise ValueError(f"Unsupported scraper type: {scraper_type}")
        
        scraper_class = self._scrapers[scraper_type]
        
        try:
            # Create and return scraper instance
            return scraper_class(config)
        except Exception as e:
            logger.error(f"Failed to create {scraper_type.value} scraper: {e}")
            
            # Fallback to Playwright if ScrapingBee fails
            if scraper_type == ScraperType.SCRAPINGBEE:
                logger.info("Falling back to Playwright scraper")
                return PlaywrightScraper(config)
            
            raise
    
    @classmethod
    def _auto_detect_scraper_type(cls) -> ScraperType:
        """
        Automatically detect which scraper to use based on environment
        
        Returns:
            ScraperType to use
        """
        
        # Check for ScrapingBee API key
        scrapingbee_key = os.getenv('SCRAPINGBEE_API_KEY')
        
        # Check for explicit preference
        scraper_preference = os.getenv('PREFERRED_SCRAPER', '').lower()
        
        if scraper_preference == 'scrapingbee' and scrapingbee_key:
            logger.info("Auto-detected: ScrapingBee (preferred + API key available)")
            return ScraperType.SCRAPINGBEE
        elif scraper_preference == 'playwright':
            logger.info("Auto-detected: Playwright (preferred)")
            return ScraperType.PLAYWRIGHT
        elif scrapingbee_key:
            logger.info("Auto-detected: ScrapingBee (API key available)")
            return ScraperType.SCRAPINGBEE
        else:
            logger.info("Auto-detected: Playwright (default/free option)")
            return ScraperType.PLAYWRIGHT
    
    @classmethod
    def get_available_scrapers(cls) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all available scrapers
        
        Returns:
            Dictionary with scraper information
        """
        available = {}
        
        for scraper_type, scraper_class in cls._scrapers.items():
            try:
                # Create temporary instance to get info
                temp_config = {}
                if scraper_type == ScraperType.SCRAPINGBEE:
                    # Use dummy API key for info retrieval
                    temp_config = {'api_key': 'dummy_key_for_info'}
                
                temp_scraper = scraper_class(temp_config)
                available[scraper_type.value] = temp_scraper.get_scraper_info()
                
                # Add availability status
                if scraper_type == ScraperType.SCRAPINGBEE:
                    has_api_key = bool(os.getenv('SCRAPINGBEE_API_KEY'))
                    available[scraper_type.value]['available'] = has_api_key
                    available[scraper_type.value]['status'] = 'Ready' if has_api_key else 'API key required'
                else:
                    available[scraper_type.value]['available'] = True
                    available[scraper_type.value]['status'] = 'Ready'
                    
            except Exception as e:
                available[scraper_type.value] = {
                    'name': scraper_type.value,
                    'available': False,
                    'status': f'Error: {e}',
                    'error': str(e)
                }
        
        return available
    
    @classmethod
    def create_from_string(cls, scraper_name: str, config: Optional[Dict[str, Any]] = None) -> BaseScraper:
        """
        Create scraper from string name
        
        Args:
            scraper_name: Name of scraper ('playwright', 'scrapingbee', 'auto')
            config: Configuration dictionary
            
        Returns:
            Configured scraper instance
        """
        try:
            scraper_type = ScraperType(scraper_name.lower())
            return cls.create_scraper(scraper_type, config)
        except ValueError:
            raise ValueError(f"Unknown scraper type: {scraper_name}. Available: {[t.value for t in ScraperType]}")

# Convenience functions for easy scraper creation
def create_playwright_scraper(config: Optional[Dict[str, Any]] = None) -> PlaywrightScraper:
    """Create a Playwright scraper instance"""
    return ScraperFactory.create_scraper(ScraperType.PLAYWRIGHT, config)

def create_scrapingbee_scraper(config: Optional[Dict[str, Any]] = None) -> ScrapingBeeScraper:
    """Create a ScrapingBee scraper instance"""
    return ScraperFactory.create_scraper(ScraperType.SCRAPINGBEE, config)

def create_auto_scraper(config: Optional[Dict[str, Any]] = None) -> BaseScraper:
    """Create a scraper instance using auto-detection"""
    return ScraperFactory.create_scraper(ScraperType.AUTO, config)

# Environment-based scraper creation
def get_scraper_from_env(config: Optional[Dict[str, Any]] = None) -> BaseScraper:
    """
    Create scraper based on environment variables
    
    Environment variables:
    - PREFERRED_SCRAPER: 'playwright' or 'scrapingbee'
    - SCRAPINGBEE_API_KEY: API key for ScrapingBee
    
    Returns:
        Configured scraper instance based on environment
    """
    return ScraperFactory.create_scraper(ScraperType.AUTO, config) 