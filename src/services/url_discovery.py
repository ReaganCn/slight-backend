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
                                     selection_llm: str = "cohere",  # LLM for final selection
                                     min_confidence_threshold: float = 0.6) -> List[Dict[str, Any]]:  # Minimum confidence threshold
        """
        Simplified URL discovery workflow with confidence validation:
        1. Search for each category (implicit categorization)
        2. Use LLM to rank top 10 most relevant URLs per category
        3. Use LLM to select single best URL from top 10
        4. Validate confidence and brand recognition before returning results
        
        Args:
            competitor_name: Name of the competitor
            base_url: Base URL of the competitor
            search_depth: Search depth (standard, comprehensive)
            categories: List of categories to search for
            ranking_llm: LLM to use for relevance ranking ("cohere", "openai")
            selection_llm: LLM to use for final selection ("cohere", "openai")
            min_confidence_threshold: Minimum confidence required to return results (0.0-1.0)
        """
        logger.info(f"🔍 Starting simplified URL discovery for {competitor_name}")
        logger.info(f"🏷️ Searching for categories: {categories}")
        logger.info(f"🤖 Using {ranking_llm} for ranking, {selection_llm} for selection")
        logger.info(f"🎯 Minimum confidence threshold: {min_confidence_threshold}")
        
        if not categories:
            categories = ['pricing', 'features', 'blog']
        
        # Step 1: Validate company and discover official domains
        logger.info(f"🔍 Step 1: Validating company and discovering domains for {competitor_name}...")
        domain_discovery_result = await self._discover_brand_domains_with_confidence(competitor_name, base_url)
        
        if not domain_discovery_result['success']:
            logger.warning(f"⚠️ Company validation failed: {domain_discovery_result['reason']}")
            return []  # Return empty results rather than wrong results
        
        official_domains = domain_discovery_result['domains']
        brand_confidence = domain_discovery_result['confidence']
        
        logger.info(f"✅ Brand validation successful (confidence: {brand_confidence:.2f})")
        logger.info(f"🔍 Validated domains: {official_domains}")
        
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
        
        # Step 4: Filter to same-domain URLs and validate relevance
        logger.info(f"🔍 Step 4: Filtering and validating results...")
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
            
            # Step 5: Use LLM to rank top 10 most relevant URLs with confidence validation
            logger.info(f"🤖 Step 5: Using {ranking_llm} to rank most relevant URLs for {category}...")
            ranking_result = await self._llm_rank_urls_for_category_with_confidence(
                same_domain_results, category, competitor_name, ranking_llm, limit=10
            )
            
            if not ranking_result['success']:
                logger.warning(f"⚠️ Ranking failed for {category}: {ranking_result['reason']}")
                continue
            
            top_urls = ranking_result['urls']
            ranking_confidence = ranking_result['confidence']
            
            # Step 6: Use LLM to select best URL with confidence validation
            logger.info(f"🤖 Step 6: Using {selection_llm} to select best URL from top {len(top_urls)} for {category}...")
            selection_result = await self._llm_select_best_url_with_confidence(
                top_urls, category, competitor_name, selection_llm
            )
            
            if not selection_result['success']:
                logger.warning(f"⚠️ Selection failed for {category}: {selection_result['reason']}")
                continue
            
            best_url = selection_result['url']
            selection_confidence = selection_result['confidence']
            
            # Calculate overall confidence
            overall_confidence = min(brand_confidence, ranking_confidence, selection_confidence)
            
            # Apply confidence threshold
            if overall_confidence < min_confidence_threshold:
                logger.warning(f"⚠️ {category}: Overall confidence {overall_confidence:.2f} below threshold {min_confidence_threshold}")
                logger.warning(f"   Skipping to avoid potentially incorrect results")
                continue
            
            final_results.append({
                **best_url,
                'category': category,
                'confidence_score': overall_confidence,
                'discovery_method': f'{ranking_llm}_ranking + {selection_llm}_selection',
                'ranking_llm': ranking_llm,
                'selection_llm': selection_llm,
                'brand_confidence': brand_confidence,
                'ranking_confidence': ranking_confidence,
                'selection_confidence': selection_confidence
            })
            logger.info(f"✅ {category.upper()}: Selected {best_url.get('url')} (confidence: {overall_confidence:.2f})")
        
        logger.info(f"🎯 Discovery complete: {len(final_results)} URLs found across {len(categories)} categories")
        
        if len(final_results) == 0:
            logger.warning(f"⚠️ No URLs met confidence threshold {min_confidence_threshold}")
            logger.warning(f"   This may indicate the company is not well-known or search results are unreliable")
        
        return final_results

    async def _discover_brand_domains_with_confidence(self, competitor_name: str, base_url: str) -> Dict[str, Any]:
        """Discover brand domains with confidence validation."""
        try:
            # First validate the company exists and is recognizable
            validation_result = await self._validate_brand_recognition(competitor_name, base_url)
            
            if not validation_result['is_recognized']:
                return {
                    'success': False,
                    'reason': f"Brand not well-recognized: {validation_result['reason']}",
                    'confidence': validation_result['confidence']
                }
            
            # Proceed with domain discovery
            domains = await self._discover_brand_domains(competitor_name, base_url)
            
            # Validate discovered domains
            domain_validation = await self._validate_discovered_domains(domains, competitor_name, base_url)
            
            return {
                'success': domain_validation['valid'],
                'domains': domains if domain_validation['valid'] else [],
                'confidence': min(validation_result['confidence'], domain_validation['confidence']),
                'reason': domain_validation.get('reason', 'Success')
            }
            
        except Exception as e:
            logger.error(f"❌ Brand domain discovery failed: {e}")
            return {
                'success': False,
                'reason': f"Discovery error: {str(e)}",
                'confidence': 0.0
            }

    async def _validate_brand_recognition(self, competitor_name: str, base_url: str) -> Dict[str, Any]:
        """Validate if the brand is well-recognized to avoid wrong results."""
        prompt = f"""
        Evaluate if "{competitor_name}" is a well-known, legitimate company or brand.
        
        Website: {base_url}
        
        Consider:
        - Is this a real company/product that exists?
        - Is it well-known enough to have reliable search results?
        - Would search engines return accurate information about this brand?
        - Is the website domain consistent with the company name?
        
        Respond with:
        RECOGNIZED: [YES/NO]
        CONFIDENCE: [0.0-1.0]
        REASON: [Brief explanation]
        
        Example responses:
        RECOGNIZED: YES
        CONFIDENCE: 0.9
        REASON: Well-known productivity software company
        
        RECOGNIZED: NO
        CONFIDENCE: 0.2
        REASON: Unknown company name, may be startup or fictional
        """
        
        try:
            if hasattr(self, 'cohere_client') and self.cohere_client:
                response_text = await self._cohere_query(prompt)
            else:
                response_text = await self._openai_query(prompt)
            
            # Parse response
            lines = response_text.strip().split('\n')
            recognized = False
            confidence = 0.0
            reason = "Unknown"
            
            for line in lines:
                line = line.strip()
                if line.startswith('RECOGNIZED:'):
                    recognized = 'YES' in line.upper()
                elif line.startswith('CONFIDENCE:'):
                    try:
                        confidence = float(line.split(':')[1].strip())
                    except:
                        confidence = 0.5
                elif line.startswith('REASON:'):
                    reason = line.split(':', 1)[1].strip()
            
            return {
                'is_recognized': recognized,
                'confidence': confidence,
                'reason': reason
            }
            
        except Exception as e:
            logger.error(f"❌ Brand recognition validation failed: {e}")
            return {
                'is_recognized': False,
                'confidence': 0.0,
                'reason': f"Validation error: {str(e)}"
            }

    async def _validate_discovered_domains(self, domains: List[str], competitor_name: str, base_url: str) -> Dict[str, Any]:
        """Validate that discovered domains are actually related to the company."""
        if not domains:
            return {'valid': False, 'confidence': 0.0, 'reason': 'No domains discovered'}
        
        # Check if base domain is in discovered domains
        base_domain = self._extract_domain(base_url)
        domain_match = any(self._domains_match(base_domain, domain) for domain in domains)
        
        if not domain_match:
            return {
                'valid': False, 
                'confidence': 0.0, 
                'reason': f'Base domain {base_domain} not found in discovered domains {domains}'
            }
        
        # Additional validation with LLM
        prompt = f"""
        Validate if these domains are actually related to "{competitor_name}":
        
        Discovered domains: {domains}
        Expected base domain: {base_domain}
        
        Are these domains legitimate and related to the company?
        
        Respond with:
        VALID: [YES/NO]
        CONFIDENCE: [0.0-1.0]
        REASON: [Brief explanation]
        """
        
        try:
            if hasattr(self, 'cohere_client') and self.cohere_client:
                response_text = await self._cohere_query(prompt)
            else:
                response_text = await self._openai_query(prompt)
            
            # Parse response
            lines = response_text.strip().split('\n')
            valid = True  # Default to valid if we can't parse
            confidence = 0.8
            reason = "Domain validation successful"
            
            for line in lines:
                line = line.strip()
                if line.startswith('VALID:'):
                    valid = 'YES' in line.upper()
                elif line.startswith('CONFIDENCE:'):
                    try:
                        confidence = float(line.split(':')[1].strip())
                    except:
                        confidence = 0.8
                elif line.startswith('REASON:'):
                    reason = line.split(':', 1)[1].strip()
            
            return {
                'valid': valid,
                'confidence': confidence,
                'reason': reason
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Domain validation failed, proceeding with basic validation: {e}")
            return {
                'valid': domain_match,
                'confidence': 0.7 if domain_match else 0.0,
                'reason': "Basic domain matching validation"
            }

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except:
            return url.lower()

    def _domains_match(self, domain1: str, domain2: str) -> bool:
        """Check if two domains match (considering subdomains)."""
        domain1 = domain1.lower().strip()
        domain2 = domain2.lower().strip()
        
        # Direct match
        if domain1 == domain2:
            return True
        
        # Remove www prefix for comparison
        domain1_clean = domain1.replace('www.', '')
        domain2_clean = domain2.replace('www.', '')
        
        if domain1_clean == domain2_clean:
            return True
        
        # Check if one is a subdomain of the other
        if domain1_clean.endswith('.' + domain2_clean) or domain2_clean.endswith('.' + domain1_clean):
            return True
        
        return False

    async def _llm_rank_urls_for_category_with_confidence(self, urls: List[Dict[str, Any]], category: str, 
                                        competitor_name: str, llm_choice: str, limit: int = 10) -> Dict[str, Any]:
        """Use LLM to rank URLs by relevance with confidence validation."""
        if not urls:
            return {'success': False, 'reason': 'No URLs to rank', 'confidence': 0.0}
        
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
        
        IMPORTANT: If none of the URLs seem relevant to {category} for {competitor_name}, 
        respond with "NO_RELEVANT_URLS" instead of ranking.
        
        If URLs are relevant, respond with the top {limit} most relevant URLs in order:
        RANKING: [URL numbers in order]
        CONFIDENCE: [0.0-1.0 confidence in the ranking]
        REASON: [Brief explanation]
        
        Example response:
        RANKING: 3,7,1,5
        CONFIDENCE: 0.8
        REASON: URLs clearly related to pricing with official domain
        """
        
        try:
            if llm_choice == "cohere":
                response_text = await self._cohere_query(prompt)
            else:  # openai
                response_text = await self._openai_query(prompt)
            
            # Check for no relevant URLs response
            if "NO_RELEVANT_URLS" in response_text.upper():
                return {
                    'success': False,
                    'reason': 'LLM determined no URLs are relevant for this category',
                    'confidence': 0.0
                }
            
            # Parse the ranking response
            ranking_line = ""
            confidence = 0.5
            reason = "Ranking completed"
            
            for line in response_text.split('\n'):
                line = line.strip()
                if line.startswith('RANKING:'):
                    ranking_line = line.split(':', 1)[1].strip()
                elif line.startswith('CONFIDENCE:'):
                    try:
                        confidence = float(line.split(':')[1].strip())
                    except:
                        confidence = 0.5
                elif line.startswith('REASON:'):
                    reason = line.split(':', 1)[1].strip()
            
            if not ranking_line:
                return {
                    'success': False,
                    'reason': 'Could not parse ranking response',
                    'confidence': 0.0
                }
            
            # Parse ranking indices
            ranked_indices = []
            for num_str in ranking_line.split(','):
                try:
                    idx = int(num_str.strip()) - 1  # Convert to 0-based index
                    if 0 <= idx < len(input_urls):
                        ranked_indices.append(idx)
                except ValueError:
                    continue
            
            if not ranked_indices:
                return {
                    'success': False,
                    'reason': 'No valid ranking indices found',
                    'confidence': 0.0
                }
            
            # Return URLs in ranked order
            ranked_urls = []
            for idx in ranked_indices[:limit]:
                ranked_urls.append(input_urls[idx])
            
            logger.info(f"📊 Ranked {len(ranked_urls)} URLs for {category} using {llm_choice} (confidence: {confidence:.2f})")
            
            return {
                'success': True,
                'urls': ranked_urls,
                'confidence': confidence,
                'reason': reason
            }
            
        except Exception as e:
            logger.error(f"❌ LLM ranking failed for {category}: {e}")
            return {
                'success': False,
                'reason': f'Ranking error: {str(e)}',
                'confidence': 0.0
            }

    async def _llm_select_best_url_with_confidence(self, urls: List[Dict[str, Any]], category: str, 
                                 competitor_name: str, llm_choice: str) -> Dict[str, Any]:
        """Use LLM to select the single best URL with confidence validation."""
        if not urls:
            return {'success': False, 'reason': 'No URLs to select from', 'confidence': 0.0}
        
        if len(urls) == 1:
            return {
                'success': True,
                'url': urls[0],
                'confidence': 0.8,  # High confidence for single option
                'reason': 'Single URL available'
            }
        
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
        
        IMPORTANT: If none of the URLs seem appropriate for {category} information about {competitor_name},
        respond with "NO_SUITABLE_URL" instead of selecting.
        
        If a URL is suitable, respond with:
        SELECTION: [URL number]
        CONFIDENCE: [0.0-1.0 confidence in the selection]
        REASON: [Brief explanation why this URL is best]
        
        Example response:
        SELECTION: 2
        CONFIDENCE: 0.9
        REASON: Official pricing page with comprehensive plan details
        """
        
        try:
            if llm_choice == "cohere":
                response_text = await self._cohere_query(prompt)
            else:  # openai
                response_text = await self._openai_query(prompt)
            
            # Check for no suitable URL response
            if "NO_SUITABLE_URL" in response_text.upper():
                return {
                    'success': False,
                    'reason': 'LLM determined no URLs are suitable for this category',
                    'confidence': 0.0
                }
            
            # Parse the selection response
            selection_num = None
            confidence = 0.5
            reason = "Selection completed"
            
            for line in response_text.split('\n'):
                line = line.strip()
                if line.startswith('SELECTION:'):
                    try:
                        selection_num = int(line.split(':')[1].strip())
                    except:
                        continue
                elif line.startswith('CONFIDENCE:'):
                    try:
                        confidence = float(line.split(':')[1].strip())
                    except:
                        confidence = 0.5
                elif line.startswith('REASON:'):
                    reason = line.split(':', 1)[1].strip()
            
            if selection_num is None or selection_num < 1 or selection_num > len(urls):
                return {
                    'success': False,
                    'reason': 'Invalid or missing selection number',
                    'confidence': 0.0
                }
            
            selected_url = urls[selection_num - 1]  # Convert to 0-based index
            
            logger.info(f"🎯 Selected URL {selection_num} for {category} using {llm_choice} (confidence: {confidence:.2f})")
            
            return {
                'success': True,
                'url': selected_url,
                'confidence': confidence,
                'reason': reason
            }
            
        except Exception as e:
            logger.error(f"❌ LLM selection failed for {category}: {e}")
            return {
                'success': False,
                'reason': f'Selection error: {str(e)}',
                'confidence': 0.0
            }

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

    def _is_same_brand_domain(self, url_domain: str, base_domain: str, official_domains: List[str]) -> bool:
        """Check if URL domain matches any of the discovered official brand domains."""
        url_domain_clean = url_domain.replace('www.', '').lower()
        
        for official_domain in official_domains:
            official_domain_clean = official_domain.replace('www.', '').lower()
            
            # Direct match
            if url_domain_clean == official_domain_clean:
                return True
            
            # Subdomain match (e.g., app.cursor.com matches cursor.com)
            if url_domain_clean.endswith('.' + official_domain_clean):
                return True
                
            # Reverse subdomain match (e.g., cursor.com matches app.cursor.com)
            if official_domain_clean.endswith('.' + url_domain_clean):
                return True
        
        return False

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

    async def _cohere_query(self, prompt: str) -> str:
        """Execute a Cohere query."""
        if not hasattr(self, 'cohere_client') or not self.cohere_client:
            raise Exception("Cohere client not available")
        
        response = await asyncio.get_event_loop().run_in_executor(
            None, lambda: self.cohere_client.invoke(prompt)
        )
        
        if hasattr(response, 'content'):
            return response.content
        else:
            return str(response)

    async def _openai_query(self, prompt: str) -> str:
        """Execute an OpenAI query."""
        if not self.openai_api_key:
            raise Exception("OpenAI API key not available")
        
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