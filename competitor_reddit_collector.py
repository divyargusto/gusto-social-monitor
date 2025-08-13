#!/usr/bin/env python3
"""
Competitor Reddit Data Collector
Collects Reddit posts and comments specifically mentioning competitors for competitive analysis.
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json

from collectors.reddit_collector import RedditCollector
from backend.database.database import init_database, get_session
from backend.database.models import SocialMediaPost, CompetitorMention
from utils.sentiment_analyzer import SentimentAnalyzer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CompetitorRedditCollector:
    """Collects Reddit data specifically for competitor analysis."""
    
    def __init__(self):
        self.reddit_collector = RedditCollector()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.competitors = {
            'adp': ['adp', 'automatic data processing', 'adp payroll', 'adp workforce'],
            'paychex': ['paychex', 'paychex flex', 'paychex payroll'],
            'quickbooks': ['quickbooks payroll', 'qb payroll', 'intuit payroll', 'quickbooks'],
            'bamboohr': ['bamboohr', 'bamboo hr'],
            'rippling': ['rippling', 'rippling hr', 'rippling payroll'],
            'workday': ['workday', 'workday hcm', 'workday payroll'],
            'deel': ['deel', 'deel.com', 'deel payroll'],
            'justworks': ['justworks', 'just works']
        }
    
    async def collect_competitor_data(self, competitor: str, days_back: int = 30) -> List[Dict[str, Any]]:
        """
        Collect Reddit posts mentioning a specific competitor.
        
        Args:
            competitor: Competitor name (e.g., 'adp', 'paychex')
            days_back: Number of days to look back
            
        Returns:
            List of posts mentioning the competitor
        """
        if competitor not in self.competitors:
            logger.error(f"Unknown competitor: {competitor}")
            return []
        
        competitor_terms = self.competitors[competitor]
        logger.info(f"Collecting Reddit data for {competitor} with terms: {competitor_terms}")
        
        all_posts = []
        
        # Collect posts for each competitor term
        for term in competitor_terms:
            try:
                logger.info(f"Searching for term: {term}")
                posts = await self.reddit_collector.collect_data([term], days_back)
                
                # Add competitor metadata to each post
                for post in posts:
                    post['competitor'] = competitor
                    post['search_term'] = term
                    all_posts.append(post)
                
                # Rate limiting
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error collecting data for term '{term}': {e}")
                continue
        
        logger.info(f"Collected {len(all_posts)} posts for {competitor}")
        return all_posts
    
    async def collect_all_competitors(self, days_back: int = 30) -> Dict[str, List[Dict[str, Any]]]:
        """
        Collect Reddit data for all competitors.
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            Dictionary with competitor names as keys and their posts as values
        """
        all_competitor_data = {}
        
        for competitor in self.competitors.keys():
            logger.info(f"Starting collection for {competitor}")
            competitor_posts = await self.collect_competitor_data(competitor, days_back)
            all_competitor_data[competitor] = competitor_posts
            
            # Longer delay between competitors to avoid rate limiting
            await asyncio.sleep(5)
        
        return all_competitor_data
    
    def save_competitor_data_to_db(self, competitor_data: Dict[str, List[Dict[str, Any]]]):
        """
        Save competitor Reddit data to the database.
        
        Args:
            competitor_data: Dictionary of competitor data
        """
        try:
            init_database()
            
            with get_session() as session:
                total_saved = 0
                
                for competitor, posts in competitor_data.items():
                    logger.info(f"Saving {len(posts)} posts for {competitor}")
                    
                    for post_data in posts:
                        try:
                            # Check if post already exists
                            existing_post = session.query(SocialMediaPost).filter_by(
                                external_id=post_data.get('id'),
                                platform='reddit'
                            ).first()
                            
                            if existing_post:
                                continue
                            
                            # Create new post
                            post = SocialMediaPost(
                                external_id=post_data.get('id'),
                                platform='reddit',
                                title=post_data.get('title', ''),
                                content=post_data.get('text', ''),
                                author=post_data.get('author'),
                                url=post_data.get('url'),
                                created_at=datetime.fromisoformat(post_data.get('created_at')) if post_data.get('created_at') else datetime.now(),
                                collected_at=datetime.now(),
                                raw_data=post_data,
                                upvotes=post_data.get('score', 0),
                                comments_count=post_data.get('num_comments', 0),
                                sentiment_label=post_data.get('sentiment'),
                                sentiment_score=post_data.get('sentiment_score', 0.0),
                                confidence_score=0.8  # Default confidence
                            )
                            
                            session.add(post)
                            session.flush()  # Get the post ID
                            
                            # Add competitor mention
                            competitor_mention = CompetitorMention(
                                post_id=post.id,
                                competitor_name=competitor,
                                mention_context=post_data.get('text', '')[:500],  # First 500 chars
                                sentiment_towards_competitor=post_data.get('sentiment_score', 0.0)
                            )
                            
                            session.add(competitor_mention)
                            total_saved += 1
                            
                        except Exception as e:
                            logger.error(f"Error saving post {post_data.get('id')}: {e}")
                            continue
                
                session.commit()
                logger.info(f"Successfully saved {total_saved} new competitor posts to database")
                
        except Exception as e:
            logger.error(f"Error saving competitor data to database: {e}")
    
    def save_competitor_data_to_file(self, competitor_data: Dict[str, List[Dict[str, Any]]], filename: str = None):
        """
        Save competitor data to JSON file for backup.
        
        Args:
            competitor_data: Dictionary of competitor data
            filename: Optional filename, defaults to timestamped file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"competitor_reddit_data_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(competitor_data, f, indent=2, default=str)
            logger.info(f"Competitor data saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving competitor data to file: {e}")

async def main():
    """Main function to run competitor data collection."""
    collector = CompetitorRedditCollector()
    
    # Collect data for specific competitors or all
    import argparse
    parser = argparse.ArgumentParser(description="Collect Reddit data for competitors")
    parser.add_argument("--competitor", help="Specific competitor to collect (e.g., 'adp', 'paychex')")
    parser.add_argument("--days", type=int, default=30, help="Days back to search (default: 30)")
    parser.add_argument("--save-db", action="store_true", help="Save to database")
    parser.add_argument("--save-file", action="store_true", help="Save to JSON file")
    
    args = parser.parse_args()
    
    if args.competitor:
        if args.competitor not in collector.competitors:
            logger.error(f"Unknown competitor: {args.competitor}")
            logger.info(f"Available competitors: {list(collector.competitors.keys())}")
            return
        
        logger.info(f"Collecting data for {args.competitor}")
        competitor_data = {args.competitor: await collector.collect_competitor_data(args.competitor, args.days)}
    else:
        logger.info("Collecting data for all competitors")
        competitor_data = await collector.collect_all_competitors(args.days)
    
    # Save data
    if args.save_db:
        collector.save_competitor_data_to_db(competitor_data)
    
    if args.save_file:
        collector.save_competitor_data_to_file(competitor_data)
    
    # Print summary
    total_posts = sum(len(posts) for posts in competitor_data.values())
    logger.info(f"Collection complete. Total posts collected: {total_posts}")
    
    for competitor, posts in competitor_data.items():
        logger.info(f"{competitor}: {len(posts)} posts")

if __name__ == "__main__":
    asyncio.run(main())
