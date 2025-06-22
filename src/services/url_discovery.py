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

# Cohere imports for fallback AI
try:
    from scrapers.cohere import get_cohere_client
    COHERE_AVAILABLE = True
except ImportError:
    COHERE_AVAILABLE = False
    logging.warning("Cohere not available - AI categorization will use basic fallback only")

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class URLDiscoveryService:
    """
    Enhanced URL Discovery Service with Google Custom Search and Brave Search.
    No longer uses DuckDuckGo due to reliability issues.
    Uses predefined categories instead of AI-generated ones.
    """
    
    # Predefined categories for URL classification
    PREDEFINED_CATEGORIES = {
        'pricing': {
            'patterns': ['pricing', 'plans', 'subscription', 'cost', 'price', 'billing'],
            'description': 'Pricing and subscription information'
        },
        'features': {
            'patterns': ['features', 'product', 'capabilities', 'functionality', 'solutions'],
            'description': 'Product features and capabilities'
        },
        'blog': {
            'patterns': ['blog', 'news', 'articles', 'insights', 'resources'],
            'description': 'Blog posts and articles'
        },
        'about': {
            'patterns': ['about', 'company', 'team', 'story', 'mission'],
            'description': 'Company information and team'
        },
        'contact': {
            'patterns': ['contact', 'support', 'help', 'customer-service'],
            'description': 'Contact and support information'
        },
        'social': {
            'patterns': ['twitter', 'linkedin', 'facebook', 'instagram', 'tiktok', 'youtube'],
            'description': 'Social media profiles'
        },
        'careers': {
            'patterns': ['careers', 'jobs', 'hiring', 'work', 'join'],
            'description': 'Career opportunities'
        },
        'docs': {
            'patterns': ['docs', 'documentation', 'api', 'developer', 'guide'],
            'description': 'Documentation and developer resources'
        },
        'general': {
            'patterns': [],
            'description': 'General website content'
        }
    }
    
    def __init__(self, openai_api_key: Optional[str] = None, 
                 google_cse_api_key: Optional[str] = None,
                 google_cse_id: Optional[str] = None,
                 brave_api_key: Optional[str] = None,
                 cohere_api_key: Optional[str] = None):
        """Initialize the URL discovery service with reliable search options."""
        self.openai_api_key = openai_api_key
        self.google_cse_api_key = google_cse_api_key
        self.google_cse_id = google_cse_id
        self.brave_api_key = brave_api_key
        self.cohere_api_key = cohere_api_key
        
        # Initialize LLM if OpenAI key provided
        if openai_api_key:
            self.llm = ChatOpenAI(
                model="gpt-4",
                api_key=openai_api_key,
                temperature=0.3
            )
            logger.info("✅ OpenAI GPT-4 initialized for AI categorization")
        else:
            self.llm = None
            logger.info("⚠️ No OpenAI API key provided")
            
        # Initialize Cohere as fallback
        self.cohere_client = None
        if COHERE_AVAILABLE and (cohere_api_key or self.cohere_api_key):
            try:
                self.cohere_client = get_cohere_client()
                logger.info("✅ Cohere initialized as AI fallback")
            except Exception as e:
                logger.warning(f"⚠️ Cohere initialization failed: {e}")
                self.cohere_client = None
        
        # Initialize search tools with better error handling and priorities
        self.search_tools = []
        self._init_search_tools()
        
        # Request session with timeout and retry logic
        self.session_timeout = aiohttp.ClientTimeout(total=15, connect=5)
        
        logger.info(f"🏷️ Using predefined categories: {list(self.PREDEFINED_CATEGORIES.keys())}")

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
        enhanced_results = await self._enhance_with_ai(unique_results, competitor_name, base_url)
        
        logger.info(f"🎯 Discovery complete: {len(enhanced_results)} unique URLs found")
        return enhanced_results

    def _generate_search_queries(self, competitor_name: str, base_url: str, depth: str) -> List[str]:
        """Generate search queries based on depth level."""
        if depth == "quick":
            # Quick mode: only essential queries for fast testing
            return [
                f"{competitor_name} pricing",
                f"site:{urlparse(base_url).netloc} pricing"
            ]
        
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

    async def _enhance_with_ai(self, results: List[Dict[str, Any]], competitor_name: str, base_url: str) -> List[Dict[str, Any]]:
        """Enhanced results with AI categorization and smart batching system."""
        if not results:
            return results
        
        # If no AI available, use basic categorization
        if not self.llm and not self.cohere_client:
            logger.info("🔧 No AI available, using pattern-based categorization")
            return self._basic_categorization(results)
        
        logger.info(f"🤖 Starting smart AI categorization for {len(results)} URLs...")
        logger.info("📊 Smart Batching: Process 10 URLs, continue only if avg confidence < 0.7 (max 40 URLs)")
        
        # Smart batching configuration
        BATCH_SIZE = 10
        CONFIDENCE_THRESHOLD = 0.7
        MAX_URLS = 40
        
        # Limit initial processing to MAX_URLS
        urls_to_process = results[:MAX_URLS]
        if len(results) > MAX_URLS:
            logger.info(f"⚠️ Limited processing to {MAX_URLS} URLs (from {len(results)} available)")
        
        categorized_results = []
        batch_num = 0
        
        # Process URLs in batches of 10
        for i in range(0, len(urls_to_process), BATCH_SIZE):
            batch = urls_to_process[i:i + BATCH_SIZE]
            batch_num += 1
            batch_start = i + 1
            batch_end = min(i + BATCH_SIZE, len(urls_to_process))
            
            logger.info(f"📦 Processing batch {batch_num} (URLs {batch_start}-{batch_end})...")
            
            # Process each URL in the current batch
            batch_results = []
            for j, result in enumerate(batch):
                try:
                    category, confidence, method = await self._ai_categorize_url_with_fallback(result, competitor_name)
                    logger.info(f"   ✅ URL {i+j+1}: {result.get('url', 'Unknown')[:50]}... -> {category} ({confidence:.2f}, {method})")
                except Exception as e:
                    logger.warning(f"   ⚠️ URL {i+j+1} failed: {e}")
                    category, confidence = self._pattern_categorize_url(result)
                    method = 'pattern_matching'
                
                enhanced_result = {
                    **result,
                    'category': category,
                    'confidence_score': confidence,
                    'discovery_method': method
                }
                batch_results.append(enhanced_result)
                categorized_results.append(enhanced_result)
            
            # Calculate average confidence for this batch
            batch_confidences = [r.get('confidence_score', 0) for r in batch_results]
            avg_confidence = sum(batch_confidences) / len(batch_confidences) if batch_confidences else 0
            
            logger.info(f"📊 Batch {batch_num} complete: {len(batch_results)} URLs, avg confidence: {avg_confidence:.3f}")
            
            # Check if we should continue to next batch
            if avg_confidence >= CONFIDENCE_THRESHOLD:
                logger.info(f"✅ High confidence ({avg_confidence:.3f} >= {CONFIDENCE_THRESHOLD}) - stopping early")
                break
            elif batch_end >= len(urls_to_process):
                logger.info(f"📄 Reached end of URLs ({batch_end}/{len(urls_to_process)})")
                break
            elif batch_end >= MAX_URLS:
                logger.info(f"🔒 Reached maximum URL limit ({MAX_URLS})")
                break
            else:
                logger.info(f"⏭️ Low confidence ({avg_confidence:.3f} < {CONFIDENCE_THRESHOLD}) - continuing to next batch")
        
        logger.info(f"🎯 Smart batching complete: Processed {len(categorized_results)} URLs in {batch_num} batches")
        
        # Group URLs by category and select top 3 per category
        category_groups = {}
        for result in categorized_results:
            category = result.get('category', 'general')
            if category not in category_groups:
                category_groups[category] = []
            category_groups[category].append(result)
        
        logger.info(f"📂 Found categories: {list(category_groups.keys())}")
        
        # For each category, get top 3 URLs and use LLM to select the best one
        final_results = []
        for category, urls in category_groups.items():
            if category == 'general':  # Skip general category
                continue
                
            # Sort by confidence score and take top 3
            top_urls = sorted(urls, key=lambda x: x.get('confidence_score', 0), reverse=True)[:3]
            
            if len(top_urls) == 1:
                # Only one URL, use it directly
                final_results.append(top_urls[0])
                logger.info(f"📄 {category.upper()}: Selected only URL -> {top_urls[0].get('url', '')}")
            else:
                # Multiple URLs, use LLM to select the best one
                try:
                    best_url = await self._select_best_url_for_category(top_urls, category, competitor_name, base_url)
                    final_results.append(best_url)
                    logger.info(f"📄 {category.upper()}: LLM selected -> {best_url.get('url', '')}")
                except Exception as e:
                    logger.warning(f"⚠️ LLM selection failed for {category}, using highest confidence URL: {e}")
                    final_results.append(top_urls[0])  # Fallback to highest confidence
        
        logger.info(f"✅ Final selection: {len(final_results)} URLs (1 per category)")
        return final_results

    async def _select_best_url_for_category(self, urls: List[Dict[str, Any]], category: str, competitor_name: str, base_url: str) -> Dict[str, Any]:
        """Use LLM to select the single best URL for a specific category."""
        
        # Prepare URLs for LLM selection
        url_options = []
        for i, url_data in enumerate(urls):
            url_options.append(f"""
Option {i+1}:
URL: {url_data.get('url', '')}
Title: {url_data.get('title', '')}
Snippet: {url_data.get('snippet', '')}""")
        
        prompt = f"""You are analyzing competitor URLs for {competitor_name}. 
        
I need you to select the single best URL that represents the {category} page for this company.

Here are the top 3 candidate URLs:
{chr(10).join(url_options)}

While ignoring the confidence scores, tell me which of these URLs is most likely to be the {category} page of the website {base_url}.

Please respond with ONLY the number (1, 2, or 3) of the best option. Do not include any explanation or additional text."""

        try:
            # Try Cohere first
            if self.cohere_client:
                try:
                    response = await self._cohere_select_url(prompt)
                    selection = self._parse_url_selection(response, len(urls))
                    if selection is not None:
                        selected_url = urls[selection]
                        selected_url['selection_method'] = 'cohere_selection'
                        return selected_url
                except Exception as e:
                    logger.warning(f"⚠️ Cohere URL selection failed: {e}")
            
            # Try OpenAI as fallback
            if self.llm:
                try:
                    response = await self._openai_select_url(prompt)
                    selection = self._parse_url_selection(response, len(urls))
                    if selection is not None:
                        selected_url = urls[selection]
                        selected_url['selection_method'] = 'openai_selection'
                        return selected_url
                except Exception as e:
                    logger.warning(f"⚠️ OpenAI URL selection failed: {e}")
            
            # Fallback to highest confidence
            logger.info("🔧 Using confidence-based selection as fallback")
            selected_url = urls[0]  # Already sorted by confidence
            selected_url['selection_method'] = 'confidence_fallback'
            return selected_url
            
        except Exception as e:
            logger.error(f"❌ URL selection failed: {e}")
            return urls[0]  # Return first URL as ultimate fallback

    async def _cohere_select_url(self, prompt: str) -> str:
        """Use Cohere to select the best URL."""
        if not self.cohere_client:
            raise Exception("Cohere client not available")
        
        try:
            # Use the correct Cohere API method
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.cohere_client.invoke(prompt)
            )
            
            # Cohere returns a response object with content
            if hasattr(response, 'content'):
                return response.content.strip()
            else:
                return str(response).strip()
                
        except Exception as e:
            raise Exception(f"Cohere selection failed: {e}")

    async def _openai_select_url(self, prompt: str) -> str:
        """Use OpenAI to select the best URL."""
        if not self.llm:
            raise Exception("OpenAI client not available")
        
        try:
            # Create a custom OpenAI client with faster failure
            from openai import OpenAI
            custom_client = OpenAI(
                api_key=self.openai_api_key,
                max_retries=1,
                timeout=10.0
            )
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: custom_client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=10
                )
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise Exception(f"OpenAI selection failed: {e}")

    def _parse_url_selection(self, response: str, num_options: int) -> Optional[int]:
        """Parse LLM response to extract URL selection."""
        try:
            # Look for a number in the response
            import re
            numbers = re.findall(r'\b([123])\b', response)
            if numbers:
                selection = int(numbers[0]) - 1  # Convert to 0-based index
                if 0 <= selection < num_options:
                    return selection
            
            # Try to find the number at the start of the response
            if response.strip().startswith(('1', '2', '3')):
                selection = int(response.strip()[0]) - 1
                if 0 <= selection < num_options:
                    return selection
                    
            logger.warning(f"⚠️ Could not parse URL selection from response: '{response}'")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error parsing URL selection: {e}")
            return None

    async def _ai_categorize_url_with_fallback(self, result: Dict[str, Any], competitor_name: str) -> tuple:
        """AI categorization with predefined categories and Cohere -> OpenAI -> Pattern matching fallback chain."""
        
        # Get the list of valid categories
        valid_categories = list(self.PREDEFINED_CATEGORIES.keys())
        categories_text = ", ".join(valid_categories)
        
        # Try Cohere first (primary AI)
        if self.cohere_client:
            try:
                category, confidence = await self._cohere_categorize_url(result, competitor_name, categories_text)
                return category, confidence, 'cohere_enhanced'
            except Exception as e:
                logger.warning(f"⚠️ Cohere categorization failed: {e}")
        
        # Try OpenAI as fallback
        if self.llm:
            try:
                category, confidence = await self._openai_categorize_url(result, competitor_name, categories_text)
                return category, confidence, 'openai_enhanced'
            except Exception as e:
                # Check if it's a quota/rate limit error
                error_str = str(e).lower()
                if any(keyword in error_str for keyword in ['quota', '429', 'rate limit', 'insufficient_quota']):
                    logger.warning(f"🚫 OpenAI quota/rate limit exceeded: {e}")
                else:
                    logger.warning(f"⚠️ OpenAI categorization failed: {e}")
        
        # Final fallback to pattern matching
        logger.info("🔧 Using pattern-based categorization as final fallback")
        category, confidence = self._pattern_categorize_url(result)
        return category, confidence, 'pattern_matching'

    async def _openai_categorize_url(self, result: Dict[str, Any], competitor_name: str, categories_text: str) -> tuple:
        """Use OpenAI to categorize URL with predefined categories and assign confidence score."""
        prompt = f"""
        Analyze this URL and content for competitor research on {competitor_name}:
        
        URL: {result.get('url', '')}
        Title: {result.get('title', '')}
        Snippet: {result.get('snippet', '')}
        
        Categorize this as ONE of these predefined categories ONLY: {categories_text}
        Also provide a confidence score from 0.0 to 1.0 for how relevant this is for competitive analysis.
        
        You MUST choose from the predefined categories. Do not create new categories.
        
        Respond in format: "Category: [category], Confidence: [score]"
        """
        
        # Create a custom OpenAI client with faster failure for quota errors
        from openai import OpenAI
        custom_client = OpenAI(
            api_key=self.openai_api_key,
            max_retries=1,  # Reduce retries for faster fallback
            timeout=10.0    # Shorter timeout
        )
        
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: custom_client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=50
                )
            )
            
            # Parse response
            response_text = response.choices[0].message.content.strip()
            category_match = re.search(r'Category:\s*(\w+)', response_text, re.IGNORECASE)
            confidence_match = re.search(r'Confidence:\s*([\d.]+)', response_text)
            
            category = category_match.group(1).lower() if category_match else 'general'
            confidence = float(confidence_match.group(1)) if confidence_match else 0.5
            
            # Validate category is in predefined list
            if category not in self.PREDEFINED_CATEGORIES:
                logger.warning(f"⚠️ OpenAI returned invalid category '{category}', using 'general'")
                category = 'general'
            
            return category, min(max(confidence, 0.0), 1.0)  # Clamp between 0-1
            
        except Exception as e:
            # Check for quota/rate limit errors and fail fast
            error_str = str(e).lower()
            if any(keyword in error_str for keyword in ['quota', '429', 'rate limit', 'insufficient_quota']):
                # Don't retry on quota errors - fail immediately to trigger fallback
                raise Exception(f"OpenAI quota exceeded: {e}")
            else:
                raise

    async def _cohere_categorize_url(self, result: Dict[str, Any], competitor_name: str, categories_text: str) -> tuple:
        """Use Cohere to categorize URL with predefined categories and assign confidence score."""
        prompt = f"""
        Analyze this URL and content for competitor research on {competitor_name}:
        
        URL: {result.get('url', '')}
        Title: {result.get('title', '')}
        Snippet: {result.get('snippet', '')}
        
        Categorize this as ONE of these predefined categories ONLY: {categories_text}
        Also provide a confidence score from 0.0 to 1.0 for how relevant this is for competitive analysis.
        
        You MUST choose from the predefined categories. Do not create new categories.
        
        Respond in format: "Category: [category], Confidence: [score]"
        """
        
        try:
            # Use Cohere client with correct invoke method
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.cohere_client.invoke(prompt)
            )
            
            # Parse response (Cohere returns different response types)
            if hasattr(response, 'content'):
                response_text = response.content
            else:
                response_text = str(response)
                
            category_match = re.search(r'Category:\s*(\w+)', response_text, re.IGNORECASE)
            confidence_match = re.search(r'Confidence:\s*([\d.]+)', response_text)
            
            category = category_match.group(1).lower() if category_match else 'general'
            confidence = float(confidence_match.group(1)) if confidence_match else 0.5
            
            # Validate category is in predefined list
            if category not in self.PREDEFINED_CATEGORIES:
                logger.warning(f"⚠️ Cohere returned invalid category '{category}', using 'general'")
                category = 'general'
            
            logger.info(f"✅ Cohere categorization: {category} (confidence: {confidence:.2f})")
            return category, min(max(confidence, 0.0), 1.0)  # Clamp between 0-1
            
        except Exception as e:
            raise Exception(f"Cohere categorization failed: {e}")

    def _pattern_categorize_url(self, result: Dict[str, Any]) -> tuple:
        """Pattern-based URL categorization using predefined categories."""
        url = result.get('url', '').lower()
        title = result.get('title', '').lower()
        
        category = 'general'
        confidence = 0.6  # Default confidence for pattern matching
        
        # Check each predefined category
        for cat, config in self.PREDEFINED_CATEGORIES.items():
            if cat == 'general':  # Skip general category in pattern matching
                continue
                
            patterns = config['patterns']
            if any(pattern in url or pattern in title for pattern in patterns):
                category = cat
                confidence = 0.8
                break
        
        return category, confidence

    def _basic_categorization(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Basic URL categorization without AI (legacy method)."""
        enhanced_results = []
        
        for result in results:
            category, confidence = self._pattern_categorize_url(result)
            
            enhanced_result = {
                **result,
                'category': category,
                'confidence_score': confidence,
                'discovery_method': 'pattern_matching'
            }
            
            enhanced_results.append(enhanced_result)
        
        return enhanced_results

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

    def get_predefined_categories(self) -> Dict[str, Dict[str, Any]]:
        """Get the predefined categories configuration."""
        return self.PREDEFINED_CATEGORIES.copy()

    def get_ai_status(self) -> Dict[str, Any]:
        """Get information about available AI services."""
        return {
            'openai_available': bool(self.llm),
            'cohere_available': bool(self.cohere_client),
            'fallback_method': 'pattern_matching',
            'predefined_categories': list(self.PREDEFINED_CATEGORIES.keys())
        } 