#!/usr/bin/env python3
"""
Enhanced Automated Data Refresh Script for Gusto Social Media Monitor
Runs every Monday to refresh dashboard data with comprehensive Reddit monitoring.
"""

import os
import sys
import sqlite3
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

try:
    from utils.sentiment_analyzer import SentimentAnalyzer
    SENTIMENT_AVAILABLE = True
except ImportError:
    SENTIMENT_AVAILABLE = False
    print("WARNING: sentiment_analyzer not available")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedRedditCollector:
    """Enhanced Reddit data collector with comprehensive Gusto monitoring."""
    
    def __init__(self, db_path="gusto_monitor.db"):
        self.db_path = db_path
        
        # Initialize sentiment analyzer if available
        self.sentiment_analyzer = SentimentAnalyzer() if SENTIMENT_AVAILABLE else None
        
        if not PRAW_AVAILABLE:
            logger.warning("⚠️ praw not available. Running in demo mode.")
            self.reddit = None
            return
        
        client_id = os.getenv('REDDIT_CLIENT_ID')
        client_secret = os.getenv('REDDIT_CLIENT_SECRET')
        user_agent = os.getenv('REDDIT_USER_AGENT', 'GustoSocialMonitor/1.0')
        
        if not client_id or not client_secret:
            logger.warning("⚠️ Reddit API credentials not found. Running in demo mode.")
            self.reddit = None
            return
        
        try:
            self.reddit = praw.Reddit(client_id=client_id, client_secret=client_secret, user_agent=user_agent)
            logger.info("✅ Reddit API connection established")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Reddit API: {e}")
            self.reddit = None
    
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
    
    def insert_posts_to_database(self, posts_data):
        """Insert new posts into the database."""
        if not posts_data:
            return 0
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        inserted_count = 0
        
        for post in posts_data:
            try:
                # Analyze sentiment if analyzer is available
                if self.sentiment_analyzer and 'text' in post:
                    sentiment_result = self.sentiment_analyzer.analyze_sentiment(post['text'])
                    post['sentiment_label'] = sentiment_result.get('label', 'neutral')
                    post['sentiment_score'] = sentiment_result.get('score', 0.0)
                else:
                    post['sentiment_label'] = 'neutral'
                    post['sentiment_score'] = 0.0
                
                cursor.execute("""
                    INSERT OR IGNORE INTO social_media_posts 
                    (platform, post_id, title, content, author, url, created_at, 
                     upvotes, comments_count, sentiment_label, sentiment_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    'reddit', post['post_id'], post['title'], post['text'],
                    post['author'], post['url'], post['created_at'], post['upvotes'],
                    post.get('comments_count', 0), post['sentiment_label'], post['sentiment_score']
                ))
                
                if cursor.rowcount > 0:
                    inserted_count += 1
                    
            except Exception as e:
                logger.warning(f"⚠️ Error inserting post {post['post_id']}: {e}")
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Inserted {inserted_count} new posts into database")
        return inserted_count
    
    def run_weekly_refresh(self, days_back=7, max_posts=100):
        """Run the weekly data refresh process."""
        logger.info("🚀 Starting weekly data refresh process...")
        
        # Collect posts
        posts = self.collect_gusto_posts(days_back, max_posts)
        
        if not posts:
            logger.info("ℹ️ No new posts found")
            return {'status': 'completed', 'posts_collected': 0, 'posts_inserted': 0}
        
        # Insert into database
        inserted = self.insert_posts_to_database(posts)
        
        # Show database stats
        self._show_database_stats()
        
        return {
            'status': 'completed',
            'posts_collected': len(posts),
            'posts_inserted': inserted
        }
    
    def _show_database_stats(self):
        """Show current database statistics."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM social_media_posts')
            total = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT strftime('%Y-%m', created_at) as month, COUNT(*) 
                FROM social_media_posts 
                GROUP BY strftime('%Y-%m', created_at) 
                ORDER BY month DESC LIMIT 6
            """)
            monthly_stats = cursor.fetchall()
            
            print(f"\n📊 DATABASE STATS:")
            print(f"Total posts: {total}")
            print("Recent months:")
            for month, count in monthly_stats:
                print(f"  {month}: {count} posts")
            
            conn.close()
        except Exception as e:
            logger.warning(f"⚠️ Could not show database stats: {e}")

def main():
    parser = argparse.ArgumentParser(description="Enhanced Gusto Social Media Monitor Data Refresh")
    parser.add_argument('--days-back', type=int, default=7, help='Days back to collect (default: 7)')
    parser.add_argument('--max-posts', type=int, default=100, help='Max posts to collect (default: 100)')
    parser.add_argument('--test-run', action='store_true', help='Test run with minimal data')
    parser.add_argument('--show-stats', action='store_true', help='Show database statistics only')
    
    args = parser.parse_args()
    
    if args.test_run:
        args.days_back = 1
        args.max_posts = 10
        logger.info("🧪 Running in test mode")
    
    print("✅ Enhanced Automated Data Refresh Script")
    print(f"📊 Features: 18+ subreddits, 10+ search terms")
    print(f"⚙️ Config: {args.days_back} days back, max {args.max_posts} posts")
    
    try:
        collector = EnhancedRedditCollector()
        
        if args.show_stats:
            collector._show_database_stats()
            return
        
        # Run the weekly refresh
        result = collector.run_weekly_refresh(args.days_back, args.max_posts)
        
        print(f"\n🎉 REFRESH COMPLETED!")
        print(f"Status: {result['status']}")
        print(f"Posts collected: {result['posts_collected']}")
        print(f"Posts inserted: {result['posts_inserted']}")
        
        if result['posts_collected'] == 0:
            print("💡 No new posts found. This is normal if:")
            print("  - Reddit API credentials are not set")
            print("  - Recent data has already been collected")
            print("  - There are no new Gusto mentions in monitored subreddits")
        
    except Exception as e:
        logger.error(f"❌ Error during data refresh: {e}")
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
