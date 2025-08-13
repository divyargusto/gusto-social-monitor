#!/usr/bin/env python3
"""
Test script for YouTube collector
Note: Requires YOUTUBE_API_KEY environment variable to be set
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_youtube_collector():
    """Test the YouTube collector functionality."""
    
    # Check if API key is available
    api_key = os.getenv('YOUTUBE_API_KEY')
    if not api_key:
        print("❌ YouTube API key not found!")
        print("📝 To use YouTube functionality:")
        print("   1. Get a YouTube Data API v3 key from Google Cloud Console")
        print("   2. Set it as environment variable: export YOUTUBE_API_KEY='your-key-here'")
        print("   3. Add it to your .env file: YOUTUBE_API_KEY=your-key-here")
        print("\n🔗 Get API key at: https://console.cloud.google.com/apis/credentials")
        return False
    
    try:
        from collectors.youtube_collector import YouTubeCollector
        
        print("🎬 Testing YouTube Collector...")
        print(f"✅ API Key found: {api_key[:10]}...")
        
        # Initialize collector
        collector = YouTubeCollector()
        print("✅ YouTube collector initialized")
        
        # Test search (dry run - just search, don't store)
        print("🔍 Testing video search...")
        videos = collector.search_gusto_videos(max_results=3, days_back=30)
        
        if videos:
            print(f"✅ Found {len(videos)} Gusto-related videos")
            for i, video in enumerate(videos[:2], 1):
                print(f"   {i}. {video['title'][:60]}...")
                print(f"      Channel: {video['channel_title']}")
                print(f"      URL: {video['url']}")
        else:
            print("⚠️  No Gusto-related videos found (this is normal if there's limited recent content)")
        
        print("\n🎯 YouTube collector is ready!")
        print("💡 To collect data through the web interface:")
        print("   1. Go to http://localhost:5000")
        print("   2. Click 'Collect Data' in the YouTube Sources section")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing YouTube collector: {e}")
        return False

if __name__ == '__main__':
    success = test_youtube_collector()
    sys.exit(0 if success else 1)