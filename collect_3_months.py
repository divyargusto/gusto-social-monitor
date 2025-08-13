#!/usr/bin/env python3
"""
Enhanced Reddit data collection for 3 months of Gusto mentions
"""

import asyncio
import json
import logging
from datetime import datetime
from dotenv import load_dotenv

from collectors.reddit_collector import RedditCollector
from backend.database.database import init_database

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    """Collect 3 months of Reddit data about Gusto."""
    
    print("🚀 Starting 3-Month Gusto Reddit Data Collection...")
    print("📅 Searching: April-June 2025 (last 3 months)")
    
    # Initialize database
    try:
        init_database()
        print("✅ Database initialized")
    except Exception as e:
        print(f"❌ Database error: {e}")
        return
    
    # Initialize Reddit collector
    reddit_collector = RedditCollector()
    if not reddit_collector.reddit:
        print("❌ Reddit API not connected. Check your .env file.")
        return
    
    print("✅ Reddit API connected")
    
    # Expanded keywords for better coverage
    keywords = [
        # Brand mentions
        "Gusto payroll", "Gusto HR", "Gusto software", "@gustohq", "gusto.com",
        
        # Product specific
        "Gusto benefits", "Gusto onboarding", "Gusto time tracking", "Gusto PTO",
        "Gusto taxes", "Gusto direct deposit", "Gusto compliance",
        
        # Comparison mentions
        "Gusto vs", "Gusto alternative", "Gusto review", "Gusto pricing",
        "compared to Gusto", "instead of Gusto", "switched to Gusto",
        
        # General mentions (case-sensitive search)
        "Gusto", "gustohq"
    ]
    
    print(f"🔍 Searching with {len(keywords)} different keyword combinations...")
    print("📊 This will take several minutes to search thoroughly...")
    
    # Collect data for 3 months (90 days)
    days_back = 90
    reddit_data = await reddit_collector.collect_data(keywords, days_back=days_back)
    
    print(f"📈 Collected {len(reddit_data)} posts/comments from Reddit")
    
    if reddit_data:
        # Save raw data with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reddit_data_3months_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(reddit_data, f, indent=2, default=str)
        
        print(f"💾 Raw data saved to {filename}")
        
        # Analyze the data
        platforms = {}
        sentiment_quick = {'positive': 0, 'negative': 0, 'neutral': 0}
        
        for item in reddit_data:
            platform = item.get('platform', 'unknown')
            platforms[platform] = platforms.get(platform, 0) + 1
            
            text = item.get('text', '').lower()
            # Quick sentiment check
            if any(word in text for word in ['good', 'great', 'love', 'excellent', 'recommend', 'amazing', 'perfect']):
                sentiment_quick['positive'] += 1
            elif any(word in text for word in ['bad', 'terrible', 'hate', 'awful', 'worst', 'horrible', 'sucks']):
                sentiment_quick['negative'] += 1
            else:
                sentiment_quick['neutral'] += 1
        
        print(f"\n📊 Collection Summary:")
        print(f"   Total items: {len(reddit_data)}")
        print(f"   Time period: {days_back} days")
        
        print(f"\n📱 Platform breakdown:")
        for platform, count in platforms.items():
            print(f"   {platform}: {count} items")
        
        print(f"\n💭 Quick sentiment analysis:")
        total = len(reddit_data)
        for sentiment, count in sentiment_quick.items():
            pct = (count/total*100) if total > 0 else 0
            print(f"   {sentiment.title()}: {count} ({pct:.1f}%)")
        
        print(f"\n🔄 Next steps:")
        print(f"   1. Run: python process_data.py")
        print(f"   2. Update process_data.py to use file: {filename}")
        print(f"   3. View results at: http://localhost:5000")
        
    else:
        print("📭 No data found. This could mean:")
        print("   - Very few Gusto mentions in the time period")
        print("   - API rate limits")
        print("   - Subreddits not accessible")
        print("   - Try different keywords or time periods")
    
    print("✅ 3-month collection completed!")

if __name__ == "__main__":
    asyncio.run(main()) 