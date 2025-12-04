import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter

from utils.sentiment_analyzer import SentimentAnalyzer
from utils.theme_extractor import ThemeExtractor
from backend.database.database import get_session
from backend.database.models import (
    SocialMediaPost, Theme, PostTheme, Keyword, PostKeyword,
    SentimentTrend, CompetitorMention, DataCollection
)

logger = logging.getLogger(__name__)

class DataProcessor:
    """Processes and analyzes collected social media data."""
    
    def __init__(self):
        """Initialize data processor with analysis tools."""
        self.sentiment_analyzer = SentimentAnalyzer()
        self.theme_extractor = ThemeExtractor()
        
        # Competitor keywords for detection
        self.competitors = [
            'adp', 'paychex', 'quickbooks payroll', 'bamboohr', 'workday',
            'zenefits', 'namely', 'rippling', 'justworks', 'square payroll'
        ]
    
    def process(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Process the collected data with sentiment and theme analysis.
        
        Args:
            df: DataFrame with collected social media data
            
        Returns:
            Dictionary with processed and analyzed data
        """
        if df.empty:
            logger.warning("No data to process")
            return {}
        
        logger.info(f"Processing {len(df)} posts/comments")
        
        try:
            # Ensure required columns exist
            if 'text' not in df.columns:
                logger.error("Required 'text' column not found in data")
                return {}
            
            # Clean and prepare data
            df = self._clean_data(df)
            
            # Perform sentiment analysis
            df = self._analyze_sentiment(df)
            
            # Extract themes
            theme_analysis = self._analyze_themes(df)
            
            # Detect competitor mentions
            df = self._detect_competitors(df)
            
            # Calculate metrics
            metrics = self._calculate_metrics(df)
            
            # Store in database
            self._store_to_database(df, theme_analysis)
            
            # Create summary
            summary = self._create_summary(df, theme_analysis, metrics)
            
            return summary
            
        except Exception as e:
            logger.error(f"Error processing data: {e}")
            return {}
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and normalize the data.
        
        Args:
            df: Raw DataFrame
            
        Returns:
            Cleaned DataFrame
        """
        # Remove duplicates based on platform and post ID
        if 'id' in df.columns and 'platform' in df.columns:
            df = df.drop_duplicates(subset=['platform', 'id'])
        
        # Ensure datetime columns
        if 'created_at' in df.columns:
            # Handle multiple date formats
            df['created_at'] = pd.to_datetime(df['created_at'], format='mixed', errors='coerce')
        
        # Fill missing values
        df['text'] = df['text'].fillna('')
        df['title'] = df.get('title', '').fillna('')
        df['author'] = df.get('author', '').fillna('Unknown')
        
        # Create combined text for analysis
        df['combined_text'] = (df['title'].astype(str) + ' ' + df['text'].astype(str)).str.strip()
        
        # Filter out very short texts
        df = df[df['combined_text'].str.len() > 10]
        
        logger.info(f"Data cleaned. {len(df)} posts remain after cleaning")
        return df
    
    def _analyze_sentiment(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Perform sentiment analysis on the data.
        
        Args:
            df: DataFrame with text data
            
        Returns:
            DataFrame with sentiment analysis results
        """
        logger.info("Performing sentiment analysis")
        
        # Analyze sentiment for each text
        sentiment_results = []
        for text in df['combined_text']:
            result = self.sentiment_analyzer.analyze_detailed_sentiment(text)
            sentiment_results.append(result)
        
        # Add sentiment results to DataFrame
        df['sentiment_label'] = [r['sentiment_label'] for r in sentiment_results]
        df['sentiment_score'] = [r['sentiment_score'] for r in sentiment_results]
        df['sentiment_confidence'] = [r['confidence'] for r in sentiment_results]
        df['aspects_mentioned'] = [r['aspects'] for r in sentiment_results]
        
        logger.info("Sentiment analysis completed")
        return df
    
    def _analyze_themes(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Perform theme analysis on the data.
        
        Args:
            df: DataFrame with text data
            
        Returns:
            Theme analysis results
        """
        logger.info("Performing theme analysis")
        
        # Get all texts for theme analysis
        texts = df['combined_text'].tolist()
        
        # Perform comprehensive theme analysis
        theme_analysis = self.theme_extractor.analyze_themes(texts)
        
        # Add individual theme scores to DataFrame
        theme_scores_list = []
        for text in texts:
            theme_scores = self.theme_extractor.classify_predefined_themes(text)
            theme_scores_list.append(theme_scores)
        
        # Add theme information to DataFrame
        for theme_name in self.theme_extractor.predefined_themes.keys():
            df[f'theme_{theme_name}'] = [scores.get(theme_name, 0) for scores in theme_scores_list]
        
        logger.info("Theme analysis completed")
        return theme_analysis
    
    def _detect_competitors(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect mentions of competitors in the data.
        
        Args:
            df: DataFrame with text data
            
        Returns:
            DataFrame with competitor information
        """
        logger.info("Detecting competitor mentions")
        
        competitor_mentions = []
        for text in df['combined_text']:
            text_lower = text.lower()
            mentioned_competitors = [comp for comp in self.competitors if comp in text_lower]
            competitor_mentions.append(mentioned_competitors)
        
        df['competitors_mentioned'] = competitor_mentions
        df['has_competitor_mention'] = df['competitors_mentioned'].apply(lambda x: len(x) > 0)
        
        logger.info(f"Competitor detection completed. Found {df['has_competitor_mention'].sum()} posts with competitor mentions")
        return df
    
    def _calculate_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate various metrics from the processed data.
        
        Args:
            df: Processed DataFrame
            
        Returns:
            Dictionary with calculated metrics
        """
        metrics = {}
        
        # Basic counts
        metrics['total_posts'] = len(df)
        metrics['platforms'] = df['platform'].value_counts().to_dict()
        
        # Sentiment metrics
        sentiment_counts = df['sentiment_label'].value_counts().to_dict()
        metrics['sentiment_breakdown'] = sentiment_counts
        metrics['avg_sentiment_score'] = df['sentiment_score'].mean()
        
        # Engagement metrics (if available)
        if 'score' in df.columns:
            metrics['avg_engagement'] = df['score'].mean()
            metrics['total_engagement'] = df['score'].sum()
        
        # Time-based metrics
        if 'created_at' in df.columns:
            df['date'] = df['created_at'].dt.date
            daily_counts = df['date'].value_counts().sort_index().to_dict()
            metrics['daily_post_counts'] = {str(k): v for k, v in daily_counts.items()}
        
        # Theme metrics
        theme_columns = [col for col in df.columns if col.startswith('theme_')]
        if theme_columns:
            theme_averages = {}
            for col in theme_columns:
                theme_name = col.replace('theme_', '')
                theme_averages[theme_name] = df[col].mean()
            metrics['avg_theme_scores'] = theme_averages
        
        # Competitor metrics
        if 'has_competitor_mention' in df.columns:
            metrics['competitor_mention_rate'] = df['has_competitor_mention'].mean()
            metrics['posts_with_competitors'] = df['has_competitor_mention'].sum()
        
        return metrics
    
    def _store_to_database(self, df: pd.DataFrame, theme_analysis: Dict[str, Any]):
        """
        Store processed data to the database.
        
        Args:
            df: Processed DataFrame
            theme_analysis: Theme analysis results
        """
        logger.info("Storing data to database")
        
        try:
            with get_session() as session:
                # Store themes first
                theme_map = self._store_themes(session, theme_analysis)
                
                # Store posts
                post_ids = self._store_posts(session, df)
                
                # Store post-theme relationships
                self._store_post_themes(session, df, post_ids, theme_map)
                
                # Store keywords
                keyword_map = self._store_keywords(session, theme_analysis)
                
                # Store post-keyword relationships
                self._store_post_keywords(session, df, post_ids, keyword_map)
                
                # Store competitor mentions
                self._store_competitor_mentions(session, df, post_ids)
                
                logger.info("Data successfully stored to database")
                
        except Exception as e:
            logger.error(f"Error storing data to database: {e}")
    
    def _store_themes(self, session, theme_analysis: Dict[str, Any]) -> Dict[str, int]:
        """Store themes in database and return theme name to ID mapping."""
        theme_map = {}
        
        if 'predefined_themes' in theme_analysis:
            themes_data = theme_analysis['predefined_themes']
            if 'descriptions' in themes_data:
                for theme_name, description in themes_data['descriptions'].items():
                    # Check if theme already exists
                    existing_theme = session.query(Theme).filter_by(name=theme_name).first()
                    
                    if not existing_theme:
                        theme = Theme(
                            name=theme_name,
                            description=description,
                            category='predefined'
                        )
                        session.add(theme)
                        session.flush()
                        theme_map[theme_name] = theme.id
                    else:
                        theme_map[theme_name] = existing_theme.id
        
        return theme_map
    
    def _store_posts(self, session, df: pd.DataFrame) -> Dict[str, int]:
        """Store posts in database and return post external ID to internal ID mapping."""
        post_ids = {}
        
        for _, row in df.iterrows():
            # Handle different data formats (post_id vs id)
            external_post_id = row.get('post_id') or row.get('id')
            
            # Check if post already exists
            existing_post = session.query(SocialMediaPost).filter_by(
                platform=row['platform'],
                post_id=external_post_id
            ).first()
            
            if not existing_post:
                post = SocialMediaPost(
                    platform=row['platform'],
                    post_id=external_post_id,
                    title=row.get('title', ''),
                    content=row['text'],
                    author=row.get('author', ''),
                    url=row.get('url', ''),
                    created_at=row.get('created_at', datetime.now()),
                    upvotes=row.get('upvotes', 0),
                    downvotes=row.get('downvotes', 0),
                    likes=row.get('likes', 0),
                    shares=row.get('shares', 0),
                    comments_count=row.get('comments_count', 0),
                    sentiment_score=row.get('sentiment_score', 0),
                    sentiment_label=row.get('sentiment_label', 'neutral'),
                    confidence_score=row.get('sentiment_confidence', 0),
                    is_processed=True,
                    raw_data=row.get('raw_data', {})
                )
                session.add(post)
                session.flush()
                post_ids[external_post_id] = post.id
            else:
                post_ids[external_post_id] = existing_post.id
        
        return post_ids
    
    def _store_post_themes(self, session, df: pd.DataFrame, post_ids: Dict[str, int], theme_map: Dict[str, int]):
        """Store post-theme relationships."""
        theme_columns = [col for col in df.columns if col.startswith('theme_')]
        
        for _, row in df.iterrows():
            external_post_id = row.get('post_id') or row.get('id')
            post_internal_id = post_ids[external_post_id]
            
            for col in theme_columns:
                theme_name = col.replace('theme_', '')
                if theme_name in theme_map:
                    relevance_score = row[col]
                    
                    if relevance_score > 0:  # Only store non-zero relevance scores
                        post_theme = PostTheme(
                            post_id=post_internal_id,
                            theme_id=theme_map[theme_name],
                            relevance_score=relevance_score,
                            confidence=row.get('sentiment_confidence', 0)
                        )
                        session.add(post_theme)
    
    def _store_keywords(self, session, theme_analysis: Dict[str, Any]) -> Dict[str, int]:
        """Store keywords and return keyword to ID mapping."""
        keyword_map = {}
        
        if 'top_keywords' in theme_analysis:
            for keyword, score in theme_analysis['top_keywords']:
                # Check if keyword already exists
                existing_keyword = session.query(Keyword).filter_by(word=keyword).first()
                
                if not existing_keyword:
                    keyword_obj = Keyword(
                        word=keyword,
                        category='extracted',
                        is_active=True
                    )
                    session.add(keyword_obj)
                    session.flush()
                    keyword_map[keyword] = keyword_obj.id
                else:
                    keyword_map[keyword] = existing_keyword.id
        
        return keyword_map
    
    def _store_post_keywords(self, session, df: pd.DataFrame, post_ids: Dict[str, int], keyword_map: Dict[str, int]):
        """Store post-keyword relationships."""
        for _, row in df.iterrows():
            external_post_id = row.get('post_id') or row.get('id')
            post_internal_id = post_ids[external_post_id]
            text = row['combined_text'].lower()
            
            for keyword, keyword_id in keyword_map.items():
                if keyword in text:
                    mention_count = text.count(keyword)
                    
                    post_keyword = PostKeyword(
                        post_id=post_internal_id,
                        keyword_id=keyword_id,
                        mention_count=mention_count,
                        context=text[:200]  # Store first 200 chars as context
                    )
                    session.add(post_keyword)
    
    def _store_competitor_mentions(self, session, df: pd.DataFrame, post_ids: Dict[str, int]):
        """Store competitor mentions."""
        for _, row in df.iterrows():
            if row.get('has_competitor_mention', False):
                external_post_id = row.get('post_id') or row.get('id')
                post_internal_id = post_ids[external_post_id]
                
                for competitor in row['competitors_mentioned']:
                    # Determine sentiment towards competitor
                    competitor_sentiment = self.sentiment_analyzer.get_sentiment_score(
                        f"competitor {competitor} " + row['combined_text']
                    )
                    
                    mention = CompetitorMention(
                        post_id=post_internal_id,
                        competitor_name=competitor,
                        mention_type='comparison',
                        context=row['combined_text'][:500],
                        sentiment_towards_competitor=competitor_sentiment
                    )
                    session.add(mention)
    
    def _create_summary(self, df: pd.DataFrame, theme_analysis: Dict[str, Any], metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a comprehensive summary of the processed data.
        
        Args:
            df: Processed DataFrame
            theme_analysis: Theme analysis results
            metrics: Calculated metrics
            
        Returns:
            Summary dictionary
        """
        summary = {
            'overview': {
                'total_posts': metrics['total_posts'],
                'platforms': metrics['platforms'],
                'date_range': {
                    'start': df['created_at'].min().isoformat() if 'created_at' in df.columns else None,
                    'end': df['created_at'].max().isoformat() if 'created_at' in df.columns else None
                },
                'avg_sentiment_score': round(metrics['avg_sentiment_score'], 3)
            },
            'sentiment_analysis': {
                'breakdown': metrics['sentiment_breakdown'],
                'distribution': {
                    'positive_pct': round(metrics['sentiment_breakdown'].get('positive', 0) / metrics['total_posts'] * 100, 1),
                    'negative_pct': round(metrics['sentiment_breakdown'].get('negative', 0) / metrics['total_posts'] * 100, 1),
                    'neutral_pct': round(metrics['sentiment_breakdown'].get('neutral', 0) / metrics['total_posts'] * 100, 1)
                }
            },
            'theme_analysis': self.theme_extractor.get_theme_summary(theme_analysis),
            'competitive_landscape': {
                'posts_with_competitor_mentions': metrics.get('posts_with_competitors', 0),
                'competitor_mention_rate': round(metrics.get('competitor_mention_rate', 0) * 100, 1)
            },
            'engagement_metrics': {
                'avg_engagement': metrics.get('avg_engagement', 0),
                'total_engagement': metrics.get('total_engagement', 0)
            },
            'temporal_trends': {
                'daily_post_counts': metrics.get('daily_post_counts', {})
            },
            'data_quality': {
                'posts_processed': len(df),
                'avg_text_length': df['combined_text'].str.len().mean(),
                'avg_sentiment_confidence': df['sentiment_confidence'].mean()
            }
        }
        
        return summary 