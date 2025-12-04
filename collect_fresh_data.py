#!/usr/bin/env python3
"""
Fresh Reddit data collection script with direct .env loading
"""

import os
import praw
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Reddit
reddit = praw.Reddit(
    client_id=os.getenv('REDDIT_CLIENT_ID'),
    client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
    user_agent=os.getenv('REDDIT_USER_AGENT')
)

print("🚀 Starting Fresh Gusto Data Collection")
print(f"✅ Reddit API: Connected ({reddit.read_only=})")

# Subreddits to search
subreddits = [
    'smallbusiness', 'Entrepreneurship', 'Payroll',
    'entrepreneur', 'business', 'humanresources',
    'accounting', 'startups', 'freelance'
]

# Keywords to search
keywords = ['gusto payroll', 'gusto hr', 'gusto', 'gusto vs', 'gusto review']

# Collection parameters
days_back = 90
cutoff_date = datetime.utcnow() - timedelta(days=days_back)

print(f"📅 Collecting from last {days_back} days")
print(f"📊 Searching {len(subreddits)} subreddits")
print(f"🔍 Using {len(keywords)} keywords\n")

all_posts = []

for sub_name in subreddits:
    print(f"🔍 Searching r/{sub_name}...")
    try:
        subreddit = reddit.subreddit(sub_name)
        
        for keyword in keywords:
            try:
                # Search with 'all' time filter to get more results
                results = subreddit.search(keyword, sort='new', time_filter='all', limit=50)
                
                for post in results:
                    post_date = datetime.utcfromtimestamp(post.created_utc)
                    
                    # Only collect posts within our date range
                    if post_date < cutoff_date:
                        continue
                    
                    # Check if "gusto" is actually mentioned (case insensitive)
                    full_text = f"{post.title} {post.selftext}".lower()
                    if 'gusto' not in full_text:
                        continue
                    
                    post_data = {
                        'id': post.id,
                        'platform': 'reddit',
                        'post_id': post.id,
                        'title': post.title,
                        'text': post.selftext or post.title,
                        'content': post.selftext or post.title,
                        'author': str(post.author) if post.author else '[deleted]',
                        'url': f"https://reddit.com{post.permalink}",
                        'permalink': f"https://reddit.com{post.permalink}",
                        'created_at': post_date.isoformat(),
                        'subreddit': str(post.subreddit),
                        'upvotes': post.score,
                        'score': post.score,
                        'comments_count': post.num_comments,
                        'upvote_ratio': post.upvote_ratio,
                        'raw_data': {
                            'reddit_id': post.id,
                            'subreddit': str(post.subreddit),
                            'upvote_ratio': post.upvote_ratio
                        }
                    }
                    
                    # Check if already in collection
                    if not any(p['id'] == post.id for p in all_posts):
                        all_posts.append(post_data)
                        print(f"  ✅ Found: {post.title[:60]}...")
                
            except Exception as e:
                print(f"  ⚠️  Error with keyword '{keyword}': {e}")
                continue
        
        print(f"  📊 Total from r/{sub_name}: {len([p for p in all_posts if p['subreddit'] == sub_name])}")
        
    except Exception as e:
        print(f"  ❌ Error accessing r/{sub_name}: {e}")
        continue

print(f"\n🎉 COLLECTION COMPLETE!")
print(f"📈 Total posts collected: {len(all_posts)}")

if all_posts:
    # Save to JSON file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"reddit_fresh_data_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(all_posts, f, indent=2, default=str)
    
    print(f"💾 Saved to: {filename}")
    
    # Show statistics
    print(f"\n📊 STATISTICS:")
    by_subreddit = {}
    for post in all_posts:
        sub = post['subreddit']
        by_subreddit[sub] = by_subreddit.get(sub, 0) + 1
    
    print(f"📍 By Subreddit:")
    for sub, count in sorted(by_subreddit.items(), key=lambda x: x[1], reverse=True):
        print(f"  r/{sub}: {count}")
    
    print(f"\n✅ Next step: Run 'python3 process_data.py' to analyze and store in database")
else:
    print(f"📭 No Gusto posts found in the last {days_back} days")
    print(f"💡 This could mean:")
    print(f"  - Gusto is not being discussed much in these subreddits")
    print(f"  - Try expanding search terms or subreddits")
    print(f"  - Check API rate limits")

