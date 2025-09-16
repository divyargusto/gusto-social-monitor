#!/usr/bin/env python3
"""
Weekly Scheduler for Gusto Social Media Monitor
Runs data refresh every Monday at 9 AM
"""

import os
import sys
import time
import logging
import argparse
import subprocess
from datetime import datetime

try:
    import schedule
    SCHEDULE_AVAILABLE = True
except ImportError:
    SCHEDULE_AVAILABLE = False
    print("WARNING: schedule not available. Install with: pip install schedule")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WeeklyScheduler:
    def __init__(self, refresh_time="09:00"):
        self.refresh_time = refresh_time
        self.refresh_script = os.path.join(os.path.dirname(__file__), 'automated_data_refresh.py')
        logger.info(f"📅 Scheduler initialized - runs every Monday at {refresh_time}")
    
    def run_refresh_job(self):
        logger.info("🚀 Starting weekly data refresh...")
        try:
            result = subprocess.run([sys.executable, self.refresh_script], 
                                  capture_output=True, text=True, timeout=3600)
            if result.returncode == 0:
                logger.info("✅ Data refresh completed successfully")
            else:
                logger.error(f"❌ Data refresh failed: {result.stderr}")
        except Exception as e:
            logger.error(f"❌ Error during refresh: {e}")
    
    def start_daemon(self):
        if not SCHEDULE_AVAILABLE:
            logger.error("❌ schedule library required. Install with: pip install schedule")
            return False
        
        schedule.every().monday.at(self.refresh_time).do(self.run_refresh_job)
        logger.info("🔄 Scheduler daemon started")
        
        while True:
            schedule.run_pending()
            time.sleep(60)

def main():
    parser = argparse.ArgumentParser(description="Weekly Scheduler for Gusto Social Media Monitor")
    parser.add_argument('--daemon', action='store_true', help='Run as daemon')
    parser.add_argument('--time', default='09:00', help='Refresh time (HH:MM)')
    parser.add_argument('--run-now', action='store_true', help='Run immediately')
    parser.add_argument('--show-cron', action='store_true', help='Show cron setup')
    
    args = parser.parse_args()
    scheduler = WeeklyScheduler(args.time)
    
    if args.show_cron:
        print("\n📅 CRON SETUP:")
        print("Add to crontab -e:")
        print("0 9 * * 1 cd /path/to/gusto-social-monitor && python scripts/automated_data_refresh.py")
        return
    
    if args.run_now:
        scheduler.run_refresh_job()
    elif args.daemon:
        scheduler.start_daemon()
    else:
        print("\n🤖 Enhanced Weekly Scheduler")
        print("Options:")
        print("  --daemon: Run as background daemon")
        print("  --run-now: Test run immediately")
        print("  --show-cron: Show cron setup instructions")

if __name__ == "__main__":
    main()
