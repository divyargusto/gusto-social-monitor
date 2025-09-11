#!/usr/bin/env python3
"""
Check which files should be uploaded to GitHub for Streamlit deployment.
"""

import os
import glob

def check_files():
    """Check which files are essential for upload."""
    
    print("🔍 CHECKING FILES FOR GITHUB UPLOAD\n")
    
    # Essential files
    essential_files = [
        'streamlit_app.py',
        'requirements.txt', 
        '.gitignore'
    ]
    
    print("✅ ESSENTIAL FILES (Must upload):")
    for file in essential_files:
        if os.path.exists(file):
            size = os.path.getsize(file) / 1024  # KB
            print(f"   ✅ {file} ({size:.1f} KB)")
        else:
            print(f"   ❌ {file} - MISSING!")
    
    # Backend folder
    print("\n✅ BACKEND CODE (Must upload):")
    if os.path.exists('backend'):
        backend_files = []
        for root, dirs, files in os.walk('backend'):
            for file in files:
                if file.endswith('.py'):
                    backend_files.append(os.path.join(root, file))
        
        print(f"   ✅ backend/ folder ({len(backend_files)} Python files)")
        for file in backend_files[:5]:  # Show first 5
            print(f"      - {file}")
        if len(backend_files) > 5:
            print(f"      ... and {len(backend_files) - 5} more files")
    else:
        print("   ❌ backend/ folder - MISSING!")
    
    # Database files
    print("\n✅ DATABASE FILES (Upload if you want your data):")
    db_files = glob.glob('*.db') + glob.glob('*.sqlite') + glob.glob('*.sqlite3')
    if db_files:
        for db_file in db_files:
            size = os.path.getsize(db_file) / (1024 * 1024)  # MB
            print(f"   ✅ {db_file} ({size:.1f} MB)")
    else:
        print("   ⚠️  No database files found")
    
    # Documentation
    print("\n📚 DOCUMENTATION (Optional but recommended):")
    doc_files = [
        'STREAMLIT_README.md',
        'DEPLOYMENT_GUIDE.md',
        'test_streamlit.py'
    ]
    for file in doc_files:
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} - missing")
    
    # Files to SKIP
    print("\n❌ FILES TO SKIP (Don't upload):")
    skip_patterns = [
        'venv/',
        'env/',
        '__pycache__/',
        '*.pyc',
        '.DS_Store',
        '*.log'
    ]
    
    found_skip_files = []
    for pattern in skip_patterns:
        matches = glob.glob(pattern, recursive=True)
        if matches:
            found_skip_files.extend(matches[:3])  # Show first 3 matches
    
    if found_skip_files:
        for file in found_skip_files:
            print(f"   🚫 {file}")
    else:
        print("   ✅ No unnecessary files found!")
    
    # Summary
    print("\n" + "="*60)
    print("📋 SUMMARY:")
    print("1. Upload the ✅ files listed above")
    print("2. Skip the 🚫 files")
    print("3. Your Streamlit app will work with just the essential files!")
    print("="*60)

if __name__ == "__main__":
    os.chdir('/Users/divya.rathi/gusto-social-monitor')
    check_files()
