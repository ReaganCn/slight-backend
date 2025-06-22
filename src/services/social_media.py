"""
Social media data fetcher service for competitor analysis.
Supports LinkedIn, Twitter, Instagram, and TikTok platforms.
"""

import logging
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import json
import re
from urllib.parse import urlparse

# Social media API clients
import tweepy
from linkedin_api import Linkedin
import instaloader
from TikTokApi import TikTokApi

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class SocialMediaFetcher:
    """
    Unified social media data fetcher supporting multiple platforms
    """
    
    def __init__(self, config: Optional[Dict[str, str]] = None):
        """
        Initialize social media APIs
        
        Args:
            config: Dictionary containing API credentials
        """
        self.config = config or {}
        
        # Initialize API clients
        self.linkedin_client = None
        self.twitter_client = None
        self.instagram_loader = None
        self.tiktok_api = None
        
        self._setup_api_clients()
    
    def _setup_api_clients(self):
        """Setup API clients with available credentials"""
        try:
            # Twitter API v2 setup
            if self.config.get('TWITTER_BEARER_TOKEN'):
                self.twitter_client = tweepy.Client(
                    bearer_token=self.config['TWITTER_BEARER_TOKEN']
                )
                logger.info("✅ Twitter API client initialized")
            else:
                logger.warning("⚠️ Twitter API credentials not found")
            
            # LinkedIn API setup (unofficial)
            if self.config.get('LINKEDIN_EMAIL') and self.config.get('LINKEDIN_PASSWORD'):
                try:
                    self.linkedin_client = Linkedin(
                        self.config['LINKEDIN_EMAIL'],
                        self.config['LINKEDIN_PASSWORD']
                    )
                    logger.info("✅ LinkedIn API client initialized")
                except Exception as e:
                    logger.warning(f"⚠️ LinkedIn API setup failed: {e}")
            else:
                logger.warning("⚠️ LinkedIn API credentials not found")
            
            # Instagram API setup (unofficial)
            try:
                self.instagram_loader = instaloader.Instaloader()
                logger.info("✅ Instagram loader initialized")
            except Exception as e:
                logger.warning(f"⚠️ Instagram loader setup failed: {e}")
            
            # TikTok API setup (unofficial)
            try:
                self.tiktok_api = TikTokApi()
                logger.info("✅ TikTok API initialized")
            except Exception as e:
                logger.warning(f"⚠️ TikTok API setup failed: {e}")
                
        except Exception as e:
            logger.error(f"❌ Social media API setup failed: {e}")
    
    async def fetch_all_platforms(self, competitor_id: str, social_urls: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Fetch data from all discovered social media platforms
        
        Args:
            competitor_id: UUID of the competitor
            social_urls: List of social media URLs with platform info
            
        Returns:
            Dictionary with data from all platforms
        """
        logger.info(f"🔍 Fetching social media data for competitor {competitor_id}")
        
        results = {
            'competitor_id': competitor_id,
            'platforms': {},
            'summary': {
                'total_platforms': 0,
                'successful_fetches': 0,
                'failed_fetches': 0,
                'total_followers': 0
            },
            'fetched_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Group URLs by platform
        platform_urls = {}
        for url_data in social_urls:
            platform = url_data.get('platform', 'unknown')
            if platform not in platform_urls:
                platform_urls[platform] = []
            platform_urls[platform].append(url_data)
        
        # Fetch data from each platform in parallel
        tasks = []
        for platform, urls in platform_urls.items():
            if platform == 'social_linkedin':
                for url_data in urls:
                    tasks.append(self._fetch_linkedin_wrapper(url_data['url']))
            elif platform == 'social_twitter':
                for url_data in urls:
                    tasks.append(self._fetch_twitter_wrapper(url_data['url']))
            elif platform == 'social_instagram':
                for url_data in urls:
                    tasks.append(self._fetch_instagram_wrapper(url_data['url']))
            elif platform == 'social_tiktok':
                for url_data in urls:
                    tasks.append(self._fetch_tiktok_wrapper(url_data['url']))
        
        # Execute all fetches in parallel
        if tasks:
            task_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for result in task_results:
                if isinstance(result, Exception):
                    logger.error(f"Social media fetch failed: {result}")
                    results['summary']['failed_fetches'] += 1
                elif result and result.get('success'):
                    platform = result['platform']
                    results['platforms'][platform] = result['data']
                    results['summary']['successful_fetches'] += 1
                    
                    # Add to total followers
                    followers = result['data'].get('followers_count', 0)
                    if followers:
                        results['summary']['total_followers'] += followers
                else:
                    results['summary']['failed_fetches'] += 1
        
        results['summary']['total_platforms'] = len(platform_urls)
        
        logger.info(f"✅ Social media fetch completed: {results['summary']['successful_fetches']}/{results['summary']['total_platforms']} platforms")
        return results
    
    async def _fetch_linkedin_wrapper(self, profile_url: str) -> Dict[str, Any]:
        """Wrapper for LinkedIn data fetching with error handling"""
        try:
            data = await self.fetch_linkedin_data(profile_url)
            return {
                'success': True,
                'platform': 'linkedin',
                'data': data
            }
        except Exception as e:
            logger.error(f"LinkedIn fetch failed for {profile_url}: {e}")
            return {
                'success': False,
                'platform': 'linkedin',
                'error': str(e)
            }
    
    async def _fetch_twitter_wrapper(self, profile_url: str) -> Dict[str, Any]:
        """Wrapper for Twitter data fetching with error handling"""
        try:
            data = await self.fetch_twitter_data(profile_url)
            return {
                'success': True,
                'platform': 'twitter',
                'data': data
            }
        except Exception as e:
            logger.error(f"Twitter fetch failed for {profile_url}: {e}")
            return {
                'success': False,
                'platform': 'twitter',
                'error': str(e)
            }
    
    async def _fetch_instagram_wrapper(self, profile_url: str) -> Dict[str, Any]:
        """Wrapper for Instagram data fetching with error handling"""
        try:
            data = await self.fetch_instagram_data(profile_url)
            return {
                'success': True,
                'platform': 'instagram',
                'data': data
            }
        except Exception as e:
            logger.error(f"Instagram fetch failed for {profile_url}: {e}")
            return {
                'success': False,
                'platform': 'instagram',
                'error': str(e)
            }
    
    async def _fetch_tiktok_wrapper(self, profile_url: str) -> Dict[str, Any]:
        """Wrapper for TikTok data fetching with error handling"""
        try:
            data = await self.fetch_tiktok_data(profile_url)
            return {
                'success': True,
                'platform': 'tiktok',
                'data': data
            }
        except Exception as e:
            logger.error(f"TikTok fetch failed for {profile_url}: {e}")
            return {
                'success': False,
                'platform': 'tiktok',
                'error': str(e)
            }
    
    async def fetch_linkedin_data(self, profile_url: str) -> Dict[str, Any]:
        """
        Fetch LinkedIn company data
        
        Args:
            profile_url: LinkedIn company page URL
            
        Returns:
            Dictionary with LinkedIn company data
        """
        if not self.linkedin_client:
            raise ValueError("LinkedIn API client not available")
        
        # Extract company identifier from URL
        company_id = self._extract_linkedin_company_id(profile_url)
        
        try:
            # Fetch company data
            company_data = self.linkedin_client.get_company(company_id)
            
            # Get company updates/posts
            try:
                company_updates = self.linkedin_client.get_company_updates(
                    company_id, 
                    max_results=10
                )
            except:
                company_updates = []
            
            return {
                'profile_url': profile_url,
                'company_id': company_id,
                'name': company_data.get('name', ''),
                'description': company_data.get('description', ''),
                'industry': company_data.get('industry', ''),
                'company_size': company_data.get('companySize', ''),
                'followers_count': company_data.get('followersCount', 0),
                'employee_count': company_data.get('employeesCount', 0),
                'founded_year': company_data.get('foundedYear'),
                'headquarters': company_data.get('headquarters', {}),
                'website': company_data.get('website', ''),
                'latest_posts': self._format_linkedin_posts(company_updates[:5]),
                'engagement_metrics': {
                    'average_likes': self._calculate_linkedin_engagement(company_updates, 'likes'),
                    'average_comments': self._calculate_linkedin_engagement(company_updates, 'comments'),
                    'post_frequency': len(company_updates)
                },
                'fetched_at': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"LinkedIn data fetch failed: {e}")
            raise
    
    async def fetch_twitter_data(self, profile_url: str) -> Dict[str, Any]:
        """
        Fetch Twitter/X data
        
        Args:
            profile_url: Twitter profile URL
            
        Returns:
            Dictionary with Twitter data
        """
        if not self.twitter_client:
            raise ValueError("Twitter API client not available")
        
        # Extract username from URL
        username = self._extract_twitter_username(profile_url)
        
        try:
            # Get user info
            user = self.twitter_client.get_user(username=username, user_fields=[
                'created_at', 'description', 'public_metrics', 'verified'
            ])
            
            if not user.data:
                raise ValueError(f"User {username} not found")
            
            user_data = user.data
            
            # Get recent tweets
            tweets = self.twitter_client.get_users_tweets(
                user_data.id,
                max_results=10,
                tweet_fields=['created_at', 'public_metrics', 'context_annotations']
            )
            
            return {
                'profile_url': profile_url,
                'username': username,
                'user_id': user_data.id,
                'name': user_data.name,
                'description': user_data.description,
                'followers_count': user_data.public_metrics['followers_count'],
                'following_count': user_data.public_metrics['following_count'],
                'posts_count': user_data.public_metrics['tweet_count'],
                'verified': getattr(user_data, 'verified', False),
                'created_at': user_data.created_at.isoformat() if user_data.created_at else None,
                'latest_posts': self._format_twitter_tweets(tweets.data[:5] if tweets.data else []),
                'engagement_metrics': {
                    'average_likes': self._calculate_twitter_engagement(tweets.data, 'like_count'),
                    'average_retweets': self._calculate_twitter_engagement(tweets.data, 'retweet_count'),
                    'average_replies': self._calculate_twitter_engagement(tweets.data, 'reply_count'),
                    'post_frequency': len(tweets.data) if tweets.data else 0
                },
                'fetched_at': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Twitter data fetch failed: {e}")
            raise
    
    async def fetch_instagram_data(self, profile_url: str) -> Dict[str, Any]:
        """
        Fetch Instagram business data
        
        Args:
            profile_url: Instagram profile URL
            
        Returns:
            Dictionary with Instagram data
        """
        if not self.instagram_loader:
            raise ValueError("Instagram loader not available")
        
        # Extract username from URL
        username = self._extract_instagram_username(profile_url)
        
        try:
            # Get profile data
            profile = instaloader.Profile.from_username(self.instagram_loader.context, username)
            
            # Get recent posts
            posts = []
            post_count = 0
            for post in profile.get_posts():
                if post_count >= 5:  # Limit to 5 recent posts
                    break
                posts.append({
                    'shortcode': post.shortcode,
                    'caption': post.caption[:200] if post.caption else '',
                    'likes': post.likes,
                    'comments': post.comments,
                    'date': post.date.isoformat(),
                    'is_video': post.is_video,
                    'url': f"https://www.instagram.com/p/{post.shortcode}/"
                })
                post_count += 1
            
            return {
                'profile_url': profile_url,
                'username': username,
                'user_id': profile.userid,
                'full_name': profile.full_name,
                'biography': profile.biography,
                'followers_count': profile.followers,
                'following_count': profile.followees,
                'posts_count': profile.mediacount,
                'is_business_account': profile.is_business_account,
                'is_verified': profile.is_verified,
                'external_url': profile.external_url,
                'latest_posts': posts,
                'engagement_metrics': {
                    'average_likes': sum(post['likes'] for post in posts) / len(posts) if posts else 0,
                    'average_comments': sum(post['comments'] for post in posts) / len(posts) if posts else 0,
                    'engagement_rate': self._calculate_instagram_engagement_rate(posts, profile.followers),
                    'post_frequency': len(posts)
                },
                'fetched_at': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Instagram data fetch failed: {e}")
            raise
    
    async def fetch_tiktok_data(self, profile_url: str) -> Dict[str, Any]:
        """
        Fetch TikTok data
        
        Args:
            profile_url: TikTok profile URL
            
        Returns:
            Dictionary with TikTok data
        """
        if not self.tiktok_api:
            raise ValueError("TikTok API not available")
        
        # Extract username from URL
        username = self._extract_tiktok_username(profile_url)
        
        try:
            # Get user info
            user_data = await self.tiktok_api.user(username).info()
            
            # Get recent videos
            videos = []
            async for video in self.tiktok_api.user(username).videos(count=5):
                videos.append({
                    'id': video.id,
                    'description': video.desc[:200] if video.desc else '',
                    'likes': video.stats['diggCount'],
                    'comments': video.stats['commentCount'],
                    'shares': video.stats['shareCount'],
                    'views': video.stats['playCount'],
                    'created_at': video.createTime,
                    'url': f"https://www.tiktok.com/@{username}/video/{video.id}"
                })
            
            return {
                'profile_url': profile_url,
                'username': username,
                'user_id': user_data.id,
                'display_name': user_data.display_name,
                'bio': user_data.bio,
                'followers_count': user_data.stats['followerCount'],
                'following_count': user_data.stats['followingCount'],
                'posts_count': user_data.stats['videoCount'],
                'likes_count': user_data.stats['heartCount'],
                'is_verified': user_data.verified,
                'latest_posts': videos,
                'engagement_metrics': {
                    'average_likes': sum(video['likes'] for video in videos) / len(videos) if videos else 0,
                    'average_comments': sum(video['comments'] for video in videos) / len(videos) if videos else 0,
                    'average_shares': sum(video['shares'] for video in videos) / len(videos) if videos else 0,
                    'average_views': sum(video['views'] for video in videos) / len(videos) if videos else 0,
                    'engagement_rate': self._calculate_tiktok_engagement_rate(videos, user_data.stats['followerCount']),
                    'post_frequency': len(videos)
                },
                'fetched_at': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"TikTok data fetch failed: {e}")
            raise
    
    def _extract_linkedin_company_id(self, url: str) -> str:
        """Extract LinkedIn company ID from URL"""
        # Pattern: https://www.linkedin.com/company/company-name/
        match = re.search(r'linkedin\.com/company/([^/]+)', url)
        if match:
            return match.group(1)
        raise ValueError(f"Could not extract LinkedIn company ID from {url}")
    
    def _extract_twitter_username(self, url: str) -> str:
        """Extract Twitter username from URL"""
        # Pattern: https://twitter.com/username or https://x.com/username
        match = re.search(r'(?:twitter\.com|x\.com)/([^/]+)', url)
        if match:
            return match.group(1)
        raise ValueError(f"Could not extract Twitter username from {url}")
    
    def _extract_instagram_username(self, url: str) -> str:
        """Extract Instagram username from URL"""
        # Pattern: https://www.instagram.com/username/
        match = re.search(r'instagram\.com/([^/]+)', url)
        if match:
            return match.group(1)
        raise ValueError(f"Could not extract Instagram username from {url}")
    
    def _extract_tiktok_username(self, url: str) -> str:
        """Extract TikTok username from URL"""
        # Pattern: https://www.tiktok.com/@username
        match = re.search(r'tiktok\.com/@([^/]+)', url)
        if match:
            return match.group(1)
        raise ValueError(f"Could not extract TikTok username from {url}")
    
    def _format_linkedin_posts(self, posts: List[Any]) -> List[Dict[str, Any]]:
        """Format LinkedIn posts for storage"""
        formatted_posts = []
        for post in posts[:5]:  # Limit to 5 posts
            try:
                formatted_posts.append({
                    'id': post.get('id', ''),
                    'text': post.get('text', '')[:300],  # Limit text length
                    'date': post.get('date', ''),
                    'likes': post.get('likes', 0),
                    'comments': post.get('comments', 0),
                    'shares': post.get('shares', 0)
                })
            except:
                continue
        return formatted_posts
    
    def _format_twitter_tweets(self, tweets: List[Any]) -> List[Dict[str, Any]]:
        """Format Twitter tweets for storage"""
        formatted_tweets = []
        for tweet in tweets[:5]:  # Limit to 5 tweets
            try:
                formatted_tweets.append({
                    'id': tweet.id,
                    'text': tweet.text[:300],  # Limit text length
                    'created_at': tweet.created_at.isoformat() if tweet.created_at else '',
                    'likes': tweet.public_metrics.get('like_count', 0),
                    'retweets': tweet.public_metrics.get('retweet_count', 0),
                    'replies': tweet.public_metrics.get('reply_count', 0),
                    'quotes': tweet.public_metrics.get('quote_count', 0)
                })
            except:
                continue
        return formatted_tweets
    
    def _calculate_linkedin_engagement(self, posts: List[Any], metric: str) -> float:
        """Calculate average LinkedIn engagement metrics"""
        if not posts:
            return 0.0
        
        total = sum(post.get(metric, 0) for post in posts)
        return total / len(posts)
    
    def _calculate_twitter_engagement(self, tweets: List[Any], metric: str) -> float:
        """Calculate average Twitter engagement metrics"""
        if not tweets:
            return 0.0
        
        total = sum(tweet.public_metrics.get(metric, 0) for tweet in tweets)
        return total / len(tweets)
    
    def _calculate_instagram_engagement_rate(self, posts: List[Dict[str, Any]], followers: int) -> float:
        """Calculate Instagram engagement rate"""
        if not posts or followers == 0:
            return 0.0
        
        total_engagement = sum((post['likes'] + post['comments']) for post in posts)
        avg_engagement = total_engagement / len(posts)
        return (avg_engagement / followers) * 100  # Return as percentage
    
    def _calculate_tiktok_engagement_rate(self, videos: List[Dict[str, Any]], followers: int) -> float:
        """Calculate TikTok engagement rate"""
        if not videos or followers == 0:
            return 0.0
        
        total_engagement = sum((video['likes'] + video['comments'] + video['shares']) for video in videos)
        avg_engagement = total_engagement / len(videos)
        return (avg_engagement / followers) * 100  # Return as percentage 