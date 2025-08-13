#!/usr/bin/env python3
"""
Re-extract themes for all existing posts using improved Gusto-specific theme analysis.
This script updates theme associations to focus only on what's being said about Gusto.
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.database.database import get_session
from backend.database.models import SocialMediaPost, Theme, PostTheme
from utils.theme_extractor import ThemeExtractor
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_post_themes():
    """Re-extract themes for all posts using improved Gusto-specific logic."""
    
    logger.info("🔄 Starting theme re-extraction for all posts...")
    
    # Initialize theme extractor
    theme_extractor = ThemeExtractor()
    
    with get_session() as session:
        # Get all Reddit posts
        posts = session.query(SocialMediaPost).filter(
            SocialMediaPost.platform == 'reddit'
        ).all()
        
        logger.info(f"📊 Found {len(posts)} Reddit posts to re-analyze for themes")
        
        # Get or create theme records
        theme_records = {}
        for theme_name, theme_data in theme_extractor.predefined_themes.items():
            theme = session.query(Theme).filter(Theme.name == theme_name).first()
            if not theme:
                theme = Theme(
                    name=theme_name,
                    description=theme_data['description'],
                    category='predefined'
                )
                session.add(theme)
                session.flush()
            theme_records[theme_name] = theme
        
        session.commit()
        
        updated_count = 0
        changed_themes_count = 0
        
        for i, post in enumerate(posts, 1):
            if i % 10 == 0:
                logger.info(f"📈 Progress: {i}/{len(posts)} posts processed")
            
            # Get current themes for this post
            current_post_themes = session.query(PostTheme).filter(
                PostTheme.post_id == post.id
            ).all()
            
            # Combine title and content for analysis
            combined_text = f"{post.title or ''} {post.content}".strip()
            
            # Extract themes using improved Gusto-specific logic
            theme_scores = theme_extractor.classify_predefined_themes(combined_text)
            
            # Check if themes changed significantly
            old_themes = {pt.theme.name: pt.relevance_score for pt in current_post_themes}
            significant_changes = False
            
            # Remove old theme associations
            for post_theme in current_post_themes:
                session.delete(post_theme)
            
            # Add new theme associations (only for scores > 0)
            new_themes = {}
            for theme_name, score in theme_scores.items():
                if score > 0:  # Only add themes with positive relevance
                    theme = theme_records[theme_name]
                    post_theme = PostTheme(
                        post_id=post.id,
                        theme_id=theme.id,
                        relevance_score=score
                    )
                    session.add(post_theme)
                    new_themes[theme_name] = score
            
            # Check for significant changes
            if set(old_themes.keys()) != set(new_themes.keys()):
                significant_changes = True
                changed_themes_count += 1
                
                logger.info(f"🔄 Post {post.id} theme changes:")
                logger.info(f"   Old themes: {list(old_themes.keys())}")
                logger.info(f"   New themes: {list(new_themes.keys())}")
                
                # Show Gusto segments for verification
                segments = theme_extractor.extract_gusto_segments(combined_text)
                logger.info(f"   Gusto segments: {segments[:2]}...")  # Show first 2 segments
            
            updated_count += 1
        
        # Commit all changes
        session.commit()
        
        logger.info(f"✅ Theme re-extraction completed!")
        logger.info(f"📊 Total posts updated: {updated_count}")
        logger.info(f"🔄 Posts with changed themes: {changed_themes_count}")
        logger.info(f"🎯 All theme analysis now focuses exclusively on Gusto-related content")

if __name__ == "__main__":
    try:
        update_post_themes()
        print("\n🎉 Theme re-extraction completed successfully!")
        print("All posts now use Gusto-specific theme analysis.")
        print("Visit http://localhost:5000 to see the updated theme results!")
        
    except Exception as e:
        logger.error(f"❌ Error during theme re-extraction: {e}")
        sys.exit(1)