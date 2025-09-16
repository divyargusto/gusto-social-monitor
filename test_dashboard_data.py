#!/usr/bin/env python3
"""
Test script to verify what data the Streamlit dashboard should be showing
"""

from backend.database.database import init_database, get_session
from backend.database.models import SocialMediaPost
from datetime import datetime
from sqlalchemy import func

def test_dashboard_data():
    print("🔍 TESTING DASHBOARD DATA VISIBILITY")
    print("=" * 50)
    
    try:
        init_database()
        
        with get_session() as session:
            # Same date range as dashboard default
            start_date = datetime(2025, 1, 1).date()
            end_date = datetime.now().date()
            
            print(f"📅 Date Range: {start_date} to {end_date}")
            
            # Convert to datetime for filtering (same as Streamlit)
            start_dt = datetime.combine(start_date, datetime.min.time())
            end_dt = datetime.combine(end_date, datetime.max.time())
            
            # Base query - Reddit only (same as Streamlit)
            base_query = session.query(SocialMediaPost).filter(
                SocialMediaPost.platform == 'reddit',
                SocialMediaPost.created_at >= start_dt,
                SocialMediaPost.created_at <= end_dt
            )
            
            total_posts = base_query.count()
            print(f"📊 Total Posts in Date Range: {total_posts}")
            
            # Monthly breakdown for 2025
            monthly_data = session.query(
                func.strftime('%Y-%m', SocialMediaPost.created_at).label('month'),
                func.count(SocialMediaPost.id).label('count')
            ).filter(
                SocialMediaPost.platform == 'reddit',
                SocialMediaPost.created_at >= start_dt,
                SocialMediaPost.created_at <= end_dt
            ).group_by(func.strftime('%Y-%m', SocialMediaPost.created_at)).order_by('month').all()
            
            print("\n📈 MONTHLY BREAKDOWN (What Dashboard Should Show):")
            for month, count in monthly_data:
                marker = "🎯" if month in ['2025-08', '2025-09'] else "📊"
                print(f"  {marker} {month}: {count} posts")
            
            # Sentiment breakdown for Aug/Sep
            aug_sep_sentiment = base_query.filter(
                func.strftime('%Y-%m', SocialMediaPost.created_at).in_(['2025-08', '2025-09'])
            ).with_entities(
                SocialMediaPost.sentiment_label,
                func.count(SocialMediaPost.id).label('count')
            ).group_by(SocialMediaPost.sentiment_label).all()
            
            print(f"\n🎯 AUGUST/SEPTEMBER 2025 SENTIMENT:")
            for sentiment, count in aug_sep_sentiment:
                print(f"  {sentiment or 'Unknown'}: {count} posts")
            
            # Recent posts sample
            recent_posts = base_query.filter(
                func.strftime('%Y-%m', SocialMediaPost.created_at).in_(['2025-08', '2025-09'])
            ).order_by(SocialMediaPost.created_at.desc()).limit(5).all()
            
            print(f"\n📝 SAMPLE AUGUST/SEPTEMBER POSTS:")
            for post in recent_posts:
                print(f"  {post.created_at.strftime('%Y-%m-%d')}: {post.title[:60]}...")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_dashboard_data()
