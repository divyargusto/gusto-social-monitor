#!/usr/bin/env python3
"""
G2 Data Collection Script for Gusto Social Monitor

⚠️  IMPORTANT LEGAL NOTICE:
This script is for educational and research purposes only.
Always check G2's Terms of Service before using in production.

Usage:
    python collect_g2_data.py --max-pages 2 --include-competitors
    python collect_g2_data.py --gusto-only --pages 3
"""

import argparse
import sys
import os
import logging
from datetime import datetime
import uuid

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.g2_scraper import G2Scraper
from utils.sentiment_analyzer import SentimentAnalyzer
from utils.theme_extractor import ThemeExtractor
from backend.database.database import get_session
from backend.database.models import SocialMediaPost, Theme, PostTheme

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/g2_collection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def parse_g2_date(date_str):
    """Parse G2 date string to datetime object."""
    try:
        # Handle various G2 date formats
        if not date_str:
            return datetime.now()
        
        # Common G2 date formats
        formats = [
            '%B %d, %Y',           # "July 23, 2025"
            '%b %d, %Y',           # "Jul 23, 2025"
            '%Y-%m-%d',            # "2025-07-23"
            '%m/%d/%Y',            # "07/23/2025"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
        
        # If all formats fail, return current time
        logger.warning(f"Could not parse date: {date_str}, using current time")
        return datetime.now()
        
    except Exception as e:
        logger.warning(f"Date parsing error: {e}, using current time")
        return datetime.now()

def collect_gusto_reviews(scraper, analyzer, theme_extractor, max_pages=2):
    """Collect and process Gusto reviews from G2."""
    logger.info(f"🎯 Starting Gusto review collection (max {max_pages} pages)...")
    
    results = {
        'reviews_found': 0,
        'reviews_processed': 0,
        'reviews_skipped': 0,
        'errors': []
    }
    
    try:
        # Scrape Gusto reviews
        reviews = scraper.scrape_gusto_reviews(max_pages=max_pages)
        results['reviews_found'] = len(reviews)
        
        if not reviews:
            logger.warning("❌ No Gusto reviews found")
            return results
        
        logger.info(f"✅ Found {len(reviews)} Gusto reviews")
        
        with get_session() as session:
            for i, review in enumerate(reviews, 1):
                try:
                    logger.info(f"📝 Processing review {i}/{len(reviews)}...")
                    
                    # Generate unique post_id
                    post_id = f"g2_gusto_{uuid.uuid4().hex[:12]}"
                    
                    # Check if review already exists (by content hash)
                    content_hash = hash(review['content'][:100])
                    existing = session.query(SocialMediaPost).filter(
                        SocialMediaPost.platform == 'g2',
                        SocialMediaPost.content.like(f"%{review['content'][:50]}%")
                    ).first()
                    
                    if existing:
                        logger.info(f"⏭️  Review {i} already exists, skipping...")
                        results['reviews_skipped'] += 1
                        continue
                    
                    # Analyze sentiment for Gusto-specific content
                    sentiment_result = analyzer.analyze_gusto_sentiment(review['content'])
                    
                    # Extract themes
                    themes = theme_extractor.extract_gusto_themes(review['content'])
                    
                    # Parse review date
                    review_date = parse_g2_date(review.get('date', ''))
                    
                    # Create post record
                    post = SocialMediaPost(
                        platform='g2',
                        post_id=post_id,
                        title=review.get('title', '').strip()[:500],  # Limit title length
                        content=review['content'],
                        author=review.get('reviewer', 'Anonymous'),
                        url=review.get('url', ''),
                        created_at=review_date,
                        sentiment_score=sentiment_result.get('compound', 0),
                        sentiment_label=sentiment_result.get('label', 'neutral'),
                        confidence_score=sentiment_result.get('confidence', 0),
                        upvotes=int(review.get('rating', 0)) if review.get('rating') else 0,
                        raw_data=review,
                        is_processed=True,
                        language='en'
                    )
                    
                    session.add(post)
                    session.flush()  # Get the post ID
                    
                    # Add themes
                    themes_added = 0
                    for theme_name, relevance in themes.items():
                        if relevance > 0.1:  # Only add relevant themes
                            # Find or create theme
                            theme = session.query(Theme).filter(Theme.name == theme_name).first()
                            if not theme:
                                theme = Theme(
                                    name=theme_name,
                                    category='g2_product',
                                    description=f"Theme extracted from G2 reviews"
                                )
                                session.add(theme)
                                session.flush()
                            
                            # Link post to theme
                            post_theme = PostTheme(
                                post_id=post.id,
                                theme_id=theme.id,
                                relevance_score=relevance,
                                confidence=0.8
                            )
                            session.add(post_theme)
                            themes_added += 1
                    
                    logger.info(f"✅ Processed review {i}: {themes_added} themes, sentiment: {sentiment_result.get('label', 'neutral')}")
                    results['reviews_processed'] += 1
                    
                except Exception as e:
                    error_msg = f"Error processing review {i}: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            # Commit all changes
            session.commit()
            logger.info(f"💾 Committed {results['reviews_processed']} Gusto reviews to database")
    
    except Exception as e:
        error_msg = f"Failed to collect Gusto reviews: {str(e)}"
        logger.error(error_msg)
        results['errors'].append(error_msg)
    
    return results

def main():
    """Main function to run G2 data collection."""
    parser = argparse.ArgumentParser(description='Collect G2 reviews for Gusto monitoring')
    parser.add_argument('--max-pages', type=int, default=2, help='Maximum pages to scrape per product')
    parser.add_argument('--include-competitors', action='store_true', help='Include competitor reviews')
    parser.add_argument('--gusto-only', action='store_true', help='Only collect Gusto reviews')
    parser.add_argument('--delay', type=int, default=3, help='Delay between requests (seconds)')
    
    args = parser.parse_args()
    
    # Print legal warning
    print("⚠️  LEGAL WARNING: This script scrapes G2.com for educational purposes.")
    print("   Please ensure compliance with G2's Terms of Service.")
    print("   Use responsibly with appropriate rate limiting.")
    print()
    
    # Initialize components
    logger.info("🚀 Starting G2 data collection...")
    scraper = G2Scraper(delay_range=(args.delay, args.delay + 2))
    analyzer = SentimentAnalyzer()
    theme_extractor = ThemeExtractor()
    
    # Collect Gusto reviews
    gusto_results = collect_gusto_reviews(scraper, analyzer, theme_extractor, args.max_pages)
    
    # Print summary
    print("\n" + "="*50)
    print("📊 G2 COLLECTION SUMMARY")
    print("="*50)
    print(f"✅ Gusto reviews processed: {gusto_results['reviews_processed']}")
    print(f"❌ Total errors: {len(gusto_results['errors'])}")
    print("="*50)
    
    if gusto_results['reviews_processed'] > 0:
        print("🎉 G2 data collection completed successfully!")
        print(f"📊 Check your dashboard at http://localhost:5000 to view the new data")
    else:
        print("⚠️  No new reviews were processed")
    
    logger.info(f"G2 collection completed: {gusto_results}")

if __name__ == '__main__':
    main()
