#!/usr/bin/env python3
"""
Script to clear cache and test Streamlit data loading
"""

import os
import shutil
from pathlib import Path

def clear_streamlit_cache():
    """Clear all Streamlit cache files"""
    print("🧹 CLEARING STREAMLIT CACHE")
    
    # Clear common cache locations
    cache_dirs = [
        ".streamlit",
        "__pycache__",
        "backend/__pycache__",
        "backend/database/__pycache__",
        "utils/__pycache__",
        "collectors/__pycache__"
    ]
    
    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            shutil.rmtree(cache_dir)
            print(f"  ✅ Removed {cache_dir}")
    
    # Clear Python bytecode files
    for pyc_file in Path(".").rglob("*.pyc"):
        pyc_file.unlink()
        
    print("✅ Cache cleared!")

def test_data_loading():
    """Test the data loading functions"""
    print("\n🔍 TESTING DATA LOADING FUNCTIONS")
    
    # Import after cache clear
    from backend.database.database import init_database, get_session
    from backend.database.models import SocialMediaPost
    from datetime import datetime
    from sqlalchemy import func
    
    try:
        init_database()
        
        with get_session() as session:
            start_date = datetime(2025, 1, 1).date()
            end_date = datetime.now().date()
            
            # Simulate the exact Streamlit query
            start_dt = datetime.combine(start_date, datetime.min.time())
            end_dt = datetime.combine(end_date, datetime.max.time())
            
            base_query = session.query(SocialMediaPost).filter(
                SocialMediaPost.platform == 'reddit',
                SocialMediaPost.created_at >= start_dt,
                SocialMediaPost.created_at <= end_dt
            )
            
            total_posts = base_query.count()
            print(f"📊 Total posts that should appear: {total_posts}")
            
            # Aug/Sep specific
            aug_sep = base_query.filter(
                func.strftime('%Y-%m', SocialMediaPost.created_at).in_(['2025-08', '2025-09'])
            ).count()
            print(f"🎯 August/September posts: {aug_sep}")
            
            if aug_sep > 0:
                print("✅ August/September data IS AVAILABLE")
                print("🎯 If dashboard shows 0, it's a caching issue!")
            else:
                print("❌ No August/September data found")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    clear_streamlit_cache()
    test_data_loading()
    print("\n🚀 Now run: streamlit run streamlit_app.py")
    print("📋 Click 'Clear Cache & Refresh Data' button in the sidebar!")
