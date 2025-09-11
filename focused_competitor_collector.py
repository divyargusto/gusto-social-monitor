#!/usr/bin/env python3
"""
Focused Competitor Reddit Collector
Collects competitor data from the SAME subreddits as Gusto data: r/smallbusiness and r/payroll
This ensures fair comparison within the same communities.
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

class FocusedCompetitorCollector:
    """Collects competitor data from same subreddits as Gusto data."""
    
    def __init__(self):
        self.reddit_collector = RedditCollector()
        self.sentiment_analyzer = SentimentAnalyzer()
        
        # Focus on same subreddits as Gusto data
        self.target_subreddits = ['smallbusiness', 'Payroll']
        
        # Competitor search terms
        self.competitors = {
            'adp': {
                'terms': ['ADP payroll', 'ADP', 'Automatic Data Processing', 'ADP workforce'],
                'exclude': ['gusto']  # Don't include posts that also mention Gusto
            },
            'paychex': {
                'terms': ['Paychex', 'Paychex Flex', 'Paychex payroll'],
                'exclude': ['gusto']
            },
            'quickbooks': {
                'terms': ['QuickBooks payroll', 'QB payroll', 'Intuit payroll', 'QuickBooks Payroll'],
                'exclude': ['gusto']
            },
            'rippling': {
                'terms': ['Rippling', 'Rippling HR', 'Rippling payroll'],
                'exclude': ['gusto']
            }
        }
    
    async def collect_competitor_in_subreddit(self, competitor: str, subreddit: str, days_back: int = 30, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Collect competitor posts from a specific subreddit.
        
        Args:
            competitor: Competitor name (e.g., 'adp')
            subreddit: Subreddit name (e.g., 'smallbusiness')
            days_back: Number of days to look back
            limit: Max posts per search term
            
        Returns:
            List of posts mentioning the competitor
        """
        if competitor not in self.competitors:
            logger.error(f"Unknown competitor: {competitor}")
            return []
        
        competitor_config = self.competitors[competitor]
        competitor_terms = competitor_config['terms']
        exclude_terms = competitor_config.get('exclude', [])
        
        logger.info(f"🔍 Searching r/{subreddit} for {competitor.upper()} posts...")
        
        all_posts = []
        
        for term in competitor_terms:
            try:
                logger.info(f"   Searching for: '{term}'")
                
                # Use the existing Reddit collector's subreddit search
                posts = await self.reddit_collector.search_subreddit(
                    subreddit_name=subreddit,
                    keywords=[term],
                    days_back=days_back,
                    limit=limit
                )
                
                # Filter out posts that mention excluded terms
                filtered_posts = []
                for post in posts:
                    post_text = f"{post.get('title', '')} {post.get('content', '')}".lower()
                    
                    # Skip if post mentions any excluded terms
                    if any(exclude_term.lower() in post_text for exclude_term in exclude_terms):
                        logger.debug(f"Excluding post mentioning {exclude_terms}: {post.get('title', '')[:50]}")
                        continue
                    
                    # Add metadata
                    post['competitor'] = competitor
                    post['search_term'] = term
                    post['source_subreddit'] = subreddit
                    filtered_posts.append(post)
                
                all_posts.extend(filtered_posts)
                logger.info(f"   Found {len(filtered_posts)} relevant posts for '{term}'")
                
                # Rate limiting between searches
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error searching for '{term}' in r/{subreddit}: {e}")
                continue
        
        # Remove duplicates based on post ID
        unique_posts = {}
        for post in all_posts:
            post_id = post.get('id')
            if post_id and post_id not in unique_posts:
                unique_posts[post_id] = post
        
        final_posts = list(unique_posts.values())
        logger.info(f"✅ Collected {len(final_posts)} unique {competitor.upper()} posts from r/{subreddit}")
        
        return final_posts
    
    async def collect_competitor_all_subreddits(self, competitor: str, days_back: int = 30) -> List[Dict[str, Any]]:
        """
        Collect competitor posts from all target subreddits.
        
        Args:
            competitor: Competitor name
            days_back: Number of days to look back
            
        Returns:
            Combined list of posts from all subreddits
        """
        logger.info(f"🎯 Collecting {competitor.upper()} data from Gusto's subreddits...")
        
        all_posts = []
        
        for subreddit in self.target_subreddits:
            try:
                subreddit_posts = await self.collect_competitor_in_subreddit(
                    competitor, subreddit, days_back
                )
                all_posts.extend(subreddit_posts)
                
                # Delay between subreddits
                await asyncio.sleep(3)
                
            except Exception as e:
                logger.error(f"Error collecting from r/{subreddit}: {e}")
                continue
        
        logger.info(f"🏆 Total {competitor.upper()} posts collected: {len(all_posts)}")
        return all_posts
    
    def save_to_database(self, competitor_posts: List[Dict[str, Any]], competitor: str):
        """
        Save competitor posts to database with CompetitorMention records.
        
        Args:
            competitor_posts: List of competitor posts
            competitor: Competitor name
        """
        try:
            init_database()
            
            with get_session() as session:
                saved_count = 0
                
                for post_data in competitor_posts:
                    try:
                        # Check if post already exists
                        existing_post = session.query(SocialMediaPost).filter_by(
                            external_id=post_data.get('id'),
                            platform='reddit'
                        ).first()
                        
                        if existing_post:
                            logger.debug(f"Post {post_data.get('id')} already exists, skipping")
                            continue
                        
                        # Create new post
                        post = SocialMediaPost(
                            external_id=post_data.get('id'),
                            platform='reddit',
                            title=post_data.get('title', ''),
                            content=post_data.get('content', ''),
                            author=post_data.get('author'),
                            url=post_data.get('url'),
                            created_at=datetime.fromisoformat(post_data.get('created_at')) if post_data.get('created_at') else datetime.now(),
                            collected_at=datetime.now(),
                            raw_data=post_data,
                            upvotes=post_data.get('upvotes', 0),
                            comments_count=post_data.get('comments_count', 0),
                            # We'll analyze sentiment later
                            sentiment_label='neutral',
                            sentiment_score=0.0,
                            confidence_score=0.8
                        )
                        
                        session.add(post)
                        session.flush()  # Get the post ID
                        
                        # Add competitor mention
                        competitor_mention = CompetitorMention(
                            post_id=post.id,
                            competitor_name=competitor,
                            mention_context=post_data.get('content', '')[:500],  # First 500 chars
                            sentiment_towards_competitor=0.0  # Will be analyzed later
                        )
                        
                        session.add(competitor_mention)
                        saved_count += 1
                        
                    except Exception as e:
                        logger.error(f"Error saving post {post_data.get('id')}: {e}")
                        continue
                
                session.commit()
                logger.info(f"💾 Saved {saved_count} new {competitor.upper()} posts to database")
                
        except Exception as e:
            logger.error(f"Error saving to database: {e}")
    
    def save_to_file(self, competitor_posts: List[Dict[str, Any]], competitor: str):
        """Save competitor posts to JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"focused_{competitor}_data_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(competitor_posts, f, indent=2, default=str)
            logger.info(f"📁 Saved {len(competitor_posts)} posts to {filename}")
        except Exception as e:
            logger.error(f"Error saving to file: {e}")

async def main():
    """Main function for focused competitor collection."""
    print("🎯 Focused Competitor Data Collector")
    print("=" * 50)
    print(f"📍 Target subreddits: r/smallbusiness, r/Payroll")
    print(f"🎯 Same subreddits as Gusto data for fair comparison")
    print()
    
    collector = FocusedCompetitorCollector()
    
    # Choose competitor
    competitors = list(collector.competitors.keys())
    print("Available competitors:")
    for i, comp in enumerate(competitors, 1):
        print(f"  {i}. {comp.upper()}")
    
    while True:
        try:
            choice = input(f"\nSelect competitor (1-{len(competitors)}) or 'all': ").strip()
            if choice.lower() == 'all':
                selected_competitors = competitors
                break
            else:
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(competitors):
                    selected_competitors = [competitors[choice_idx]]
                    break
                else:
                    print("Invalid choice, please try again.")
        except (ValueError, KeyboardInterrupt):
            print("Invalid input, please try again.")
    
    days = int(input("Days back to search (default 30): ") or "30")
    save_db = input("Save to database? (y/N): ").lower().strip() == 'y'
    
    print(f"\n🚀 Starting focused collection...")
    
    for competitor in selected_competitors:
        print(f"\n📊 Collecting {competitor.upper()} data...")
        
        competitor_posts = await collector.collect_competitor_all_subreddits(
            competitor, days
        )
        
        if competitor_posts:
            # Always save to file
            collector.save_to_file(competitor_posts, competitor)
            
            # Optionally save to database
            if save_db:
                collector.save_to_database(competitor_posts, competitor)
            
            print(f"✅ {competitor.upper()}: {len(competitor_posts)} posts collected")
        else:
            print(f"❌ {competitor.upper()}: No posts found")
    
    print(f"\n🎉 Focused competitor collection complete!")
    print(f"💡 Now you can run fair comparisons in the same subreddits!")

if __name__ == "__main__":
    asyncio.run(main())
