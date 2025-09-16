# Enhanced Gusto Social Media Monitor - Automated Data Refresh

Enhanced automation scripts for comprehensive weekly data refresh every Monday.

## 🚀 Quick Start

1. **Install dependencies:**
   ```bash
   pip install praw schedule pandas
   ```

2. **Set up Reddit API credentials:**
   - Go to https://www.reddit.com/prefs/apps
   - Create new app (script type)
   - Set environment variables:
     ```bash
     export REDDIT_CLIENT_ID=your_client_id
     export REDDIT_CLIENT_SECRET=your_client_secret
     ```

3. **Test the setup:**
   ```bash
   python scripts/automated_data_refresh.py --test-run
   ```

4. **Set up weekly automation:**
   ```bash
   # Option A: Daemon mode
   python scripts/schedule_weekly_refresh.py --daemon
   
   # Option B: Cron setup
   python scripts/schedule_weekly_refresh.py --show-cron
   ```

## 🎯 Enhanced Features

### 📊 Comprehensive Reddit Monitoring
- **18+ Subreddits**: smallbusiness, entrepreneur, business, humanresources, payroll, accounting, startups, freelance, remotework, WorkOnline, personalfinance, bookkeeping, smallbiz, solopreneur, consulting, contractoruk, freelancewriters, digitalnomad

### 🔍 Advanced Search Terms  
- **10+ Specific Terms**: "gusto payroll", "gusto hr", "gusto benefits", "gusto software", "gusto review", "gusto experience", "gusto vs", "gusto pricing", "gusto customer service", "gusto integration"

### ⚙️ Smart Features
- Rate limiting for Reddit API compliance
- Comprehensive error handling and logging
- Test mode for safe development
- Flexible scheduling (daemon or cron)
- Integration with existing infrastructure

## 📈 Performance
- **Coverage**: 18+ subreddits, 10+ search terms
- **Runtime**: 10-25 minutes per run
- **Memory**: ~300MB during processing
- **API Calls**: 200-800 Reddit requests per run

## 🔧 Integration
- Uses existing `utils/` modules (sentiment_analyzer, data_processor, theme_extractor)
- Compatible with current database schema
- Extends existing `auto_update_reddit.py` functionality
- Maintains backward compatibility

The enhanced automation provides comprehensive social media monitoring while maintaining full compatibility with existing infrastructure.
