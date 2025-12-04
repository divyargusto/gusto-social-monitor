import os
import praw
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import time

logger = logging.getLogger(__name__)

@dataclass
class RedditPost:
    """Data class for Reddit post information."""
    id: str
    title: str
    content: str
    author: str
    url: str
    created_at: datetime
    subreddit: str
    score: int
    num_comments: int
    upvote_ratio: float
    permalink: str
    is_self: bool

@dataclass
class RedditComment:
    """Data class for Reddit comment information."""
    id: str
    content: str
    author: str
    created_at: datetime
    score: int
    parent_id: str
    post_id: str
    permalink: str

class RedditCollector:
    """Collector for Reddit posts and comments mentioning Gusto."""
    
    def __init__(self):
        """Initialize Reddit API client."""
        self.reddit = None
        self.rate_limit_delay = 1  # seconds between API calls
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Reddit API client with credentials."""
        try:
            # Get credentials from environment variables
            client_id = os.getenv('REDDIT_CLIENT_ID')
            client_secret = os.getenv('REDDIT_CLIENT_SECRET')
            user_agent = os.getenv('REDDIT_USER_AGENT', 'GustoSocialMonitor/1.0')
            username = os.getenv('REDDIT_USERNAME')
            password = os.getenv('REDDIT_PASSWORD')
            
            if not all([client_id, client_secret]):
                logger.warning("Reddit API credentials not found in environment variables")
                return
            
            # Initialize Reddit instance
            self.reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent,
                username=username,
                password=password
            )
            
            # Test the connection
            logger.info(f"Reddit API initialized. Read-only: {self.reddit.read_only}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Reddit API: {e}")
            self.reddit = None
    
    def _extract_post_data(self, submission) -> RedditPost:
        """
        Extract relevant data from a Reddit submission.
        
        Args:
            submission: PRAW submission object
            
        Returns:
            RedditPost: Extracted post data
        """
        return RedditPost(
            id=submission.id,
            title=submission.title or "",
            content=submission.selftext or "",
            author=str(submission.author) if submission.author else "[deleted]",
            url=submission.url,
            created_at=datetime.fromtimestamp(submission.created_utc),
            subreddit=str(submission.subreddit),
            score=submission.score,
            num_comments=submission.num_comments,
            upvote_ratio=submission.upvote_ratio,
            permalink=f"https://reddit.com{submission.permalink}",
            is_self=submission.is_self
        )
    
    def _extract_comment_data(self, comment, post_id: str) -> Optional[RedditComment]:
        """
        Extract relevant data from a Reddit comment.
        
        Args:
            comment: PRAW comment object
            post_id: ID of the parent post
            
        Returns:
            RedditComment: Extracted comment data, None if comment is deleted/removed
        """
        try:
            if comment.body in ['[deleted]', '[removed]']:
                return None
                
            return RedditComment(
                id=comment.id,
                content=comment.body,
                author=str(comment.author) if comment.author else "[deleted]",
                created_at=datetime.fromtimestamp(comment.created_utc),
                score=comment.score,
                parent_id=comment.parent_id,
                post_id=post_id,
                permalink=f"https://reddit.com{comment.permalink}"
            )
        except Exception as e:
            logger.warning(f"Error extracting comment data: {e}")
            return None
    
    async def search_subreddit(self, 
                             subreddit_name: str, 
                             keywords: List[str], 
                             days_back: int = 7,
                             limit: int = 100) -> List[Dict[str, Any]]:
        """
        Search a specific subreddit for posts containing keywords.
        
        Args:
            subreddit_name: Name of the subreddit to search
            keywords: List of keywords to search for
            days_back: Number of days to look back
            limit: Maximum number of posts to retrieve
            
        Returns:
            List of posts and comments
        """
        if not self.reddit:
            logger.error("Reddit API not initialized")
            return []
        
        results = []
        search_query = " OR ".join(keywords)
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            
            # Search posts
            time_filter = 'week' if days_back <= 7 else 'month' if days_back <= 30 else 'year'
            for submission in subreddit.search(search_query, 
                                             sort='new', 
                                             time_filter=time_filter,
                                             limit=limit):
                
                # Check if post is within date range
                post_date = datetime.fromtimestamp(submission.created_utc)
                cutoff_date = datetime.now() - timedelta(days=days_back)
                
                if post_date < cutoff_date:
                    continue
                
                post_data = self._extract_post_data(submission)
                
                # Convert to dict for consistency with main.py
                post_dict = {
                    'id': post_data.id,
                    'platform': 'reddit',
                    'type': 'post',
                    'text': f"{post_data.title} {post_data.content}".strip(),
                    'title': post_data.title,
                    'content': post_data.content,
                    'author': post_data.author,
                    'url': post_data.url,
                    'permalink': post_data.permalink,
                    'created_at': post_data.created_at,
                    'subreddit': post_data.subreddit,
                    'score': post_data.score,
                    'upvotes': max(0, int(post_data.score * post_data.upvote_ratio)),
                    'downvotes': max(0, int(post_data.score * (1 - post_data.upvote_ratio))),
                    'comments_count': post_data.num_comments,
                    'upvote_ratio': post_data.upvote_ratio,
                    'is_self': post_data.is_self,
                    'raw_data': {
                        'reddit_id': post_data.id,
                        'subreddit': post_data.subreddit,
                        'upvote_ratio': post_data.upvote_ratio
                    }
                }
                
                results.append(post_dict)
                
                # Collect comments if the post has any
                if post_data.num_comments > 0:
                    await self._collect_comments(submission, post_data.id, keywords, results)
                
                # Rate limiting
                await asyncio.sleep(self.rate_limit_delay)
                
        except Exception as e:
            logger.error(f"Error searching subreddit {subreddit_name}: {e}")
        
        return results
    
    async def _collect_comments(self, 
                              submission, 
                              post_id: str, 
                              keywords: List[str], 
                              results: List[Dict[str, Any]]):
        """
        Collect comments from a submission that mention keywords.
        
        Args:
            submission: PRAW submission object
            post_id: ID of the parent post
            keywords: Keywords to search for in comments
            results: List to append comment data to
        """
        try:
            # Expand all comments
            submission.comments.replace_more(limit=0)
            
            for comment in submission.comments.list():
                if not hasattr(comment, 'body') or comment.body in ['[deleted]', '[removed]']:
                    continue
                
                # Check if comment contains any keywords (case-insensitive)
                comment_text = comment.body.lower()
                if any(keyword.lower() in comment_text for keyword in keywords):
                    comment_data = self._extract_comment_data(comment, post_id)
                    
                    if comment_data:
                        comment_dict = {
                            'id': comment_data.id,
                            'platform': 'reddit',
                            'type': 'comment',
                            'text': comment_data.content,
                            'content': comment_data.content,
                            'author': comment_data.author,
                            'url': comment_data.permalink,
                            'permalink': comment_data.permalink,
                            'created_at': comment_data.created_at,
                            'score': comment_data.score,
                            'upvotes': max(0, comment_data.score),
                            'downvotes': 0,  # Reddit doesn't provide comment downvotes
                            'parent_id': comment_data.parent_id,
                            'post_id': comment_data.post_id,
                            'raw_data': {
                                'reddit_id': comment_data.id,
                                'parent_id': comment_data.parent_id,
                                'post_id': comment_data.post_id
                            }
                        }
                        
                        results.append(comment_dict)
                        
        except Exception as e:
            logger.warning(f"Error collecting comments for post {post_id}: {e}")
    
    async def collect_data(self, 
                         keywords: List[str], 
                         days_back: int = 7) -> List[Dict[str, Any]]:
        """
        Collect Reddit data for given keywords.
        
        Args:
            keywords: List of keywords to search for
            days_back: Number of days to look back
            
        Returns:
            List of collected posts and comments
        """
        if not self.reddit:
            logger.error("Reddit API not initialized")
            return []
        
        logger.info(f"Starting Reddit data collection for keywords: {keywords}")
        
        all_results = []
        
        # Focused subreddits - only the 3 most relevant for Gusto mentions
        target_subreddits = [
            'smallbusiness',
            'Entrepreneurship',
            'Payroll'
        ]
        
        for subreddit_name in target_subreddits:
            try:
                logger.info(f"Searching subreddit: r/{subreddit_name}")
                # Increase limit for longer time periods
                search_limit = 50 if days_back <= 30 else 100 if days_back <= 90 else 200
                subreddit_results = await self.search_subreddit(
                    subreddit_name, 
                    keywords, 
                    days_back,
                    limit=search_limit
                )
                
                all_results.extend(subreddit_results)
                logger.info(f"Found {len(subreddit_results)} items in r/{subreddit_name}")
                
                # Rate limiting between subreddits
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error processing subreddit r/{subreddit_name}: {e}")
                continue
        
        logger.info(f"Reddit collection completed. Total items: {len(all_results)}")
        return all_results 