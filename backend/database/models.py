from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class SocialMediaPost(Base):
    """Model for storing social media posts and reviews."""
    __tablename__ = 'social_media_posts'
    
    id = Column(Integer, primary_key=True)
    platform = Column(String(50), nullable=False)  # reddit, linkedin, google_reviews, g2, etc.
    post_id = Column(String(255), unique=True, nullable=False)  # Original platform post ID
    title = Column(String(500))
    content = Column(Text, nullable=False)
    author = Column(String(255))
    url = Column(String(1000))
    created_at = Column(DateTime, nullable=False)
    collected_at = Column(DateTime, default=datetime.utcnow)
    
    # Engagement metrics
    upvotes = Column(Integer, default=0)
    downvotes = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    
    # Analysis results
    sentiment_score = Column(Float)
    sentiment_label = Column(String(20))  # positive, negative, neutral
    confidence_score = Column(Float)
    
    # Metadata
    is_processed = Column(Boolean, default=False)
    language = Column(String(10), default='en')
    raw_data = Column(JSON)  # Store original data structure
    
    # Relationships
    themes = relationship("PostTheme", back_populates="post")
    keywords = relationship("PostKeyword", back_populates="post")

class Theme(Base):
    """Model for storing identified themes/topics."""
    __tablename__ = 'themes'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
    category = Column(String(100))  # product, customer_service, pricing, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    posts = relationship("PostTheme", back_populates="theme")

class PostTheme(Base):
    """Association table for posts and themes with relevance scores."""
    __tablename__ = 'post_themes'
    
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey('social_media_posts.id'), nullable=False)
    theme_id = Column(Integer, ForeignKey('themes.id'), nullable=False)
    relevance_score = Column(Float, nullable=False)  # 0.0 to 1.0
    confidence = Column(Float)
    
    # Relationships
    post = relationship("SocialMediaPost", back_populates="themes")
    theme = relationship("Theme", back_populates="posts")

class Keyword(Base):
    """Model for storing keywords and mentions."""
    __tablename__ = 'keywords'
    
    id = Column(Integer, primary_key=True)
    word = Column(String(255), unique=True, nullable=False)
    category = Column(String(100))  # brand, product, competitor, etc.
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    posts = relationship("PostKeyword", back_populates="keyword")

class PostKeyword(Base):
    """Association table for posts and keywords with mention counts."""
    __tablename__ = 'post_keywords'
    
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey('social_media_posts.id'), nullable=False)
    keyword_id = Column(Integer, ForeignKey('keywords.id'), nullable=False)
    mention_count = Column(Integer, default=1)
    context = Column(Text)  # Surrounding text context
    
    # Relationships
    post = relationship("SocialMediaPost", back_populates="keywords")
    keyword = relationship("Keyword", back_populates="posts")

class SentimentTrend(Base):
    """Model for storing aggregated sentiment trends over time."""
    __tablename__ = 'sentiment_trends'
    
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False)
    platform = Column(String(50), nullable=False)
    theme_id = Column(Integer, ForeignKey('themes.id'))
    
    # Sentiment metrics
    avg_sentiment_score = Column(Float)
    positive_count = Column(Integer, default=0)
    negative_count = Column(Integer, default=0)
    neutral_count = Column(Integer, default=0)
    total_posts = Column(Integer, default=0)
    
    # Engagement metrics
    avg_engagement = Column(Float)
    total_reach = Column(Integer, default=0)
    
    # Relationships
    theme = relationship("Theme")

class CompetitorMention(Base):
    """Model for tracking competitor mentions."""
    __tablename__ = 'competitor_mentions'
    
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey('social_media_posts.id'), nullable=False)
    competitor_name = Column(String(255), nullable=False)
    mention_type = Column(String(50))  # comparison, alternative, review, etc.
    context = Column(Text)
    sentiment_towards_competitor = Column(Float)
    
    # Relationships
    post = relationship("SocialMediaPost")

class DataCollection(Base):
    """Model for tracking data collection runs."""
    __tablename__ = 'data_collections'
    
    id = Column(Integer, primary_key=True)
    platform = Column(String(50), nullable=False)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    status = Column(String(20), default='running')  # running, completed, failed
    posts_collected = Column(Integer, default=0)
    errors_encountered = Column(Integer, default=0)
    search_terms = Column(JSON)
    error_log = Column(Text) 