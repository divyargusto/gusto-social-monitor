#!/usr/bin/env python3
"""
Gusto Social Media Monitoring Tool
Collects and analyzes mentions of Gusto from various social media and review platforms.
"""

import asyncio
import argparse
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any

import pandas as pd
from dotenv import load_dotenv

from collectors.reddit_collector import RedditCollector
from collectors.google_reviews_collector import GoogleReviewsCollector
from collectors.linkedin_collector import LinkedInCollector
from collectors.g2_collector import G2Collector
from collectors.twitter_collector import TwitterCollector
from collectors.generic_web_collector import GenericWebCollector
from utils.sentiment_analyzer import SentimentAnalyzer
from utils.data_processor import DataProcessor
from utils.report_generator import ReportGenerator

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gusto_monitor.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class GustoSocialMonitor:
    """Main orchestrator for social media monitoring."""
    
    def __init__(self):
        self.collectors = {}
        self.sentiment_analyzer = SentimentAnalyzer()
        self.data_processor = DataProcessor()
        self.report_generator = ReportGenerator()
        
        # Initialize collectors
        self._initialize_collectors()
    
    def _initialize_collectors(self):
        """Initialize all data collectors."""
        try:
            self.collectors['reddit'] = RedditCollector()
            logger.info("Reddit collector initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Reddit collector: {e}")
        
        try:
            self.collectors['google_reviews'] = GoogleReviewsCollector()
            logger.info("Google Reviews collector initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Google Reviews collector: {e}")
        
        try:
            self.collectors['linkedin'] = LinkedInCollector()
            logger.info("LinkedIn collector initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize LinkedIn collector: {e}")
        
        try:
            self.collectors['g2'] = G2Collector()
            logger.info("G2 collector initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize G2 collector: {e}")
        
        try:
            self.collectors['twitter'] = TwitterCollector()
            logger.info("Twitter collector initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Twitter collector: {e}")
        
        try:
            self.collectors['web'] = GenericWebCollector()
            logger.info("Generic web collector initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Generic web collector: {e}")
    
    async def collect_all_data(self, 
                             keywords: List[str] = None, 
                             days_back: int = 7,
                             sources: List[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Collect data from all available sources.
        
        Args:
            keywords: List of keywords to search for (default: Gusto-related terms)
            days_back: Number of days back to search
            sources: List of specific sources to use (default: all available)
        
        Returns:
            Dictionary with source names as keys and collected data as values
        """
        if keywords is None:
            keywords = [
                "Gusto payroll", "Gusto HR", "Gusto software", 
                "Gusto review", "Gusto vs", "@gustohq",
                "gusto.com", "Gusto alternatives"
            ]
        
        if sources is None:
            sources = list(self.collectors.keys())
        
        all_data = {}
        
        # Collect data from each source
        for source_name in sources:
            if source_name not in self.collectors:
                logger.warning(f"Unknown source: {source_name}")
                continue
                
            collector = self.collectors[source_name]
            logger.info(f"Starting data collection from {source_name}")
            
            try:
                source_data = await collector.collect_data(keywords, days_back)
                all_data[source_name] = source_data
                logger.info(f"Collected {len(source_data)} items from {source_name}")
            except Exception as e:
                logger.error(f"Error collecting from {source_name}: {e}")
                all_data[source_name] = []
        
        return all_data
    
    def process_and_analyze(self, raw_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Process raw data and perform sentiment analysis.
        
        Args:
            raw_data: Raw data collected from various sources
            
        Returns:
            Processed and analyzed data
        """
        logger.info("Starting data processing and analysis")
        
        # Combine all data
        all_posts = []
        for source, posts in raw_data.items():
            for post in posts:
                post['source'] = source
                all_posts.append(post)
        
        if not all_posts:
            logger.warning("No data to process")
            return {}
        
        # Create DataFrame for analysis
        df = pd.DataFrame(all_posts)
        
        # Perform sentiment analysis
        if 'text' in df.columns:
            df['sentiment'] = df['text'].apply(self.sentiment_analyzer.analyze_sentiment)
            df['sentiment_score'] = df['text'].apply(self.sentiment_analyzer.get_sentiment_score)
        
        # Process data
        processed_data = self.data_processor.process(df)
        
        logger.info("Data processing and analysis completed")
        return processed_data
    
    def generate_reports(self, processed_data: Dict[str, Any], output_dir: str = "reports"):
        """
        Generate various reports from processed data.
        
        Args:
            processed_data: Processed and analyzed data
            output_dir: Directory to save reports
        """
        if not processed_data:
            logger.warning("No processed data available for reporting")
            return
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate reports
        self.report_generator.generate_summary_report(processed_data, output_dir)
        self.report_generator.generate_sentiment_analysis(processed_data, output_dir)
        self.report_generator.generate_source_breakdown(processed_data, output_dir)
        self.report_generator.generate_timeline_analysis(processed_data, output_dir)
        
        logger.info(f"Reports generated in {output_dir}")
    
    async def run_monitoring(self, 
                           keywords: List[str] = None,
                           days_back: int = 7,
                           sources: List[str] = None,
                           output_dir: str = "reports"):
        """
        Run complete monitoring workflow.
        
        Args:
            keywords: Keywords to search for
            days_back: Number of days to look back
            sources: Specific sources to monitor
            output_dir: Output directory for reports
        """
        logger.info("Starting Gusto social media monitoring")
        
        # Collect data
        raw_data = await self.collect_all_data(keywords, days_back, sources)
        
        # Save raw data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        raw_data_file = f"raw_data_{timestamp}.json"
        
        with open(raw_data_file, 'w') as f:
            json.dump(raw_data, f, indent=2, default=str)
        logger.info(f"Raw data saved to {raw_data_file}")
        
        # Process and analyze
        processed_data = self.process_and_analyze(raw_data)
        
        # Generate reports
        self.generate_reports(processed_data, output_dir)
        
        logger.info("Monitoring cycle completed")
        
        return processed_data

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Gusto Social Media Monitoring Tool")
    parser.add_argument("--keywords", nargs="+", help="Keywords to search for")
    parser.add_argument("--days", type=int, default=7, help="Days back to search")
    parser.add_argument("--sources", nargs="+", 
                       choices=["reddit", "google_reviews", "linkedin", "g2", "twitter", "web"],
                       help="Specific sources to monitor")
    parser.add_argument("--output", default="reports", help="Output directory")
    
    args = parser.parse_args()
    
    # Create and run monitor
    monitor = GustoSocialMonitor()
    
    # Run the monitoring
    asyncio.run(monitor.run_monitoring(
        keywords=args.keywords,
        days_back=args.days,
        sources=args.sources,
        output_dir=args.output
    ))

if __name__ == "__main__":
    main() 