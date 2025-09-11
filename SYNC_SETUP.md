# 🔄 Gusto Social Media Monitor - Machine Sync Guide

## 📋 Overview
This guide helps you sync your Gusto Social Media Monitoring App across different machines using Git and cloud storage.

## 🚀 Method 1: GitHub Repository (Recommended)

### **Step 1: Create GitHub Repository**
1. Go to [GitHub.com](https://github.com) and sign in
2. Click "New Repository" (green button)
3. Name it: `gusto-social-monitor`
4. Set to **Private** (contains API keys)
5. Don't initialize with README (we already have one)
6. Click "Create Repository"

### **Step 2: Push Your Code to GitHub**
```bash
# Add GitHub as remote origin
git remote add origin https://github.com/YOUR_USERNAME/gusto-social-monitor.git

# Push code to GitHub
git branch -M main
git push -u origin main
```

### **Step 3: Clone on New Machine**
```bash
# On your new machine
git clone https://github.com/YOUR_USERNAME/gusto-social-monitor.git
cd gusto-social-monitor

# Set up virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Copy your .env file (see Environment Setup below)
```

## 🔐 Method 2: Private Git Service

### **GitLab (Free Private Repos)**
```bash
git remote add origin https://gitlab.com/YOUR_USERNAME/gusto-social-monitor.git
git push -u origin main
```

### **Bitbucket (Free Private Repos)**
```bash
git remote add origin https://bitbucket.org/YOUR_USERNAME/gusto-social-monitor.git
git push -u origin main
```

## 📁 Method 3: Cloud Storage Backup

### **For Additional Backup (Use with Git)**
1. **Google Drive/Dropbox/OneDrive**:
   - Zip the entire project folder
   - Upload to cloud storage
   - Download and extract on new machine

2. **iCloud (macOS)**:
   - Move project to `~/Documents` (iCloud synced)
   - Access from any Mac with same Apple ID

## 🔑 Environment Setup (CRITICAL)

Your `.env` file contains sensitive API keys and is NOT synced via Git (for security).

### **Step 1: Backup .env Securely**
```bash
# View your current .env content
cat .env

# Copy this content to a secure note app or password manager
```

### **Step 2: Recreate .env on New Machine**
```bash
# In your project directory on new machine
cp .env.example .env
nano .env  # or use any text editor

# Add your actual API keys:
# REDDIT_CLIENT_ID=your_reddit_client_id
# REDDIT_CLIENT_SECRET=your_reddit_client_secret
# REDDIT_USER_AGENT=your_user_agent
# etc.
```

## 💾 Database Migration

### **Option A: Fresh Start (Recommended)**
```bash
# On new machine, collect fresh data
python reddit_focused_search.py
python demo_competitor_collection.py
```

### **Option B: Transfer Database**
```bash
# On old machine - backup database
cp gusto_monitor.db gusto_monitor_backup.db

# Transfer file manually (email, USB, cloud storage)
# Place in project root on new machine
```

## 🔄 Daily Sync Workflow

### **When Making Changes**
```bash
# Save your work
git add .
git commit -m "Updated competitive analysis features"
git push origin main
```

### **When Switching Machines**
```bash
# Pull latest changes
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Run the app
PYTHONPATH=$(pwd) python backend/app/app.py
```

## 🛠️ Cursor-Specific Sync

### **Cursor Settings Sync**
1. **Sign in to Cursor**: Use GitHub/Google account
2. **Settings sync automatically**: Extensions, themes, shortcuts
3. **AI context**: Your conversation history syncs across devices

### **Project-Specific Settings**
```bash
# Cursor workspace settings are in .cursor/ (already in .gitignore)
# These sync automatically when signed in to Cursor
```

## 📱 Quick Setup Script

Create this on your new machine:

```bash
#!/bin/bash
# setup_gusto_monitor.sh

echo "🚀 Setting up Gusto Social Media Monitor..."

# Clone repository
git clone https://github.com/YOUR_USERNAME/gusto-social-monitor.git
cd gusto-social-monitor

# Set up Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

echo "✅ Setup complete!"
echo "🔑 Don't forget to update .env with your API keys"
echo "🚀 Run: PYTHONPATH=$(pwd) python backend/app/app.py"
```

## ⚠️ Security Reminders

1. **Never commit .env files** (already in .gitignore)
2. **Use private repositories** for this project
3. **Store API keys securely** (password manager)
4. **Review .gitignore** before committing sensitive data

## 🆘 Troubleshooting

### **Common Issues:**
1. **"Module not found"** → Check PYTHONPATH and virtual environment
2. **"Database error"** → Check if gusto_monitor.db exists
3. **"API errors"** → Verify .env file has correct API keys
4. **"Port 5000 in use"** → Kill existing Flask processes

### **Quick Commands:**
```bash
# Check if Flask is running
lsof -i :5000

# Kill Flask process
pkill -f "python.*app.py"

# Restart Flask
PYTHONPATH=$(pwd) python backend/app/app.py
```

---

✨ **You're all set!** Your Gusto Social Media Monitor will now sync seamlessly across all your machines.
