#!/usr/bin/env python3
"""
Re-analyze sentiment for all existing posts using improved Gusto-specific sentiment analysis.
This script updates sentiment scores to focus only on Gusto-related sentiment.
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.database.database import get_session
from backend.database.models import SocialMediaPost
from utils.sentiment_analyzer import SentimentAnalyzer
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reanalyze_all_posts():
    """Re-analyze sentiment for all posts in the database using improved Gusto-specific logic."""
    
    logger.info("🔄 Starting sentiment re-analysis for all posts...")
    
    # Initialize sentiment analyzer
    sentiment_analyzer = SentimentAnalyzer()
    
    # Get all posts from database
    with get_session() as session:
        posts = session.query(SocialMediaPost).filter(
            SocialMediaPost.platform == 'reddit'
        ).all()
        
        logger.info(f"📊 Found {len(posts)} Reddit posts to re-analyze")
        
        updated_count = 0
        changed_sentiment_count = 0
        
        for i, post in enumerate(posts, 1):
            if i % 10 == 0:
                logger.info(f"📈 Progress: {i}/{len(posts)} posts processed")
            
            # Get current sentiment
            old_sentiment = post.sentiment_label
            old_score = post.sentiment_score
            
            # Combine title and content for analysis
            combined_text = f"{post.title or ''} {post.content}".strip()
            
            # Re-analyze sentiment using improved Gusto-specific logic
            detailed_sentiment = sentiment_analyzer.analyze_detailed_sentiment(combined_text)
            
            # Update post with new sentiment analysis
            post.sentiment_label = detailed_sentiment['sentiment_label']
            post.sentiment_score = detailed_sentiment['sentiment_score']
            post.confidence_score = detailed_sentiment['confidence']
            
            # Track changes
            if old_sentiment != post.sentiment_label:
                changed_sentiment_count += 1
                logger.info(f"🔄 Post {post.id}: {old_sentiment} → {post.sentiment_label} (score: {old_score:.3f} → {post.sentiment_score:.3f})")
            
            updated_count += 1
        
        # Commit all changes
        session.commit()
        
        logger.info(f"✅ Sentiment re-analysis completed!")
        logger.info(f"📊 Total posts updated: {updated_count}")
        logger.info(f"🔄 Posts with changed sentiment: {changed_sentiment_count}")
        logger.info(f"🎯 All sentiment analysis now focuses exclusively on Gusto-related sentiment")

if __name__ == "__main__":
    try:
        reanalyze_all_posts()
        print("\n🎉 Sentiment re-analysis completed successfully!")
        print("All posts now use Gusto-specific sentiment analysis.")
        print("Visit http://localhost:5000 to see the updated results!")
        
    except Exception as e:
        logger.error(f"❌ Error during sentiment re-analysis: {e}")
        sys.exit(1)