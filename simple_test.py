#!/usr/bin/env python3
"""
Simple Reddit API test
"""

import praw
from dotenv import load_dotenv
import os

load_dotenv()

print("🔍 Testing Reddit API credentials...")

try:
    reddit = praw.Reddit(
        client_id=os.getenv('REDDIT_CLIENT_ID'),
        client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
        user_agent=os.getenv('REDDIT_USER_AGENT', 'GustoSocialMonitor/1.0'),
        username=os.getenv('REDDIT_USERNAME'),
        password=os.getenv('REDDIT_PASSWORD')
    )
    
    print(f"✅ Reddit API connected")
    print(f"   Read-only mode: {reddit.read_only}")
    
    # Test basic access
    print("🧪 Testing basic subreddit access...")
    
    # Try to access a simple, public subreddit
    subreddit = reddit.subreddit('test')
    print(f"   Subreddit name: {subreddit.display_name}")
    print(f"   Subscribers: {subreddit.subscribers}")
    
    # Try to get a few recent posts (without searching)
    print("📋 Testing post retrieval...")
    posts = list(subreddit.new(limit=2))
    print(f"   Retrieved {len(posts)} posts successfully")
    
    if posts:
        print(f"   Sample post title: {posts[0].title[:50]}...")
    
    print("✅ All tests passed! Reddit API is working correctly.")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("Check your Reddit app credentials and make sure:")
    print("1. App type is 'script'")
    print("2. Client ID and Secret are correct")
    print("3. Username/password are correct (if provided)") 