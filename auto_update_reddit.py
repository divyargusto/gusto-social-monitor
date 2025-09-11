#!/usr/bin/env python3
"""
Automated Reddit Data Collection Script for Gusto Social Media Monitor
Run this script on a schedule (cron job, GitHub Actions, etc.) to keep data fresh
"""

import sqlite3
import praw
import os
import logging
from datetime import datetime, timedelta
from utils.sentiment_analyzer import SentimentAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RedditDataUpdater:
    def __init__(self, db_path="gusto_monitor.db"):
        self.db_path = db_path
        self.sentiment_analyzer = SentimentAnalyzer()
        
        # Reddit API setup (you'll need to add your credentials)
        self.reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID", "your_client_id"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET", "your_client_secret"),
            user_agent=os.getenv("REDDIT_USER_AGENT", "Gusto Social Monitor v1.0")
        )
    
    def collect_new_posts(self, days_back=7):
        """Collect new Reddit posts mentioning Gusto from the last N days"""
        
        # Search terms for Gusto
        search_terms = [
            "Gusto payroll",
            "Gusto HR", 
            "Gusto software",
            "site:reddit.com Gusto payroll",
            "site:reddit.com Gusto vs"
        ]
        
        subreddits = [
            "smallbusiness",
            "entrepreneur", 
            "startups",
            "accounting",
            "payroll",
            "humanresources"
        ]
        
        new_posts = []
        
        for subreddit_name in subreddits:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                
                # Search for Gusto mentions
                for submission in subreddit.search("Gusto", time_filter="week", limit=50):
                    post_age = datetime.utcnow() - datetime.utcfromtimestamp(submission.created_utc)
                    
                    if post_age.days <= days_back:
                        # Analyze sentiment
                        combined_text = f"{submission.title} {submission.selftext}"
                        sentiment_label = self.sentiment_analyzer.analyze_sentiment(combined_text)
                        sentiment_score = self.sentiment_analyzer.get_sentiment_score(combined_text)
                        
                        post_data = {
                            'platform': 'reddit',
                            'post_id': submission.id,
                            'title': submission.title,
                            'content': submission.selftext,
                            'author': str(submission.author) if submission.author else 'Unknown',
                            'url': f"https://reddit.com{submission.permalink}",
                            'created_at': datetime.utcfromtimestamp(submission.created_utc),
                            'upvotes': submission.score,
                            'comments_count': submission.num_comments,
                            'sentiment_label': sentiment_label,
                            'sentiment_score': sentiment_score
                        }
                        new_posts.append(post_data)
                        
            except Exception as e:
                logger.error(f"Error collecting from {subreddit_name}: {e}")
        
        logger.info(f"Collected {len(new_posts)} new posts")
        return new_posts
    
    def update_database(self, new_posts):
        """Insert new posts into the database"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS social_media_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                post_id TEXT UNIQUE NOT NULL,
                title TEXT,
                content TEXT,
                author TEXT,
                url TEXT,
                created_at DATETIME,
                upvotes INTEGER DEFAULT 0,
                comments_count INTEGER DEFAULT 0,
                sentiment_label TEXT,
                sentiment_score REAL
            )
        """)
        
        inserted_count = 0
        for post in new_posts:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO social_media_posts 
                    (platform, post_id, title, content, author, url, created_at, 
                     upvotes, comments_count, sentiment_label, sentiment_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    post['platform'], post['post_id'], post['title'], post['content'],
                    post['author'], post['url'], post['created_at'], post['upvotes'],
                    post['comments_count'], post['sentiment_label'], post['sentiment_score']
                ))
                
                if cursor.rowcount > 0:
                    inserted_count += 1
                    
            except Exception as e:
                logger.error(f"Error inserting post {post['post_id']}: {e}")
        
        conn.commit()
        conn.close()
        
        logger.info(f"Inserted {inserted_count} new posts into database")
        return inserted_count
    
    def run_update(self):
        """Main update process"""
        logger.info("Starting Reddit data update...")
        
        try:
            # Collect new posts
            new_posts = self.collect_new_posts(days_back=7)
            
            # Update database
            if new_posts:
                inserted = self.update_database(new_posts)
                logger.info(f"Update complete: {inserted} new posts added")
            else:
                logger.info("No new posts found")
                
        except Exception as e:
            logger.error(f"Update failed: {e}")
            raise

if __name__ == "__main__":
    # Set up database path
    db_path = os.path.join(os.path.dirname(__file__), "gusto_monitor.db")
    
    # Run the update
    updater = RedditDataUpdater(db_path)
    updater.run_update()
