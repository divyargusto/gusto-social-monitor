#!/usr/bin/env python3
"""
Simple test script to collect Reddit data about Gusto
"""

import asyncio
import json
import logging
from datetime import datetime
from dotenv import load_dotenv

from collectors.reddit_collector import RedditCollector
from utils.sentiment_analyzer import SentimentAnalyzer
from utils.theme_extractor import ThemeExtractor
from utils.data_processor import DataProcessor
from backend.database.database import init_database

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    """Test Reddit data collection and analysis."""
    
    print("🚀 Starting Gusto Reddit Monitor Test...")
    
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
    
    # Collect data
    print("📊 Collecting Reddit data (this may take a few minutes)...")
    
    keywords = ["Gusto payroll", "Gusto HR", "Gusto software", "@gustohq"]
    reddit_data = await reddit_collector.collect_data(keywords, days_back=2)
    
    print(f"📈 Collected {len(reddit_data)} posts/comments from Reddit")
    
    if reddit_data:
        # Save raw data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reddit_data_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(reddit_data, f, indent=2, default=str)
        
        print(f"💾 Raw data saved to {filename}")
        
        # Quick analysis
        positive = sum(1 for item in reddit_data if 'gusto' in item.get('text', '').lower() and any(word in item.get('text', '').lower() for word in ['good', 'great', 'love', 'excellent']))
        negative = sum(1 for item in reddit_data if 'gusto' in item.get('text', '').lower() and any(word in item.get('text', '').lower() for word in ['bad', 'terrible', 'hate', 'awful']))
        
        print(f"🔍 Quick sentiment check:")
        print(f"   Potentially positive mentions: {positive}")
        print(f"   Potentially negative mentions: {negative}")
        print(f"   Neutral/other: {len(reddit_data) - positive - negative}")
        
    else:
        print("📭 No data found. Try expanding the search terms or date range.")
    
    print("✅ Test completed successfully!")

if __name__ == "__main__":
    asyncio.run(main()) 