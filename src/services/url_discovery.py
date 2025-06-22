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
    
    # 📝 PREDEFINED_CATEGORIES: Commenting out for now - categories should come from DB/user selection
    # This dictionary is kept as reference for the algorithm but not used for hardcoded categories
    # PREDEFINED_CATEGORIES = {
    #     'pricing': {
    #         'patterns': ['pricing', 'plans', 'subscription', 'cost', 'price', 'billing'],
    #         'description': 'Pricing and subscription information'
    #     },
    #     'features': {
    #         'patterns': ['features', 'product', 'capabilities', 'functionality', 'solutions'],
    #         'description': 'Product features and capabilities'
    #     },
    #     'blog': {
    #         'patterns': ['blog', 'news', 'articles', 'insights', 'resources'],
    #         'description': 'Blog posts and articles'
    #     },
    #     'about': {
    #         'patterns': ['about', 'company', 'team', 'story', 'mission'],
    #         'description': 'Company information and team'
    #     },
    #     'contact': {
    #         'patterns': ['contact', 'support', 'help', 'customer-service'],
    #         'description': 'Contact and support information'
    #     },
    #     'social': {
    #         'patterns': ['twitter', 'linkedin', 'facebook', 'instagram', 'tiktok', 'youtube'],
    #         'description': 'Social media profiles'
    #     },
    #     'careers': {
    #         'patterns': ['careers', 'jobs', 'hiring', 'work', 'join'],
    #         'description': 'Career opportunities'
    #     },
    #     'docs': {
    #         'patterns': ['docs', 'documentation', 'api', 'developer', 'guide'],
    #         'description': 'Documentation and developer resources'
    #     },
    #     'general': {
    #         'patterns': [],
    #         'description': 'General website content'
    #     }
    # }
    
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
        
        logger.info("🏷️ Categories will be provided dynamically from user selection or database")

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
                                     search_depth: str = "standard", 
                                     categories: List[str] = None,
                                     ranking_llm: str = "cohere",  # LLM for relevance ranking
                                     selection_llm: str = "cohere") -> List[Dict[str, Any]]:  # LLM for final selection
        """
        Simplified URL discovery workflow:
        1. Search for each category (implicit categorization)
        2. Use LLM to rank top 10 most relevant URLs per category
        3. Use LLM to select single best URL from top 10
        
        Args:
            competitor_name: Name of the competitor
            base_url: Base URL of the competitor
            search_depth: Search depth (standard, comprehensive)
            categories: List of categories to search for
            ranking_llm: LLM to use for relevance ranking ("cohere", "openai")
            selection_llm: LLM to use for final selection ("cohere", "openai")
        """
        logger.info(f"🔍 Starting simplified URL discovery for {competitor_name}")
        logger.info(f"🏷️ Searching for categories: {categories}")
        logger.info(f"🤖 Using {ranking_llm} for ranking, {selection_llm} for selection")
        
        if not categories:
            categories = ['pricing', 'features', 'blog']
        
        # Step 1: Discover official domains
        logger.info(f"🔍 Step 1: Discovering top 3 official domains for {competitor_name}...")
        official_domains = await self._discover_brand_domains(competitor_name, base_url)
        
        # Step 2: Generate targeted searches for each category
        logger.info(f"🔍 Step 2: Generating targeted searches for {len(official_domains)} domains...")
        search_queries = self._generate_targeted_search_queries(competitor_name, official_domains, categories, search_depth)
        
        # Step 3: Execute searches and group by category
        logger.info(f"🔍 Step 3: Executing searches and grouping by category...")
        category_results = {}
        
        for category in categories:
            category_results[category] = []
            
            # Find queries for this category
            category_queries = [q for q in search_queries if category in q.lower()]
            
            for query in category_queries:
                for tool in self.search_tools:
                    try:
                        logger.info(f"🔧 Searching for '{query}' using {tool['name']}")
                        if tool['name'] == 'google_custom_search':
                            results = await self._google_custom_search(query, 10)
                        elif tool['name'] == 'brave_search_api':
                            results = await self._brave_search_api(query, 10)
                        else:
                            continue
                        
                        if results:
                            logger.info(f"✅ {tool['name']}: Found {len(results)} results")
                            category_results[category].extend(results)
                            break  # Use first successful search backend
                    except Exception as e:
                        logger.warning(f"⚠️ {tool['name']} failed for '{query}': {e}")
                        continue
        
        # Step 4: Filter to same-domain URLs and rank by relevance
        logger.info(f"🔍 Step 4: Filtering and ranking results...")
        final_results = []
        
        for category, results in category_results.items():
            if not results:
                logger.warning(f"⚠️ No results found for category: {category}")
                continue
            
            # Filter to same domain
            same_domain_results = []
            for result in results:
                if self._is_same_domain(result.get('url', ''), base_url, official_domains):
                    same_domain_results.append(result)
            
            logger.info(f"📊 {category}: {len(same_domain_results)} same-domain URLs from {len(results)} total")
            
            if not same_domain_results:
                logger.warning(f"⚠️ No same-domain results for category: {category}")
                continue
            
            # Step 5: Use LLM to rank top 10 most relevant URLs
            logger.info(f"🤖 Step 5: Using {ranking_llm} to rank most relevant URLs for {category}...")
            top_urls = await self._llm_rank_urls_for_category(
                same_domain_results, category, competitor_name, ranking_llm, limit=10
            )
            
            if not top_urls:
                logger.warning(f"⚠️ No URLs ranked for category: {category}")
                continue
            
            # Step 6: Use LLM to select single best URL from top 10
            logger.info(f"🤖 Step 6: Using {selection_llm} to select best URL from top {len(top_urls)} for {category}...")
            best_url = await self._llm_select_best_url(
                top_urls, category, competitor_name, selection_llm
            )
            
            if best_url:
                final_results.append({
                    **best_url,
                    'category': category,
                    'confidence_score': 0.9,  # High confidence since it's LLM-selected
                    'discovery_method': f'{ranking_llm}_ranking + {selection_llm}_selection',
                    'ranking_llm': ranking_llm,
                    'selection_llm': selection_llm
                })
                logger.info(f"✅ {category.upper()}: Selected {best_url.get('url')}")
            else:
                logger.warning(f"⚠️ No URL selected for category: {category}")
        
        logger.info(f"🎯 Discovery complete: {len(final_results)} URLs found across {len(categories)} categories")
        return final_results

    async def _llm_rank_urls_for_category(self, urls: List[Dict[str, Any]], category: str, 
                                        competitor_name: str, llm_choice: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Use LLM to rank URLs by relevance for a specific category."""
        if not urls:
            return []
        
        # Limit input URLs to prevent token overflow
        input_urls = urls[:20]  # Max 20 URLs to rank
        
        # Create URL list for LLM
        url_list = []
        for i, url in enumerate(input_urls, 1):
            url_list.append(f"{i}. {url.get('url', '')}")
            if url.get('title'):
                url_list.append(f"   Title: {url.get('title', '')}")
            if url.get('snippet'):
                url_list.append(f"   Description: {url.get('snippet', '')}")
            url_list.append("")  # Empty line for readability
        
        urls_text = "\n".join(url_list)
        
        prompt = f"""
        Rank these URLs by relevance for finding {category} information about {competitor_name}.
        
        URLs to rank:
        {urls_text}
        
        Please rank them from most relevant to least relevant for {category} information.
        Consider:
        - URL path relevance (e.g., /pricing for pricing category)
        - Title relevance to {category}
        - Description relevance to {category}
        - Overall quality for competitive analysis
        
        Respond with only the top {limit} most relevant URLs in order, using this format:
        1. [URL number from list]
        2. [URL number from list]
        3. [URL number from list]
        ...
        
        Example response:
        1. 3
        2. 7
        3. 1
        """
        
        try:
            if llm_choice == "cohere":
                response_text = await self._cohere_query(prompt)
            else:  # openai
                response_text = await self._openai_query(prompt)
            
            # Parse the ranking response
            ranked_indices = []
            for line in response_text.split('\n'):
                line = line.strip()
                if line and line[0].isdigit():
                    try:
                        # Extract number after the dot
                        rank_match = re.search(r'^\d+\.\s*(\d+)', line)
                        if rank_match:
                            idx = int(rank_match.group(1)) - 1  # Convert to 0-based index
                            if 0 <= idx < len(input_urls):
                                ranked_indices.append(idx)
                    except (ValueError, IndexError):
                        continue
            
            # Return URLs in ranked order
            ranked_urls = []
            for idx in ranked_indices[:limit]:
                ranked_urls.append(input_urls[idx])
            
            logger.info(f"📊 Ranked {len(ranked_urls)} URLs for {category} using {llm_choice}")
            return ranked_urls
            
        except Exception as e:
            logger.error(f"❌ LLM ranking failed for {category}: {e}")
            # Fallback to simple scoring
            return urls[:limit]

    async def _llm_select_best_url(self, urls: List[Dict[str, Any]], category: str, 
                                 competitor_name: str, llm_choice: str) -> Dict[str, Any]:
        """Use LLM to select the single best URL from a list."""
        if not urls:
            return None
        
        if len(urls) == 1:
            return urls[0]
        
        # Create URL options for LLM
        url_options = []
        for i, url in enumerate(urls, 1):
            url_options.append(f"{i}. {url.get('url', '')}")
            if url.get('title'):
                url_options.append(f"   Title: {url.get('title', '')}")
            if url.get('snippet'):
                url_options.append(f"   Description: {url.get('snippet', '')}")
            url_options.append("")  # Empty line for readability
        
        options_text = "\n".join(url_options)
        
        prompt = f"""
        Select the single best URL for finding {category} information about {competitor_name}.
        
        Your options:
        {options_text}
        
        Choose the URL that would be most valuable for competitive analysis of {competitor_name}'s {category}.
        Consider:
        - Most direct/official {category} information
        - Comprehensive {category} details
        - Up-to-date information
        - Competitive intelligence value
        
        Respond with only the number of your choice (1, 2, 3, etc.):
        """
        
        try:
            if llm_choice == "cohere":
                response_text = await self._cohere_query(prompt)
            else:  # openai
                response_text = await self._openai_query(prompt)
            
            # Parse the selection
            selection_match = re.search(r'(\d+)', response_text.strip())
            if selection_match:
                selected_idx = int(selection_match.group(1)) - 1  # Convert to 0-based
                if 0 <= selected_idx < len(urls):
                    logger.info(f"🎯 Selected URL {selected_idx + 1} for {category} using {llm_choice}")
                    return urls[selected_idx]
            
            # Fallback to first URL
            logger.warning(f"⚠️ Could not parse LLM selection, using first URL")
            return urls[0]
            
        except Exception as e:
            logger.error(f"❌ LLM selection failed for {category}: {e}")
            return urls[0]  # Fallback to first URL

    async def _cohere_query(self, prompt: str) -> str:
        """Execute a Cohere query."""
        response = await asyncio.get_event_loop().run_in_executor(
            None, lambda: self.cohere_client.invoke(prompt)
        )
        
        if hasattr(response, 'content'):
            return response.content
        else:
            return str(response)

    async def _openai_query(self, prompt: str) -> str:
        """Execute an OpenAI query."""
        from openai import OpenAI
        client = OpenAI(api_key=self.openai_api_key, max_retries=1, timeout=15.0)
        
        response = await asyncio.get_event_loop().run_in_executor(
            None, lambda: client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=200
            )
        )
        
        return response.choices[0].message.content.strip()

    def _generate_targeted_search_queries(self, competitor_name: str, official_domains: List[str], categories: List[str], depth: str) -> List[str]:
        """Generate targeted search queries using the discovered top 3 domains."""
        queries = []
        
        logger.info(f"🔍 Generating targeted searches for {len(official_domains)} domains and {len(categories)} categories...")
        
        # For each category, create searches targeting the discovered domains
        for category in categories:
            # Generic search query (not domain-specific)
            queries.append(f"{competitor_name} {category}")
            
            # Domain-specific queries for each discovered domain
            for domain in official_domains:
                if depth != "quick":
                    # Site-specific search for this domain
                    queries.append(f"site:{domain} {category}")
                    
                    # Add comprehensive variations for certain categories
                    if depth == "comprehensive":
                        category_variations = {
                            'pricing': ['price', 'cost', 'plans', 'subscription'],
                            'features': ['product', 'capabilities', 'functionality'],
                            'about': ['company', 'team', 'story'],
                            'contact': ['support', 'help', 'customer-service'],
                            'blog': ['news', 'articles', 'insights'],
                            'careers': ['jobs', 'hiring', 'work'],
                            'docs': ['documentation', 'api', 'developer'],
                            'social': ['twitter', 'linkedin', 'facebook']
                        }
                        
                        variations = category_variations.get(category, [])
                        for variation in variations[:1]:  # Limit to 1 variation per category per domain
                            queries.append(f"site:{domain} {variation}")
        
        # If quick mode, limit to primary domain only
        if depth == "quick":
            primary_domain = official_domains[0] if official_domains else None
            if primary_domain:
                queries = [q for q in queries if 'site:' not in q or primary_domain in q]
        
        logger.info(f"📝 Generated {len(queries)} targeted search queries")
        return queries

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

    def _rank_results_by_relevance(self, results: List[Dict[str, Any]], categories: List[str]) -> List[Dict[str, Any]]:
        """Rank results by relevance to the searched categories."""
        def calculate_relevance_score(result):
            score = 0.0
            url = result.get('url', '').lower()
            title = result.get('title', '').lower()
            snippet = result.get('snippet', '').lower()
            
            # Score based on category keywords in URL (highest weight)
            for category in categories:
                if category.lower() in url:
                    score += 3.0
                if any(keyword in url for keyword in [category.lower(), f'{category.lower()}s']):
                    score += 2.0
            
            # Score based on category keywords in title (high weight)
            for category in categories:
                if category.lower() in title:
                    score += 2.0
                    
            # Score based on category keywords in snippet (medium weight)
            for category in categories:
                if category.lower() in snippet:
                    score += 1.0
            
            # Bonus for common important page indicators
            url_indicators = {
                'pricing': ['pricing', 'price', 'cost', 'plans', 'subscription'],
                'features': ['features', 'product', 'capabilities'],
                'blog': ['blog', 'news', 'articles'],
                'about': ['about', 'company', 'team'],
                'contact': ['contact', 'support', 'help']
            }
            
            for category in categories:
                indicators = url_indicators.get(category, [])
                for indicator in indicators:
                    if indicator in url:
                        score += 1.5
                    if indicator in title:
                        score += 1.0
            
            return score
        
        # Sort by relevance score (highest first)
        ranked_results = sorted(results, key=calculate_relevance_score, reverse=True)
        
        # Log top results for debugging
        for i, result in enumerate(ranked_results[:5]):
            score = calculate_relevance_score(result)
            logger.info(f"📊 Rank {i+1}: {result.get('url', '')[:60]}... (score: {score:.1f})")
        
        return ranked_results

    async def _llm_categorize_and_select(self, results: List[Dict[str, Any]], competitor_name: str, categories: List[str]) -> List[Dict[str, Any]]:
        """Use LLM to categorize the top 10 most relevant URLs and select the best one per category."""
        if not results:
            return results
        
        # If no AI available, use basic categorization
        if not self.llm and not self.cohere_client:
            logger.info("🔧 No AI available, using pattern-based categorization")
            return self._basic_categorization(results, categories)
        
        logger.info(f"🤖 Using LLM to categorize {len(results)} top-ranked URLs...")
        
        # Categorize each URL using AI
        categorized_results = []
        for i, result in enumerate(results):
            try:
                category, confidence, method = await self._ai_categorize_url_with_fallback(result, competitor_name, categories)
                logger.info(f"   ✅ URL {i+1}: {result.get('url', 'Unknown')[:50]}... -> {category} ({confidence:.2f}, {method})")
            except Exception as e:
                logger.warning(f"   ⚠️ URL {i+1} failed: {e}")
                category, confidence = self._pattern_categorize_url(result, categories)
                method = 'pattern_matching'
            
            enhanced_result = {
                **result,
                'category': category,
                'confidence_score': confidence,
                'discovery_method': method
            }
            categorized_results.append(enhanced_result)
        
        # Group URLs by category
        category_groups = {}
        for result in categorized_results:
            category = result.get('category', 'general')
            if category != 'general':  # Skip general category
                if category not in category_groups:
                    category_groups[category] = []
                category_groups[category].append(result)
        
        logger.info(f"📂 Found categories: {list(category_groups.keys())}")
        
        # Select the best URL for each category
        final_results = []
        for category, urls in category_groups.items():
            # Sort by confidence score and take the best ones
            top_urls = sorted(urls, key=lambda x: x.get('confidence_score', 0), reverse=True)
            
            if len(top_urls) == 1:
                # Only one URL, use it directly
                selected_url = top_urls[0]
                selected_url['selection_method'] = 'single_option'
                final_results.append(selected_url)
                logger.info(f"📄 {category.upper()}: Selected only URL -> {selected_url.get('url', '')}")
            else:
                # Multiple URLs, use LLM to select the best one from top candidates
                # Limit to top 5 candidates for LLM selection to avoid token limits
                llm_candidates = top_urls[:5]
                try:
                    best_url = await self._select_best_url_for_category(
                        llm_candidates, category, competitor_name, 
                        results[0].get('url', '') if results else ''
                    )
                    final_results.append(best_url)
                    logger.info(f"📄 {category.upper()}: LLM selected -> {best_url.get('url', '')}")
                except Exception as e:
                    logger.warning(f"⚠️ LLM selection failed for {category}, using highest confidence URL: {e}")
                    selected_url = top_urls[0]  # Fallback to highest confidence
                    selected_url['selection_method'] = 'confidence_fallback'
                    final_results.append(selected_url)
        
        logger.info(f"✅ Final selection: {len(final_results)} URLs (1 per category)")
        return final_results

    def _is_same_domain(self, url: str, base_url: str, official_domains: List[str] = None) -> bool:
        """Check if URL belongs to the same domain as base_url (including subdomains and related brand domains)."""
        try:
            from urllib.parse import urlparse
            
            # Parse both URLs
            url_parsed = urlparse(url.lower())
            base_parsed = urlparse(base_url.lower())
            
            # Extract domain parts
            url_domain = url_parsed.netloc
            base_domain = base_parsed.netloc
            
            # Remove 'www.' prefix for comparison
            url_domain = url_domain.replace('www.', '')
            base_domain = base_domain.replace('www.', '')
            
            # Check if it's the exact same domain
            if url_domain == base_domain:
                return True
            
            # Check if url_domain is a subdomain of base_domain
            if url_domain.endswith('.' + base_domain):
                return True
            
            # Check if base_domain is a subdomain of url_domain (reverse case)
            if base_domain.endswith('.' + url_domain):
                return True
            
            # NEW: Check for related brand domains using LLM-discovered official domains
            if official_domains and self._is_same_brand_domain(url_domain, base_domain, official_domains):
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"⚠️ Error comparing domains for {url} vs {base_url}: {e}")
            return False

    async def _discover_brand_domains(self, competitor_name: str, base_url: str) -> List[str]:
        """Use LLM to discover all official domains for a brand."""
        try:
            from urllib.parse import urlparse
            base_domain = urlparse(base_url).netloc.replace('www.', '')
            
            # Check cache first (store for the session to avoid repeated calls)
            cache_key = f"brand_domains_{competitor_name.lower()}"
            if hasattr(self, '_domain_cache') and cache_key in self._domain_cache:
                return self._domain_cache[cache_key]
            
            prompt = f"""List the 3 MOST IMPORTANT official domains for {competitor_name}, ordered by importance and usage.

Company: {competitor_name}
Known domain: {base_domain}

I need the TOP 3 most commonly used official domains for web search purposes. Prioritize:
1. Main website domain (most traffic)
2. Primary alternative domain (if exists)
3. Most important subdomain or product domain

Only return the 3 most important domains, ordered from most to least important. Do not include:
- Social media platforms
- Third-party review sites
- Partner websites
- Regional variations unless they're primary

Format: Return exactly 3 domains, one per line, in order of importance.

Example format:
notion.so
notion.com
api.notion.com"""

            # Try Cohere first
            domains = []
            if self.cohere_client:
                try:
                    response = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: self.cohere_client.invoke(prompt)
                    )
                    
                    if hasattr(response, 'content'):
                        response_text = response.content
                    else:
                        response_text = str(response)
                    
                    # Parse domains from response
                    domains = self._parse_domain_list(response_text, competitor_name)
                    if domains:
                        logger.info(f"✅ Cohere found {len(domains)} official domains for {competitor_name}")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Cohere domain discovery failed: {e}")
            
            # Try OpenAI as fallback
            if not domains and self.llm:
                try:
                    from openai import OpenAI
                    custom_client = OpenAI(
                        api_key=self.openai_api_key,
                        max_retries=1,
                        timeout=15.0
                    )
                    
                    response = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: custom_client.chat.completions.create(
                            model="gpt-4",
                            messages=[{"role": "user", "content": prompt}],
                            temperature=0.1,
                            max_tokens=200
                        )
                    )
                    
                    response_text = response.choices[0].message.content
                    domains = self._parse_domain_list(response_text, competitor_name)
                    if domains:
                        logger.info(f"✅ OpenAI found {len(domains)} official domains for {competitor_name}")
                    
                except Exception as e:
                    logger.warning(f"⚠️ OpenAI domain discovery failed: {e}")
            
            # Always include the base domain
            if base_domain not in domains:
                domains.append(base_domain)
            
            # Cache the result for this session
            if not hasattr(self, '_domain_cache'):
                self._domain_cache = {}
            self._domain_cache[cache_key] = domains
            
            logger.info(f"🔍 Top 3 most important domains for {competitor_name}: {domains}")
            return domains
            
        except Exception as e:
            logger.warning(f"⚠️ Error discovering brand domains for {competitor_name}: {e}")
            # Fallback to just the base domain
            from urllib.parse import urlparse
            base_domain = urlparse(base_url).netloc.replace('www.', '')
            return [base_domain]

    def _parse_domain_list(self, response_text: str, competitor_name: str) -> List[str]:
        """Parse domain list from LLM response, limited to top 3 most important."""
        import re
        
        domains = []
        lines = response_text.strip().split('\n')
        
        # Limit to first 3 valid domains (LLM should return them in order of importance)
        max_domains = 3
        
        for line in lines:
            if len(domains) >= max_domains:
                break
                
            # Clean the line
            line = line.strip()
            if not line:
                continue
            
            # Remove common prefixes/suffixes from LLM responses
            line = re.sub(r'^[-•*]\s*', '', line)  # Remove bullet points
            line = re.sub(r'^\d+\.\s*', '', line)  # Remove numbers
            line = line.replace('https://', '').replace('http://', '')
            line = line.replace('www.', '')
            line = line.split()[0] if line.split() else line  # Take first word
            
            # Validate it looks like a domain
            if self._is_valid_domain_format(line):
                # Additional validation for brand relevance
                if self._is_reasonable_brand_domain(line, competitor_name):
                    domains.append(line.lower())
        
        return domains  # Return up to 3 domains in order of importance

    def _is_valid_domain_format(self, domain: str) -> bool:
        """Check if string looks like a valid domain."""
        import re
        
        # Basic domain format validation
        domain_pattern = r'^[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]*\.([a-zA-Z]{2,}|[a-zA-Z]{2,}\.[a-zA-Z]{2,})$'
        if not re.match(domain_pattern, domain):
            return False
        
        # Must have at least one dot
        if '.' not in domain:
            return False
        
        # Reasonable length
        if len(domain) < 4 or len(domain) > 100:
            return False
        
        return True

    def _is_reasonable_brand_domain(self, domain: str, competitor_name: str) -> bool:
        """Check if domain is reasonably related to the brand."""
        import re
        
        domain_lower = domain.lower()
        name_lower = competitor_name.lower()
        
        # Must contain some part of the brand name or be very short (like x.com)
        name_parts = re.split(r'[\s\-_]', name_lower)
        main_name_part = max(name_parts, key=len) if name_parts else name_lower
        
        # Check if domain contains the main brand name
        if len(main_name_part) >= 3 and main_name_part in domain_lower:
            return True
        
        # Allow very short domains that might be brand shortcuts (like x.com for Twitter)
        if len(domain_lower.split('.')[0]) <= 3:
            return True
        
        return False

    def _is_same_brand_domain(self, url_domain: str, base_domain: str, official_domains: List[str] = None) -> bool:
        """Check if two domains belong to the same brand using discovered official domains."""
        try:
            # Clean domains for comparison
            url_clean = url_domain.replace('www.', '').lower()
            base_clean = base_domain.replace('www.', '').lower()
            
            # Check against official domains list if provided
            if official_domains:
                # Extract main domain from URL (remove subdomains for comparison)
                def get_main_domain(domain):
                    parts = domain.split('.')
                    if len(parts) >= 2:
                        return '.'.join(parts[-2:])  # Keep last two parts (domain.tld)
                    return domain
                
                url_main = get_main_domain(url_clean)
                
                # Check if the URL's main domain is in the official domains list
                for official_domain in official_domains:
                    official_clean = official_domain.replace('www.', '').lower()
                    official_main = get_main_domain(official_clean)
                    
                    if url_main == official_main:
                        logger.info(f"🔗 Official brand domain match: {url_domain} ↔ {base_domain} (found in official domains)")
                        return True
            
            return False
            
        except Exception as e:
            logger.warning(f"⚠️ Error checking brand domains for {url_domain} vs {base_domain}: {e}")
            return False

    async def _select_best_url_for_category(self, urls: List[Dict[str, Any]], category: str, competitor_name: str, base_url: str) -> Dict[str, Any]:
        """Use LLM to select the single best URL for a specific category (URLs are already domain-filtered)."""
        
        # URLs are already filtered to same-domain in calling function
        logger.info(f"✅ Selecting best URL from {len(urls)} candidates for {category} (max 10)")
        
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

Here are {len(urls)} candidate URLs from {base_url} (sorted by relevance, all from the same domain):
{chr(10).join(url_options)}

Please analyze these URLs and select the one that is most likely to be the main {category} page for {competitor_name}.

Respond with ONLY the number (1 to {len(urls)}) of the best option. Do not include any explanation or additional text."""

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
            import re
            
            # Look for any number in the response that's within valid range
            numbers = re.findall(r'\b(\d+)\b', response)
            for num_str in numbers:
                selection = int(num_str) - 1  # Convert to 0-based index
                if 0 <= selection < num_options:
                    return selection
            
            # Try to find a number at the start of the response
            response_clean = response.strip()
            if response_clean and response_clean[0].isdigit():
                selection = int(response_clean[0]) - 1
                if 0 <= selection < num_options:
                    return selection
                    
            logger.warning(f"⚠️ Could not parse URL selection from response: '{response}' (expected 1-{num_options})")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error parsing URL selection: {e}")
            return None

    async def _ai_categorize_url_with_fallback(self, result: Dict[str, Any], competitor_name: str, valid_categories: List[str]) -> tuple:
        """AI categorization with predefined categories and Cohere -> OpenAI -> Pattern matching fallback chain."""
        
        # Use the provided categories from test file/database
        categories_text = ", ".join(valid_categories)
        
        # Try Cohere first (primary AI)
        if self.cohere_client:
            try:
                category, confidence = await self._cohere_categorize_url(result, competitor_name, categories_text, valid_categories)
                return category, confidence, 'cohere_enhanced'
            except Exception as e:
                logger.warning(f"⚠️ Cohere categorization failed: {e}")
        
        # Try OpenAI as fallback
        if self.llm:
            try:
                category, confidence = await self._openai_categorize_url(result, competitor_name, categories_text, valid_categories)
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
        category, confidence = self._pattern_categorize_url(result, valid_categories)
        return category, confidence, 'pattern_matching'

    async def _openai_categorize_url(self, result: Dict[str, Any], competitor_name: str, categories_text: str, valid_categories: List[str]) -> tuple:
        """Use OpenAI to categorize URL with predefined categories and assign confidence score."""
        
        # Create detailed category descriptions to help LLM understand the differences
        category_descriptions = {
            'pricing': 'Subscription plans, costs, billing information, pricing tiers',
            'features': 'Product capabilities, functionality, tools, what the product does',
            'blog': 'Company blog, news articles, insights, thought leadership content, announcements, blog templates',
            'about': 'Company information, team, mission, story, company background',
            'contact': 'Contact information, support, help desk, customer service',
            'social': 'Social media profiles (Twitter, LinkedIn, Facebook, Instagram)',
            'careers': 'Job openings, hiring, work opportunities, company culture',
            'docs': 'Documentation, API guides, developer resources, technical guides',
            'templates': 'User-created templates, examples, showcases (consider if blog-related)',
            'general': 'Other pages that don\'t fit specific categories'
        }
        
        # Build detailed descriptions for the valid categories
        detailed_categories = []
        for cat in valid_categories:
            if cat in category_descriptions:
                detailed_categories.append(f"{cat}: {category_descriptions[cat]}")
        
        detailed_categories_text = "\n".join(detailed_categories)
        
        prompt = f"""
        Analyze this URL and content for competitor research on {competitor_name}:
        
        URL: {result.get('url', '')}
        Title: {result.get('title', '')}
        Snippet: {result.get('snippet', '')}
        
        Categorize this as ONE of these specific categories:
        {detailed_categories_text}
        
        IMPORTANT DISTINCTIONS:
        - "blog": Company's official blog with articles, news, insights, announcements, OR blog templates/tools
        - "features": Product functionality, capabilities, what the software does
        - "pricing": Subscription plans, costs, billing information
        
        SPECIAL CASES:
        - If it's a blog template, blog tool, or blog-related template → choose "blog"
        - If it contains "/blog", "blog-", "blog_", or "blog template" → choose "blog"
        - Look carefully at the URL path and content for blog indicators
        
        You MUST choose from the provided categories only: {', '.join(valid_categories)}
        
        Provide a confidence score from 0.0 to 1.0 for how certain you are about this categorization.
        
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
            
            # Smart category mapping for edge cases
            category = self._map_category_to_valid(category, valid_categories, result)
            
            logger.info(f"✅ OpenAI categorization: {category} (confidence: {confidence:.2f})")
            return category, min(max(confidence, 0.0), 1.0)  # Clamp between 0-1
            
        except Exception as e:
            # Check for quota/rate limit errors and fail fast
            error_str = str(e).lower()
            if any(keyword in error_str for keyword in ['quota', '429', 'rate limit', 'insufficient_quota']):
                # Don't retry on quota errors - fail immediately to trigger fallback
                raise Exception(f"OpenAI quota exceeded: {e}")
            else:
                raise

    async def _cohere_categorize_url(self, result: Dict[str, Any], competitor_name: str, categories_text: str, valid_categories: List[str]) -> tuple:
        """Use Cohere to categorize URL with predefined categories and assign confidence score."""
        
        # Create detailed category descriptions to help LLM understand the differences
        category_descriptions = {
            'pricing': 'Subscription plans, costs, billing information, pricing tiers',
            'features': 'Product capabilities, functionality, tools, what the product does',
            'blog': 'Company blog, news articles, insights, thought leadership content, announcements, blog templates',
            'about': 'Company information, team, mission, story, company background',
            'contact': 'Contact information, support, help desk, customer service',
            'social': 'Social media profiles (Twitter, LinkedIn, Facebook, Instagram)',
            'careers': 'Job openings, hiring, work opportunities, company culture',
            'docs': 'Documentation, API guides, developer resources, technical guides',
            'templates': 'User-created templates, examples, showcases (consider if blog-related)',
            'general': 'Other pages that don\'t fit specific categories'
        }
        
        # Build detailed descriptions for the valid categories
        detailed_categories = []
        for cat in valid_categories:
            if cat in category_descriptions:
                detailed_categories.append(f"{cat}: {category_descriptions[cat]}")
        
        detailed_categories_text = "\n".join(detailed_categories)
        
        prompt = f"""
        Analyze this URL and content for competitor research on {competitor_name}:
        
        URL: {result.get('url', '')}
        Title: {result.get('title', '')}
        Snippet: {result.get('snippet', '')}
        
        Categorize this as ONE of these specific categories:
        {detailed_categories_text}
        
        IMPORTANT DISTINCTIONS:
        - "blog": Company's official blog with articles, news, insights, announcements, OR blog templates/tools
        - "features": Product functionality, capabilities, what the software does
        - "pricing": Subscription plans, costs, billing information
        
        SPECIAL CASES:
        - If it's a blog template, blog tool, or blog-related template → choose "blog"
        - If it contains "/blog", "blog-", "blog_", or "blog template" → choose "blog"
        - Look carefully at the URL path and content for blog indicators
        
        You MUST choose from the provided categories only: {', '.join(valid_categories)}
        
        Provide a confidence score from 0.0 to 1.0 for how certain you are about this categorization.
        
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
            
            # Smart category mapping for edge cases
            category = self._map_category_to_valid(category, valid_categories, result)
            
            logger.info(f"✅ Cohere categorization: {category} (confidence: {confidence:.2f})")
            return category, min(max(confidence, 0.0), 1.0)  # Clamp between 0-1
            
        except Exception as e:
            raise Exception(f"Cohere categorization failed: {e}")

    def _map_category_to_valid(self, category: str, valid_categories: List[str], result: Dict[str, Any]) -> str:
        """Map LLM-returned category to valid categories with smart logic."""
        # If the category is already valid, return it
        if category in valid_categories:
            return category
        
        # Smart mapping for common edge cases
        url = result.get('url', '').lower()
        title = result.get('title', '').lower()
        snippet = result.get('snippet', '').lower()
        
        # Map templates to appropriate categories based on context
        if category == 'templates':
            # Check if it's blog-related template
            if ('blog' in valid_categories and 
                any(indicator in url or indicator in title or indicator in snippet 
                    for indicator in ['blog', 'article', 'post', 'news', 'insights'])):
                logger.info(f"🔄 Mapping 'templates' to 'blog' based on content context")
                return 'blog'
            # Check if it's feature-related template
            elif ('features' in valid_categories and 
                  any(indicator in url or indicator in title or indicator in snippet 
                      for indicator in ['feature', 'product', 'tool', 'capability'])):
                logger.info(f"🔄 Mapping 'templates' to 'features' based on content context")
                return 'features'
        
        # Map other common mismatches
        category_mappings = {
            'documentation': 'docs',
            'doc': 'docs',
            'api': 'docs',
            'guide': 'docs',
            'help': 'docs',
            'support': 'contact',
            'price': 'pricing',
            'cost': 'pricing',
            'plan': 'pricing',
            'subscription': 'pricing',
            'product': 'features',
            'capability': 'features',
            'functionality': 'features',
            'tool': 'features',
            'news': 'blog',
            'article': 'blog',
            'insight': 'blog',
            'post': 'blog',
            'company': 'about',
            'team': 'about',
            'mission': 'about',
            'story': 'about',
            'job': 'careers',
            'hiring': 'careers',
            'work': 'careers',
            'career': 'careers'
        }
        
        # Try to map the category
        mapped_category = category_mappings.get(category)
        if mapped_category and mapped_category in valid_categories:
            logger.info(f"🔄 Mapping '{category}' to '{mapped_category}'")
            return mapped_category
        
        # If no mapping found, default to 'general' if available, otherwise first valid category
        if 'general' in valid_categories:
            logger.warning(f"⚠️ LLM returned invalid category '{category}', using 'general'")
            return 'general'
        else:
            logger.warning(f"⚠️ LLM returned invalid category '{category}', using '{valid_categories[0]}'")
            return valid_categories[0]

    def _pattern_categorize_url(self, result: Dict[str, Any], valid_categories: List[str]) -> tuple:
        """Pattern-based URL categorization using provided categories."""
        url = result.get('url', '').lower()
        title = result.get('title', '').lower()
        snippet = result.get('snippet', '').lower()
        
        category = 'general'
        confidence = 0.6  # Default confidence for pattern matching
        
        # Enhanced pattern matching with better blog detection
        category_patterns = {
            'pricing': {
                'url_patterns': ['pricing', 'price', 'cost', 'plans', 'subscription', 'billing', '/plan'],
                'content_patterns': ['pricing', 'plans', 'subscription', 'cost', 'billing'],
                'confidence': 0.9
            },
            'blog': {
                'url_patterns': ['/blog', '/news', '/articles', '/insights', '/resources', '/updates', '/announcements'],
                'content_patterns': ['blog', 'article', 'news', 'insights', 'thought leadership', 'announcement'],
                'confidence': 0.85,
                'exclude_patterns': ['template', 'showcase', 'example']  # Don't classify templates as blog
            },
            'features': {
                'url_patterns': ['features', 'product', 'capabilities', 'functionality', 'solutions', '/templates'],
                'content_patterns': ['features', 'product', 'capabilities', 'functionality', 'templates'],
                'confidence': 0.8
            },
            'about': {
                'url_patterns': ['about', 'company', 'team', 'story', 'mission', '/about-us'],
                'content_patterns': ['about', 'company', 'team', 'story', 'mission'],
                'confidence': 0.9
            },
            'contact': {
                'url_patterns': ['contact', 'support', 'help', 'customer-service', '/contact-us'],
                'content_patterns': ['contact', 'support', 'help', 'customer service'],
                'confidence': 0.9
            },
            'social': {
                'url_patterns': ['twitter.com', 'linkedin.com', 'facebook.com', 'instagram.com', 'tiktok.com', 'youtube.com'],
                'content_patterns': ['twitter', 'linkedin', 'facebook', 'instagram', 'social'],
                'confidence': 0.95
            },
            'careers': {
                'url_patterns': ['careers', 'jobs', 'hiring', 'work', '/join', '/careers'],
                'content_patterns': ['careers', 'jobs', 'hiring', 'work', 'join'],
                'confidence': 0.9
            },
            'docs': {
                'url_patterns': ['docs', 'documentation', 'api', 'developer', 'guide', '/docs'],
                'content_patterns': ['documentation', 'api', 'developer', 'guide'],
                'confidence': 0.9
            }
        }
        
        # Check each valid category for pattern matches
        best_match = None
        highest_confidence = 0
        
        for cat in valid_categories:
            if cat == 'general' or cat not in category_patterns:
                continue
            
            patterns = category_patterns[cat]
            url_patterns = patterns.get('url_patterns', [])
            content_patterns = patterns.get('content_patterns', [])
            exclude_patterns = patterns.get('exclude_patterns', [])
            pattern_confidence = patterns.get('confidence', 0.7)
            
            # Check for exclusion patterns first (especially for blog)
            if exclude_patterns and any(pattern in url or pattern in title or pattern in snippet 
                                      for pattern in exclude_patterns):
                continue
            
            # Check URL patterns (higher weight)
            url_match = any(pattern in url for pattern in url_patterns)
            
            # Check content patterns (title and snippet)
            content_match = any(pattern in title or pattern in snippet for pattern in content_patterns)
            
            if url_match or content_match:
                # Calculate confidence based on match strength
                match_confidence = pattern_confidence
                if url_match and content_match:
                    match_confidence = min(1.0, pattern_confidence + 0.1)  # Boost for both matches
                elif url_match:
                    match_confidence = pattern_confidence
                else:
                    match_confidence = max(0.6, pattern_confidence - 0.1)  # Lower for content-only match
                
                if match_confidence > highest_confidence:
                    best_match = cat
                    highest_confidence = match_confidence
        
        if best_match:
            category = best_match
            confidence = highest_confidence
        
        return category, confidence

    def _basic_categorization(self, results: List[Dict[str, Any]], categories: List[str]) -> List[Dict[str, Any]]:
        """Basic URL categorization without AI (legacy method)."""
        enhanced_results = []
        
        for result in results:
            category, confidence = self._pattern_categorize_url(result, categories)
            
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
        """Get the predefined categories configuration - now returns empty dict since categories come from user/DB."""
        # Categories are now dynamic and come from the test file or database
        logger.warning("📝 get_predefined_categories() called but categories are now dynamic")
        return {}

    def get_ai_status(self) -> Dict[str, Any]:
        """Get information about available AI services."""
        return {
            'openai_available': bool(self.llm),
            'cohere_available': bool(self.cohere_client),
            'fallback_method': 'pattern_matching',
            'categories_source': 'dynamic (from user/database)'
        } 