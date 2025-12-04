#!/usr/bin/env python3
"""
Process collected JSON data and store in database
"""

import json
import pandas as pd
from datetime import datetime
from utils.data_processor import DataProcessor
from backend.database.database import init_database

def main():
    print("🔄 Processing collected social media data...")
    
    # Initialize database
    init_database()
    
    # Process fresh Reddit data
    data_files = [
        "reddit_fresh_data_20251204_101702.json"
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
    
    print("🧠 Running sentiment analysis and theme extraction...")
    
    # Process the data (this will store it in the database)
    result = processor.process(df)
    
    print("✅ Data processing completed!")
    print(f"📈 Processed {len(df)} items")
    
    # Show summary
    if result:
        overview = result.get('overview', {})
        sentiment = result.get('sentiment_analysis', {})
        
        print(f"\n📊 Summary:")
        print(f"   Total posts: {overview.get('total_posts', 0)}")
        print(f"   Average sentiment: {overview.get('avg_sentiment_score', 0):.3f}")
        
        sentiment_breakdown = sentiment.get('sentiment_breakdown', {})
        total = sum(sentiment_breakdown.values())
        if total > 0:
            print(f"   Sentiment breakdown:")
            for sentiment_type, count in sentiment_breakdown.items():
                percentage = (count / total) * 100
                print(f"     {sentiment_type.title()}: {percentage:.1f}%")
    
    print(f"\n🌐 Data is now available in your dashboard at http://localhost:5000")

if __name__ == "__main__":
    main() 