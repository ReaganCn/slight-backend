"""
LangChain-powered URL discovery service for finding competitor pages.
Automatically discovers pricing, features, blog, and social media URLs.
"""

import logging
import asyncio
import re
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urljoin, urlparse
import validators
import aiohttp
from bs4 import BeautifulSoup

# LangChain imports
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.prompts import PromptTemplate

# Sitemap parsing
import advertools as adv

# Additional imports for Google Custom Search and Brave Search
import json
from typing import List, Dict, Any, Optional, Union
import aiohttp
import asyncio
import logging
import re
from urllib.parse import urljoin, urlparse
import validators
from bs4 import BeautifulSoup

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class URLDiscoveryService:
    """
    Enhanced URL Discovery Service with Google Custom Search and Brave Search.
    No longer uses DuckDuckGo due to reliability issues.
    """
    
    def __init__(self, openai_api_key: Optional[str] = None, 
                 google_cse_api_key: Optional[str] = None,
                 google_cse_id: Optional[str] = None,
                 brave_api_key: Optional[str] = None):
        """Initialize the URL discovery service with reliable search options."""
        self.openai_api_key = openai_api_key
        self.google_cse_api_key = google_cse_api_key
        self.google_cse_id = google_cse_id
        self.brave_api_key = brave_api_key
        
        # Initialize LLM if OpenAI key provided
        if openai_api_key:
            self.llm = ChatOpenAI(
                model="gpt-4",
                api_key=openai_api_key,
                temperature=0.3
            )
        else:
            self.llm = None
            
        # Initialize search tools with better error handling and priorities
        self.search_tools = []
        self._init_search_tools()
        
        # Request session with timeout and retry logic
        self.session_timeout = aiohttp.ClientTimeout(total=15, connect=5)
        
    def _init_search_tools(self):
        """Initialize search tools in order of preference."""
        # 1. Google Custom Search (best quality, 100 free/day)
        if self.google_cse_api_key and self.google_cse_id:
            self.search_tools.append({
                'name': 'google_custom_search',
                'priority': 1,
                'daily_limit': 100,
                'handler': self._google_custom_search
            })
            logger.info("✅ Google Custom Search API initialized")
        
        # 2. Brave Search API (2000 free/month, good quality)
        if self.brave_api_key:
            self.search_tools.append({
                'name': 'brave_search_api',
                'priority': 2,
                'daily_limit': 2000,  # Free tier monthly limit
                'handler': self._brave_search_api
            })
            logger.info("✅ Brave Search API initialized")
        
        # 3. Fallback: Direct sitemap + social discovery
        self.search_tools.append({
            'name': 'sitemap_fallback',
            'priority': 3,
            'daily_limit': float('inf'),
            'handler': self._sitemap_fallback_search
        })
        
        if not self.search_tools or len(self.search_tools) == 1:  # Only fallback
            logger.warning("⚠️ No reliable search APIs configured. Please add Google Custom Search or Brave Search API keys.")
        
        logger.info(f"🔧 Initialized {len(self.search_tools)} search backends")

    async def _google_custom_search(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """Google Custom Search API implementation."""
        if not self.google_cse_api_key or not self.google_cse_id:
            raise ValueError("Google Custom Search credentials not configured")
            
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': self.google_cse_api_key,
            'cx': self.google_cse_id,
            'q': query,
            'num': min(num_results, 10)  # Google CSE max is 10 per request
        }
        
        async with aiohttp.ClientSession(timeout=self.session_timeout) as session:
            try:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = []
                        
                        for item in data.get('items', []):
                            results.append({
                                'title': item.get('title', ''),
                                'url': item.get('link', ''),
                                'snippet': item.get('snippet', ''),
                                'source': 'google_custom_search'
                            })
                        
                        logger.info(f"✅ Google Custom Search: {len(results)} results for '{query}'")
                        return results
                    
                    elif response.status == 429:
                        logger.warning("⚠️ Google Custom Search rate limit exceeded")
                        raise Exception("Rate limit exceeded")
                    else:
                        logger.error(f"❌ Google Custom Search error: {response.status}")
                        raise Exception(f"Search failed with status {response.status}")
                        
            except asyncio.TimeoutError:
                logger.error("⏰ Google Custom Search timeout")
                raise Exception("Search timeout")
            except Exception as e:
                logger.error(f"❌ Google Custom Search error: {e}")
                raise

    async def _brave_search_api(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """Brave Search API implementation."""
        if not self.brave_api_key:
            raise ValueError("Brave Search API key not configured")
            
        url = "https://api.search.brave.com/res/v1/web/search"
        headers = {
            'X-Subscription-Token': self.brave_api_key,
            'Accept': 'application/json'
        }
        params = {
            'q': query,
            'count': min(num_results, 10)  # Brave API max per request
        }
        
        async with aiohttp.ClientSession(timeout=self.session_timeout) as session:
            try:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = []
                        
                        for item in data.get('web', {}).get('results', []):
                            results.append({
                                'title': item.get('title', ''),
                                'url': item.get('url', ''),
                                'snippet': item.get('description', ''),
                                'source': 'brave_search_api'
                            })
                        
                        logger.info(f"✅ Brave Search API: {len(results)} results for '{query}'")
                        return results
                    
                    elif response.status == 429:
                        logger.warning("⚠️ Brave Search API rate limit exceeded")
                        raise Exception("Rate limit exceeded")
                    else:
                        logger.error(f"❌ Brave Search API error: {response.status}")
                        raise Exception(f"Search failed with status {response.status}")
                        
            except asyncio.TimeoutError:
                logger.error("⏰ Brave Search API timeout")
                raise Exception("Search timeout")
            except Exception as e:
                logger.error(f"❌ Brave Search API error: {e}")
                raise

    async def _sitemap_fallback_search(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """Fallback search using sitemap analysis and common URL patterns."""
        results = []
        
        # Extract domain from query if it contains a URL
        domain_match = re.search(r'https?://([^/]+)', query)
        if domain_match:
            domain = domain_match.group(1)
            base_url = f"https://{domain}"
            
            # Common URL patterns for competitive intelligence
            patterns = [
                f"{base_url}/pricing",
                f"{base_url}/plans",
                f"{base_url}/features",
                f"{base_url}/about",
                f"{base_url}/blog",
                f"{base_url}/contact",
                f"{base_url}/company",
                f"{base_url}/team"
            ]
            
            # Check which URLs exist
            async with aiohttp.ClientSession(timeout=self.session_timeout) as session:
                for url in patterns:
                    try:
                        async with session.head(url) as response:
                            if response.status == 200:
                                # Extract page title
                                title = await self._extract_page_title(session, url)
                                results.append({
                                    'url': url,
                                    'title': title or url.split('/')[-1].title(),
                                    'snippet': f"Found via sitemap analysis",
                                    'source': 'sitemap_fallback'
                                })
                                
                                if len(results) >= num_results:
                                    break
                                    
                    except Exception:
                        continue  # Skip failed URLs
                        
        logger.info(f"✅ Sitemap fallback: {len(results)} results for '{query}'")
        return results

    async def _extract_page_title(self, session: aiohttp.ClientSession, url: str) -> Optional[str]:
        """Extract page title for better result presentation."""
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    title_tag = soup.find('title')
                    if title_tag:
                        return title_tag.text.strip()
        except Exception:
            pass
        return None

    async def discover_competitor_urls(self, competitor_name: str, base_url: str, 
                                     search_depth: str = "standard") -> List[Dict[str, Any]]:
        """
        Main URL discovery method with multiple fallback options.
        
        Args:
            competitor_name: Name of the competitor
            base_url: Base website URL
            search_depth: "quick", "standard", or "comprehensive"
        """
        logger.info(f"🔍 Starting URL discovery for {competitor_name}")
        
        all_results = []
        search_queries = self._generate_search_queries(competitor_name, base_url, search_depth)
        
        # Try each search backend in priority order
        for query in search_queries:
            found_results = False
            
            for search_tool in self.search_tools:
                try:
                    logger.info(f"🔧 Trying {search_tool['name']} for query: '{query}'")
                    results = await search_tool['handler'](query, num_results=10)
                    
                    if results:
                        all_results.extend(results)
                        found_results = True
                        logger.info(f"✅ {search_tool['name']}: Found {len(results)} results")
                        break  # Success, move to next query
                        
                except Exception as e:
                    logger.warning(f"⚠️ {search_tool['name']} failed for '{query}': {e}")
                    continue  # Try next search backend
            
            if not found_results:
                logger.warning(f"❌ All search backends failed for query: '{query}'")
        
        # Deduplicate and enhance results
        unique_results = self._deduplicate_results(all_results)
        enhanced_results = await self._enhance_with_ai(unique_results, competitor_name)
        
        logger.info(f"🎯 Discovery complete: {len(enhanced_results)} unique URLs found")
        return enhanced_results

    def _generate_search_queries(self, competitor_name: str, base_url: str, depth: str) -> List[str]:
        """Generate search queries based on depth level."""
        base_queries = [
            f"{competitor_name} pricing",
            f"{competitor_name} features",
            f"site:{urlparse(base_url).netloc} pricing",
            f"site:{urlparse(base_url).netloc} features"
        ]
        
        if depth == "comprehensive":
            base_queries.extend([
                f"{competitor_name} blog",
                f"{competitor_name} about company",
                f"{competitor_name} contact",
                f"site:{urlparse(base_url).netloc} blog",
                f"site:{urlparse(base_url).netloc} about"
            ])
        
        return base_queries

    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate URLs from results."""
        seen_urls = set()
        unique_results = []
        
        for result in results:
            url = result.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        return unique_results

    async def _enhance_with_ai(self, results: List[Dict[str, Any]], competitor_name: str) -> List[Dict[str, Any]]:
        """Enhance results with AI categorization and confidence scoring."""
        if not self.llm or not results:
            # Without AI, provide basic categorization
            return self._basic_categorization(results)
        
        try:
            enhanced_results = []
            
            for result in results:
                # Use AI to categorize and score
                category, confidence = await self._ai_categorize_url(result, competitor_name)
                
                enhanced_result = {
                    **result,
                    'category': category,
                    'confidence_score': confidence,
                    'discovery_method': 'ai_enhanced'
                }
                
                enhanced_results.append(enhanced_result)
            
            return enhanced_results
            
        except Exception as e:
            logger.warning(f"⚠️ AI enhancement failed, using basic categorization: {e}")
            return self._basic_categorization(results)

    def _basic_categorization(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Basic URL categorization without AI."""
        category_patterns = {
            'pricing': ['pricing', 'plans', 'subscription', 'cost', 'price'],
            'features': ['features', 'product', 'capabilities', 'functionality'],
            'blog': ['blog', 'news', 'articles', 'insights'],
            'about': ['about', 'company', 'team', 'story'],
            'contact': ['contact', 'support', 'help']
        }
        
        enhanced_results = []
        
        for result in results:
            url = result.get('url', '').lower()
            title = result.get('title', '').lower()
            
            category = 'general'
            confidence = 0.6  # Default confidence for pattern matching
            
            for cat, patterns in category_patterns.items():
                if any(pattern in url or pattern in title for pattern in patterns):
                    category = cat
                    confidence = 0.8
                    break
            
            enhanced_result = {
                **result,
                'category': category,
                'confidence_score': confidence,
                'discovery_method': 'pattern_matching'
            }
            
            enhanced_results.append(enhanced_result)
        
        return enhanced_results

    async def _ai_categorize_url(self, result: Dict[str, Any], competitor_name: str) -> tuple:
        """Use AI to categorize URL and assign confidence score."""
        try:
            prompt = f"""
            Analyze this URL and content for competitor research on {competitor_name}:
            
            URL: {result.get('url', '')}
            Title: {result.get('title', '')}
            Snippet: {result.get('snippet', '')}
            
            Categorize this as one of: pricing, features, blog, about, contact, social, or general
            Also provide a confidence score from 0.0 to 1.0 for how relevant this is for competitive analysis.
            
            Respond in format: "Category: [category], Confidence: [score]"
            """
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.llm.invoke([HumanMessage(content=prompt)])
            )
            
            # Parse response
            response_text = response.content.strip()
            category_match = re.search(r'Category:\s*(\w+)', response_text, re.IGNORECASE)
            confidence_match = re.search(r'Confidence:\s*([\d.]+)', response_text)
            
            category = category_match.group(1).lower() if category_match else 'general'
            confidence = float(confidence_match.group(1)) if confidence_match else 0.5
            
            return category, min(max(confidence, 0.0), 1.0)  # Clamp between 0-1
            
        except Exception as e:
            logger.warning(f"⚠️ AI categorization failed: {e}")
            return 'general', 0.5

    def get_available_search_backends(self) -> List[str]:
        """Get list of available search backends."""
        return [tool['name'] for tool in self.search_tools]

    def get_search_backend_info(self) -> Dict[str, Any]:
        """Get information about configured search backends."""
        info = {}
        for tool in self.search_tools:
            info[tool['name']] = {
                'priority': tool['priority'],
                'daily_limit': tool['daily_limit'],
                'status': 'available'
            }
        return info 