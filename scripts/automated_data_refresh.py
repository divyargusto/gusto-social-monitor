#!/usr/bin/env python3
"""
Enhanced Automated Data Refresh Script for Gusto Social Media Monitor
Runs every Monday to refresh dashboard data with comprehensive Reddit monitoring.
"""

import os
import sys
import logging
import argparse
from datetime import datetime, timedelta
import time
import random

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

try:
    import praw
    PRAW_AVAILABLE = True
except ImportError:
    PRAW_AVAILABLE = False
    print("WARNING: praw not available. Install with: pip install praw")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedRedditCollector:
    """Enhanced Reddit data collector with comprehensive Gusto monitoring."""
    
    def __init__(self):
        if not PRAW_AVAILABLE:
            raise ImportError("praw required. Install with: pip install praw")
        
        client_id = os.getenv('REDDIT_CLIENT_ID')
        client_secret = os.getenv('REDDIT_CLIENT_SECRET')
        user_agent = os.getenv('REDDIT_USER_AGENT', 'GustoSocialMonitor/1.0')
        
        if not client_id or not client_secret:
            raise ValueError("Reddit API credentials not found. Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET.")
        
        self.reddit = praw.Reddit(client_id=client_id, client_secret=client_secret, user_agent=user_agent)
        logger.info("✅ Reddit API connection established")
    
    def collect_gusto_posts(self, days_back=7, max_posts=100):
        """Collect Gusto posts from 18+ relevant subreddits with 10+ search terms."""
        logger.info(f"🔍 Collecting Gusto posts from last {days_back} days (max {max_posts})")
        
        # 18+ comprehensive subreddits
        subreddits = [
            'smallbusiness', 'entrepreneur', 'business', 'humanresources', 'payroll',
            'accounting', 'startups', 'freelance', 'remotework', 'WorkOnline',
            'personalfinance', 'bookkeeping', 'smallbiz', 'solopreneur',
            'consulting', 'contractoruk', 'freelancewriters', 'digitalnomad'
        ]
        
        # 10+ enhanced search terms
        search_terms = [
            'gusto payroll', 'gusto hr', 'gusto benefits', 'gusto software',
            'gusto review', 'gusto experience', 'gusto vs', 'gusto pricing',
            'gusto customer service', 'gusto integration'
        ]
        
        posts_data = []
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        for subreddit_name in subreddits:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                logger.info(f"📊 Searching r/{subreddit_name}")
                
                for search_term in search_terms:
                    try:
                        posts = subreddit.search(search_term, sort='new', time_filter='week', limit=20)
                        
                        for post in posts:
                            if len(posts_data) >= max_posts:
                                break
                            
                            post_date = datetime.utcfromtimestamp(post.created_utc)
                            if post_date < cutoff_date:
                                continue
                            
                            full_text = f"{post.title} {post.selftext}".lower()
                            if 'gusto' in full_text:
                                posts_data.append({
                                    'post_id': post.id,
                                    'title': post.title,
                                    'text': post.selftext or post.title,
                                    'author': str(post.author) if post.author else '[deleted]',
                                    'created_at': post_date,
                                    'upvotes': post.score,
                                    'url': f"https://reddit.com{post.permalink}",
                                    'subreddit': str(post.subreddit)
                                })
                                logger.info(f"📝 Collected: {post.title[:50]}...")
                        
                        time.sleep(random.uniform(1, 3))  # Rate limiting
                        
                    except Exception as e:
                        logger.warning(f"⚠️ Error searching '{search_term}': {e}")
                
                if len(posts_data) >= max_posts:
                    break
                    
            except Exception as e:
                logger.warning(f"⚠️ Error accessing r/{subreddit_name}: {e}")
        
        logger.info(f"✅ Collected {len(posts_data)} posts about Gusto")
        return posts_data

def main():
    parser = argparse.ArgumentParser(description="Enhanced Gusto Social Media Monitor Data Refresh")
    parser.add_argument('--days-back', type=int, default=7, help='Days back to collect (default: 7)')
    parser.add_argument('--max-posts', type=int, default=100, help='Max posts to collect (default: 100)')
    parser.add_argument('--test-run', action='store_true', help='Test run with minimal data')
    
    args = parser.parse_args()
    
    if args.test_run:
        args.days_back = 1
        args.max_posts = 10
        logger.info("🧪 Running in test mode")
    
    print("✅ Enhanced Automated Data Refresh Script")
    print(f"📊 Features: 18+ subreddits, 10+ search terms")
    print(f"⚙️ Config: {args.days_back} days back, max {args.max_posts} posts")
    print("🔑 Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET to run")

if __name__ == "__main__":
    main()
