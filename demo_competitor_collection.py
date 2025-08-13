#!/usr/bin/env python3
"""
Demo script to collect a small sample of competitor Reddit data for testing.
"""

import asyncio
import logging
from competitor_reddit_collector import CompetitorRedditCollector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def demo_collection():
    """Demo collecting a small sample of competitor data."""
    collector = CompetitorRedditCollector()
    
    # Collect just a few days of data for ADP as a test
    logger.info("🚀 Starting demo collection for ADP (3 days)")
    
    try:
        adp_data = await collector.collect_competitor_data('adp', days_back=3)
        
        logger.info(f"✅ Demo complete! Collected {len(adp_data)} ADP posts")
        
        if adp_data:
            logger.info("📊 Sample post titles:")
            for i, post in enumerate(adp_data[:3]):  # Show first 3 titles
                logger.info(f"  {i+1}. {post.get('title', 'No title')[:100]}")
        
        # Save to file for inspection
        collector.save_competitor_data_to_file({'adp': adp_data}, 'demo_adp_data.json')
        
        # Optionally save to database
        save_to_db = input("\n💾 Save this demo data to database? (y/N): ").lower().strip()
        if save_to_db == 'y':
            collector.save_competitor_data_to_db({'adp': adp_data})
            logger.info("✅ Demo data saved to database!")
        else:
            logger.info("📁 Demo data saved to demo_adp_data.json only")
            
    except Exception as e:
        logger.error(f"❌ Error during demo collection: {e}")

if __name__ == "__main__":
    print("🎯 Gusto Competitor Reddit Data Collection Demo")
    print("=" * 50)
    asyncio.run(demo_collection())
