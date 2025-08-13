#!/usr/bin/env python3
"""
Reprocess all data with Gusto-specific sentiment and theme analysis
"""

import json
import pandas as pd
from datetime import datetime
from utils.data_processor import DataProcessor
from backend.database.database import init_database, get_session
from backend.database.models import (
    SocialMediaPost, Theme, PostTheme, Keyword, PostKeyword,
    SentimentTrend, CompetitorMention, DataCollection
)

def clear_database():
    """Clear all existing data from the database."""
    print("🗑️  Clearing existing database...")
    
    with get_session() as session:
        # Delete in correct order due to foreign key constraints
        session.query(PostKeyword).delete()
        session.query(PostTheme).delete()
        session.query(SentimentTrend).delete()
        session.query(CompetitorMention).delete()
        session.query(DataCollection).delete()
        session.query(SocialMediaPost).delete()
        session.query(Keyword).delete()
        session.query(Theme).delete()
        session.commit()
    
    print("✅ Database cleared!")

def main():
    print("🔄 Reprocessing data with Gusto-specific sentiment analysis...")
    
    # Initialize database
    init_database()
    
    # Clear existing data
    clear_database()
    
    # Process both LinkedIn and ultra-strict Reddit data
    data_files = [
        "linkedin_data_backup.json",
        "reddit_ultrastrict_gusto_20250723_105935.json"
    ]
    
    all_data = []
    
    for json_file in data_files:
        try:
            # Load the JSON data
            with open(json_file, 'r') as f:
                raw_data = json.load(f)
            
            print(f"📂 Loaded data from {json_file}")
            print(f"📊 Found {len(raw_data)} items")
            
            if raw_data:
                all_data.extend(raw_data)
                
        except FileNotFoundError:
            print(f"⚠️  File not found: {json_file}")
            continue
        except Exception as e:
            print(f"❌ Error loading {json_file}: {e}")
            continue
    
    if not all_data:
        print("❌ No data to process")
        return
    
    print(f"📊 Total combined items: {len(all_data)}")
    
    # Convert to DataFrame format expected by DataProcessor  
    df = pd.DataFrame(all_data)
    
    # Initialize data processor
    processor = DataProcessor()
    
    print("🧠 Running GUSTO-SPECIFIC sentiment analysis and theme extraction...")
    
    # Process the data (this will store it in the database)
    result = processor.process(df)
    
    print("✅ Gusto-specific data processing completed!")
    print(f"📈 Processed {len(df)} items")
    
    # Show summary
    if result:
        overview = result.get('overview', {})
        sentiment = result.get('sentiment_analysis', {})
        
        print(f"\n📊 Gusto-Specific Analysis Summary:")
        print(f"   Total posts: {overview.get('total_posts', 0)}")
        print(f"   Average Gusto sentiment: {overview.get('avg_sentiment_score', 0):.3f}")
        
        sentiment_breakdown = sentiment.get('sentiment_breakdown', {})
        total = sum(sentiment_breakdown.values())
        if total > 0:
            print(f"   Gusto sentiment breakdown:")
            for sentiment_type, count in sentiment_breakdown.items():
                percentage = (count / total) * 100
                print(f"     {sentiment_type.title()}: {percentage:.1f}%")
    
    print(f"\n🌐 Updated Gusto-specific analysis is now available at http://localhost:5000")

if __name__ == "__main__":
    main() 