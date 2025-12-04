#!/usr/bin/env python3
"""
Comprehensive Reddit search for Gusto mentions across 60+ subreddits
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
    """Comprehensive search across 60+ subreddits for Gusto mentions."""
    
    print("🚀 Starting COMPREHENSIVE Gusto Reddit Search...")
    print("📊 Searching 60+ subreddits + site-wide search")
    print("📅 Looking back 3 months for maximum data")
    print("⏰ This will take 10-15 minutes for thorough coverage...")
    
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
    
    # Ultra-comprehensive keywords for maximum coverage
    keywords = [
        # Primary brand mentions
        "Gusto", "gustohq", "gusto.com", "@gustohq",
        
        # Product-specific searches
        "Gusto payroll", "Gusto HR", "Gusto software", "Gusto app",
        "Gusto benefits", "Gusto onboarding", "Gusto time tracking", 
        "Gusto PTO", "Gusto taxes", "Gusto direct deposit", 
        "Gusto compliance", "Gusto W2", "Gusto 1099",
        
        # Comparison searches (high-value data)
        "Gusto vs ADP", "Gusto vs Paychex", "Gusto vs BambooHR",
        "Gusto vs Rippling", "Gusto vs QuickBooks payroll",
        "ADP vs Gusto", "Paychex vs Gusto", "BambooHR vs Gusto",
        
        # Decision-making searches
        "Gusto review", "Gusto pricing", "Gusto cost", "Gusto demo",
        "should I use Gusto", "Gusto worth it", "Gusto experience",
        "switched to Gusto", "migrated to Gusto", "left Gusto",
        
        # Problem/solution searches
        "Gusto issues", "Gusto problems", "Gusto support",
        "Gusto alternatives", "instead of Gusto", "better than Gusto",
        
        # Integration searches
        "Gusto QuickBooks", "Gusto Xero", "Gusto integration",
        "Gusto API", "Gusto sync"
    ]
    
    print(f"🔍 Using {len(keywords)} comprehensive keyword searches")
    print(f"📈 Searching {len(reddit_collector.target_subreddits) if hasattr(reddit_collector, 'target_subreddits') else '60+'} subreddits")
    
    # Focused time period for better search results
    days_back = 90  # 3 months for more reliable results
    print(f"📅 Search period: {days_back} days (3 months)")
    
    # Collect data
    reddit_data = await reddit_collector.collect_data(keywords, days_back=days_back)
    
    print(f"\n🎉 COLLECTION COMPLETE!")
    print(f"📈 Total collected: {len(reddit_data)} posts/comments")
    
    if reddit_data:
        # Save comprehensive data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reddit_comprehensive_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(reddit_data, f, indent=2, default=str)
        
        print(f"💾 Comprehensive data saved to: {filename}")
        
        # Detailed analysis
        print(f"\n📊 COMPREHENSIVE ANALYSIS:")
        
        # Platform breakdown
        platforms = {}
        subreddits = {}
        keywords_found = {}
        monthly_data = {}
        
        for item in reddit_data:
            # Platform stats
            platform = item.get('platform', 'unknown')
            platforms[platform] = platforms.get(platform, 0) + 1
            
            # Subreddit stats
            subreddit = item.get('subreddit', 'unknown')
            subreddits[subreddit] = subreddits.get(subreddit, 0) + 1
            
            # Keyword stats
            text = item.get('text', '').lower()
            for keyword in ['gusto', 'payroll', 'hr', 'benefits', 'vs']:
                if keyword in text:
                    keywords_found[keyword] = keywords_found.get(keyword, 0) + 1
            
            # Monthly breakdown
            created_at = item.get('created_at', '')
            if created_at:
                try:
                    month = created_at[:7]  # YYYY-MM format
                    monthly_data[month] = monthly_data.get(month, 0) + 1
                except:
                    pass
        
        print(f"   📊 Total items: {len(reddit_data)}")
        print(f"   📅 Time span: {days_back} days (6 months)")
        
        print(f"\n🏆 TOP SUBREDDITS:")
        sorted_subreddits = sorted(subreddits.items(), key=lambda x: x[1], reverse=True)
        for subreddit, count in sorted_subreddits[:10]:
            print(f"   r/{subreddit}: {count} mentions")
        
        print(f"\n🔍 TOP KEYWORDS FOUND:")
        sorted_keywords = sorted(keywords_found.items(), key=lambda x: x[1], reverse=True)
        for keyword, count in sorted_keywords[:10]:
            print(f"   '{keyword}': {count} occurrences")
        
        print(f"\n📈 MONTHLY BREAKDOWN:")
        sorted_months = sorted(monthly_data.items(), reverse=True)
        for month, count in sorted_months[:6]:
            print(f"   {month}: {count} posts")
        
        # Quick sentiment preview
        sentiment_quick = {'positive': 0, 'negative': 0, 'neutral': 0}
        for item in reddit_data:
            text = item.get('text', '').lower()
            if any(word in text for word in ['good', 'great', 'love', 'excellent', 'recommend', 'amazing', 'perfect', 'easy', 'simple']):
                sentiment_quick['positive'] += 1
            elif any(word in text for word in ['bad', 'terrible', 'hate', 'awful', 'worst', 'horrible', 'sucks', 'difficult', 'confusing']):
                sentiment_quick['negative'] += 1
            else:
                sentiment_quick['neutral'] += 1
        
        print(f"\n💭 QUICK SENTIMENT PREVIEW:")
        total = len(reddit_data)
        for sentiment, count in sentiment_quick.items():
            pct = (count/total*100) if total > 0 else 0
            print(f"   {sentiment.title()}: {count} ({pct:.1f}%)")
        
        print(f"\n🔄 NEXT STEPS:")
        print(f"   1. Update process_data.py to use: {filename}")
        print(f"   2. Run: python process_data.py")
        print(f"   3. Start dashboard: python backend/app/app.py")
        print(f"   4. View results at: http://localhost:5000")
        
        # Update the process_data.py file automatically
        try:
            with open('process_data.py', 'r') as f:
                content = f.read()
            
            # Find and replace the JSON filename
            import re
            new_content = re.sub(
                r'json_file = "reddit_data_.*\.json"',
                f'json_file = "{filename}"',
                content
            )
            
            with open('process_data.py', 'w') as f:
                f.write(new_content)
            
            print(f"   ✅ Auto-updated process_data.py to use {filename}")
            
        except Exception as e:
            print(f"   ⚠️  Manually update process_data.py filename: {e}")
        
    else:
        print("📭 No data found - this is unusual with such comprehensive search!")
        print("   Check API limits or credentials")
    
    print("\n🎉 COMPREHENSIVE SEARCH COMPLETED!")
    print(f"Expected much more data with 60+ subreddits and 6-month timeframe!")

if __name__ == "__main__":
    asyncio.run(main()) 