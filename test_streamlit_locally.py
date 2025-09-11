#!/usr/bin/env python3
"""
Quick test script to verify Streamlit app functionality before deployment.
"""

import sqlite3
import os
import sys

def test_database_connection():
    """Test if the database file exists and has data."""
    print("🔍 Testing Database Connection...")
    
    db_paths = [
        'gusto_monitor.db',
        'backend/gusto_monitor.db',
        './gusto_monitor.db'
    ]
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Test basic queries
                cursor.execute("SELECT COUNT(*) FROM social_media_posts")
                post_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM themes")
                theme_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(DISTINCT sentiment_label) FROM social_media_posts WHERE sentiment_label IS NOT NULL")
                sentiment_count = cursor.fetchone()[0]
                
                print(f"✅ Database found: {db_path}")
                print(f"   📊 Posts: {post_count}")
                print(f"   🎯 Themes: {theme_count}")
                print(f"   😊 Sentiments: {sentiment_count}")
                
                if post_count > 0:
                    print("✅ Database has data - Streamlit app should work!")
                    return True
                else:
                    print("⚠️  Database is empty - app will show 0 data")
                    return False
                    
            except Exception as e:
                print(f"❌ Database error: {e}")
                continue
    
    print("❌ No database file found!")
    return False

def test_streamlit_imports():
    """Test if Streamlit and required packages are installed."""
    print("\n📦 Testing Package Imports...")
    
    required_packages = [
        ('streamlit', 'Streamlit'),
        ('plotly', 'Plotly'),
        ('pandas', 'Pandas'),
        ('sqlite3', 'SQLite3')
    ]
    
    missing = []
    for package, name in required_packages:
        try:
            __import__(package)
            print(f"✅ {name} - installed")
        except ImportError:
            missing.append(name)
            print(f"❌ {name} - missing")
    
    if missing:
        print(f"\n🚨 Missing packages: {', '.join(missing)}")
        print("Run: pip install streamlit plotly pandas")
        return False
    
    print("✅ All packages installed!")
    return True

def test_streamlit_app():
    """Test if the Streamlit app file exists and has no syntax errors."""
    print("\n🎯 Testing Streamlit App File...")
    
    app_files = ['streamlit_app_fixed.py', 'streamlit_app.py']
    
    for app_file in app_files:
        if os.path.exists(app_file):
            try:
                with open(app_file, 'r') as f:
                    content = f.read()
                
                # Basic syntax check
                compile(content, app_file, 'exec')
                
                print(f"✅ {app_file} - syntax OK")
                print(f"   📄 File size: {len(content)} characters")
                
                # Check for key functions
                key_features = [
                    'load_overview_data',
                    'load_sentiment_trends', 
                    'load_themes_data',
                    'load_posts_by_theme_sentiment'
                ]
                
                for feature in key_features:
                    if feature in content:
                        print(f"   ✅ {feature} - found")
                    else:
                        print(f"   ❌ {feature} - missing")
                
                return app_file
                
            except SyntaxError as e:
                print(f"❌ {app_file} - syntax error: {e}")
                continue
    
    print("❌ No valid Streamlit app file found!")
    return None

def run_streamlit_test():
    """Run a quick Streamlit test."""
    print("\n🚀 Running Streamlit Test...")
    
    import subprocess
    
    app_file = test_streamlit_app()
    if not app_file:
        return False
    
    print(f"🎯 Testing {app_file}...")
    print("📱 Streamlit app will open in your browser")
    print("🛑 Press Ctrl+C to stop the test")
    
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", app_file])
        return True
    except KeyboardInterrupt:
        print("\n👋 Test stopped by user")
        return True
    except Exception as e:
        print(f"❌ Streamlit test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 STREAMLIT APP TESTING\n")
    
    # Test 1: Database
    db_ok = test_database_connection()
    
    # Test 2: Imports
    imports_ok = test_streamlit_imports()
    
    # Test 3: App file
    app_ok = test_streamlit_app() is not None
    
    # Summary
    print("\n" + "="*50)
    print("📋 TEST SUMMARY:")
    print(f"   Database: {'✅' if db_ok else '❌'}")
    print(f"   Packages: {'✅' if imports_ok else '❌'}")
    print(f"   App File: {'✅' if app_ok else '❌'}")
    
    if db_ok and imports_ok and app_ok:
        print("\n🎉 ALL TESTS PASSED!")
        response = input("\n🚀 Run Streamlit app now? (y/n): ")
        if response.lower() == 'y':
            run_streamlit_test()
    else:
        print("\n⚠️  Some tests failed. Fix the issues before deploying.")
    
    print("\n✅ Testing complete!")

if __name__ == "__main__":
    main()
