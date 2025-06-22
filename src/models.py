from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Boolean, Float, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class User(Base):
    """User model for multi-tenant support"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    competitors = relationship("Competitor", back_populates="user", cascade="all, delete-orphan")
    battle_cards = relationship("BattleCard", back_populates="user", cascade="all, delete-orphan")

class Competitor(Base):
    """Competitor model for tracking competitive intelligence"""
    __tablename__ = "competitors"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    website = Column(String(500))
    pricing_url = Column(String(500))  # Will be deprecated in favor of discovered URLs
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Scraping configuration
    scrape_frequency_hours = Column(String(50), default="6")  # "6", "12", "24", "weekly"
    last_scraped_at = Column(DateTime(timezone=True))
    
    # URL discovery status
    urls_discovered_at = Column(DateTime(timezone=True))
    url_discovery_status = Column(String(50), default="pending")  # "pending", "completed", "failed"
    
    # Relationships
    user = relationship("User", back_populates="competitors")
    scrape_results = relationship("ScrapeResult", back_populates="competitor", cascade="all, delete-orphan")
    urls = relationship("CompetitorUrl", back_populates="competitor", cascade="all, delete-orphan")
    social_media = relationship("SocialMediaData", back_populates="competitor", cascade="all, delete-orphan")

class CompetitorUrl(Base):
    """Discovered URLs for competitor pages (pricing, features, blog, social media)"""
    __tablename__ = "competitor_urls"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    competitor_id = Column(UUID(as_uuid=True), ForeignKey("competitors.id"), nullable=False, index=True)
    
    # URL details
    url_type = Column(String(50), nullable=False, index=True)  # 'pricing', 'features', 'blog', 'social_linkedin', etc.
    url = Column(String(1000), nullable=False)
    title = Column(String(500))
    description = Column(Text)
    
    # Discovery metadata
    confidence_score = Column(Float)  # 0.0-1.0 from LangChain analysis
    discovered_by = Column(String(50), default="langchain_search")  # 'langchain_search', 'manual', 'sitemap'
    discovery_method = Column(String(100))  # Details about how it was found
    
    # Status tracking
    status = Column(String(50), default="pending")  # 'pending', 'confirmed', 'rejected'
    discovered_at = Column(DateTime(timezone=True), server_default=func.now())
    confirmed_at = Column(DateTime(timezone=True))
    last_scraped_at = Column(DateTime(timezone=True))
    
    # Additional metadata
    metadata_ = Column(JSONB)  # Additional discovery data
    
    # Relationships
    competitor = relationship("Competitor", back_populates="urls")

class SocialMediaData(Base):
    """Social media data for competitors"""
    __tablename__ = "social_media_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    competitor_id = Column(UUID(as_uuid=True), ForeignKey("competitors.id"), nullable=False, index=True)
    
    # Platform details
    platform = Column(String(50), nullable=False, index=True)  # 'linkedin', 'twitter', 'instagram', 'tiktok'
    profile_url = Column(String(500), nullable=False)
    username = Column(String(255))  # Platform-specific username/handle
    
    # Metrics
    followers_count = Column(Integer)
    following_count = Column(Integer)
    posts_count = Column(Integer)
    
    # Content data
    latest_posts = Column(JSONB)  # Array of recent posts with metadata
    profile_info = Column(JSONB)  # Profile description, verified status, etc.
    engagement_metrics = Column(JSONB)  # Platform-specific metrics (likes, shares, etc.)
    
    # Tracking
    fetched_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated_at = Column(DateTime(timezone=True))
    fetch_status = Column(String(50), default="success")  # "success", "failed", "rate_limited"
    error_message = Column(Text)
    
    # Relationships
    competitor = relationship("Competitor", back_populates="social_media")

class ScrapeResult(Base):
    """Scrape results for storing competitive pricing and feature data"""
    __tablename__ = "scrape_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    competitor_id = Column(UUID(as_uuid=True), ForeignKey("competitors.id"), nullable=False, index=True)
    
    # Link to discovered URL (if applicable)
    competitor_url_id = Column(UUID(as_uuid=True), ForeignKey("competitor_urls.id"), nullable=True, index=True)
    
    # Scraped data stored as JSONB for flexibility
    prices = Column(JSONB)  # {"basic": 29, "pro": 99, "enterprise": "contact"}
    features = Column(JSONB)  # {"plan_name": ["feature1", "feature2"]}
    metadata_ = Column(JSONB)  # {"scrape_method": "scrapingbee", "page_title": "...", "response_time": 1.2}
    
    # Raw data for debugging
    raw_html_snippet = Column(Text)  # Store key sections for debugging
    
    # Status and timing
    scrape_status = Column(String(50), default="success")  # "success", "failed", "partial"
    error_message = Column(Text)
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    competitor = relationship("Competitor", back_populates="scrape_results")
    competitor_url = relationship("CompetitorUrl")

class BattleCard(Base):
    """AI-generated battle cards for competitive positioning"""
    __tablename__ = "battle_cards"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Battle card content
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)  # Markdown formatted content
    competitor_ids = Column(JSONB)  # List of competitor UUIDs used in analysis
    
    # AI generation metadata_
    ai_model_used = Column(String(100), default="gpt-4")
    generation_prompt = Column(Text)
    
    # Enhanced with social media insights
    includes_social_data = Column(Boolean, default=False)
    social_insights = Column(JSONB)  # Social media competitive analysis
    
    # Status and timing
    status = Column(String(50), default="generated")  # "generating", "generated", "failed"
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="battle_cards")

class ScrapeJob(Base):
    """Track scraping jobs and their status"""
    __tablename__ = "scrape_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    competitor_id = Column(UUID(as_uuid=True), ForeignKey("competitors.id"), nullable=False, index=True)
    
    # Job details
    job_type = Column(String(50), default="scheduled")  # "scheduled", "manual", "test", "url_discovery", "social_media"
    status = Column(String(50), default="pending")  # "pending", "running", "completed", "failed"
    
    # Enhanced job tracking
    target_url_type = Column(String(50))  # Specific URL type being scraped
    competitor_url_id = Column(UUID(as_uuid=True), ForeignKey("competitor_urls.id"))
    
    # Timing
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Results
    result_id = Column(UUID(as_uuid=True), ForeignKey("scrape_results.id"))
    error_message = Column(Text)
    
    # Relationships
    competitor = relationship("Competitor")
    result = relationship("ScrapeResult")
    competitor_url = relationship("CompetitorUrl") 