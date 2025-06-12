from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Boolean
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
    pricing_url = Column(String(500))
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Scraping configuration
    scrape_frequency_hours = Column(String(50), default="6")  # "6", "12", "24", "weekly"
    last_scraped_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="competitors")
    scrape_results = relationship("ScrapeResult", back_populates="competitor", cascade="all, delete-orphan")

class ScrapeResult(Base):
    """Scrape results for storing competitive pricing and feature data"""
    __tablename__ = "scrape_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    competitor_id = Column(UUID(as_uuid=True), ForeignKey("competitors.id"), nullable=False, index=True)
    
    # Scraped data stored as JSONB for flexibility
    prices = Column(JSONB)  # {"basic": 29, "pro": 99, "enterprise": "contact"}
    features = Column(JSONB)  # {"plan_name": ["feature1", "feature2"]}
    metadata = Column(JSONB)  # {"scrape_method": "scrapingbee", "page_title": "...", "response_time": 1.2}
    
    # Raw data for debugging
    raw_html_snippet = Column(Text)  # Store key sections for debugging
    
    # Status and timing
    scrape_status = Column(String(50), default="success")  # "success", "failed", "partial"
    error_message = Column(Text)
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    competitor = relationship("Competitor", back_populates="scrape_results")

class BattleCard(Base):
    """AI-generated battle cards for competitive positioning"""
    __tablename__ = "battle_cards"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Battle card content
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)  # Markdown formatted content
    competitor_ids = Column(JSONB)  # List of competitor UUIDs used in analysis
    
    # AI generation metadata
    ai_model_used = Column(String(100), default="gpt-4")
    generation_prompt = Column(Text)
    
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
    job_type = Column(String(50), default="scheduled")  # "scheduled", "manual", "test"
    status = Column(String(50), default="pending")  # "pending", "running", "completed", "failed"
    
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