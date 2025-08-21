#!/usr/bin/env python3
"""
Simple test script to verify Streamlit app works locally before deployment.
"""

import subprocess
import sys
import os

def check_requirements():
    """Check if required packages are installed."""
    required_packages = [
        'streamlit',
        'plotly',
        'pandas',
        'sqlalchemy'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} - installed")
        except ImportError:
            missing.append(package)
            print(f"❌ {package} - missing")
    
    if missing:
        print(f"\n🚨 Missing packages: {', '.join(missing)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    print("\n✅ All required packages are installed!")
    return True

def test_database_connection():
    """Test if database connection works."""
    try:
        # Add current directory to path
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        from backend.database.database import get_session
        from backend.database.models import SocialMediaPost
        
        with get_session() as session:
            post_count = session.query(SocialMediaPost).count()
            print(f"✅ Database connection successful! Found {post_count} posts.")
            return True
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def run_streamlit():
    """Run the Streamlit app."""
    print("\n🚀 Starting Streamlit app...")
    print("📱 Your dashboard will open in your browser automatically.")
    print("🛑 Press Ctrl+C to stop the server")
    
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "streamlit_app.py"])
    except KeyboardInterrupt:
        print("\n👋 Streamlit app stopped.")

if __name__ == "__main__":
    print("🧪 Testing Streamlit App Setup\n")
    
    if not check_requirements():
        sys.exit(1)
    
    if not test_database_connection():
        print("\n⚠️  Database issues detected. The app may not work properly.")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    print("\n🎉 All tests passed!")
    response = input("Run Streamlit app now? (y/n): ")
    
    if response.lower() == 'y':
        run_streamlit()
    else:
        print("\n✅ Setup complete! Run 'streamlit run streamlit_app.py' when ready.")
