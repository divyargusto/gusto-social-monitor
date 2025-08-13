#!/usr/bin/env python3
"""
Update sentiment analysis for posts that mention both Gusto and competitors.
This specifically addresses cases like the Deel post where Gusto sentiment was contaminated.
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

def update_mixed_sentiment_posts():
    """Update sentiment for posts that mention both Gusto and competitors."""
    
    logger.info("🔄 Updating sentiment for posts with mixed platform mentions...")
    
    # Initialize sentiment analyzer
    sentiment_analyzer = SentimentAnalyzer()
    
    # Competitor names to look for
    competitors = ['adp', 'paychex', 'quickbooks', 'bamboohr', 'rippling', 'workday', 'deel', 'justworks']
    
    # Get posts that mention both Gusto and competitors
    with get_session() as session:
        posts = session.query(SocialMediaPost).filter(
            SocialMediaPost.platform == 'reddit'
        ).all()
        
        mixed_posts = []
        for post in posts:
            combined_text = f"{post.title or ''} {post.content}".lower()
            if 'gusto' in combined_text and any(comp in combined_text for comp in competitors):
                mixed_posts.append(post)
        
        logger.info(f"📊 Found {len(mixed_posts)} posts mentioning both Gusto and competitors")
        
        updated_count = 0
        changed_sentiment_count = 0
        
        for i, post in enumerate(mixed_posts, 1):
            logger.info(f"📈 Processing post {i}/{len(mixed_posts)}: '{post.title[:50]}...'")
            
            # Get current sentiment
            old_sentiment = post.sentiment_label
            old_score = post.sentiment_score
            
            # Combine title and content for analysis
            combined_text = f"{post.title or ''} {post.content}".strip()
            
            # Re-analyze sentiment using improved logic
            detailed_sentiment = sentiment_analyzer.analyze_detailed_sentiment(combined_text)
            
            # Update post with new sentiment analysis
            post.sentiment_label = detailed_sentiment['sentiment_label']
            post.sentiment_score = detailed_sentiment['sentiment_score']
            post.confidence_score = detailed_sentiment['confidence']
            
            # Track changes
            if old_sentiment != post.sentiment_label:
                changed_sentiment_count += 1
                logger.info(f"🔄 Changed: {old_sentiment} → {post.sentiment_label} (score: {old_score:.3f} → {post.sentiment_score:.3f})")
                
                # Show the Gusto segments for verification
                segments = sentiment_analyzer.extract_gusto_segments(combined_text)
                logger.info(f"   Gusto segments: {segments}")
            
            updated_count += 1
        
        # Commit all changes
        session.commit()
        
        logger.info(f"✅ Mixed sentiment update completed!")
        logger.info(f"📊 Total mixed posts updated: {updated_count}")
        logger.info(f"🔄 Posts with changed sentiment: {changed_sentiment_count}")

if __name__ == "__main__":
    try:
        update_mixed_sentiment_posts()
        print("\n🎉 Mixed sentiment update completed successfully!")
        print("Posts with both Gusto and competitor mentions now have accurate Gusto-specific sentiment.")
        print("Visit http://localhost:5000 to see the updated results!")
        
    except Exception as e:
        logger.error(f"❌ Error during mixed sentiment update: {e}")
        sys.exit(1)