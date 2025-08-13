import os
import json
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import pandas as pd
from sqlalchemy import func, desc
from sqlalchemy.orm import joinedload

from backend.database.database import init_database, get_session
from backend.database.models import (
    SocialMediaPost, Theme, PostTheme, Keyword, PostKeyword,
    SentimentTrend, CompetitorMention, DataCollection
)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')
CORS(app)

# Initialize database
try:
    init_database()
except Exception as e:
    print(f"Database initialization warning: {e}")

@app.route('/')
def index():
    """Serve the main dashboard page."""
    return render_template('index.html')

@app.route('/api/overview')
def api_overview():
    """Get overview statistics."""
    try:
        with get_session() as session:
            # Basic counts - Reddit only
            total_posts = session.query(SocialMediaPost).filter(SocialMediaPost.platform == 'reddit').count()
            
            # Platform breakdown - Reddit only
            platform_counts = session.query(
                SocialMediaPost.platform,
                func.count(SocialMediaPost.id).label('count')
            ).filter(SocialMediaPost.platform == 'reddit').group_by(SocialMediaPost.platform).all()
            
            platforms = {platform: count for platform, count in platform_counts}
            
            # Sentiment breakdown - Reddit only
            sentiment_counts = session.query(
                SocialMediaPost.sentiment_label,
                func.count(SocialMediaPost.id).label('count')
            ).filter(SocialMediaPost.platform == 'reddit').group_by(SocialMediaPost.sentiment_label).all()
            
            sentiment_breakdown = {sentiment: count for sentiment, count in sentiment_counts}
            
            # Average sentiment score - Reddit only
            avg_sentiment = session.query(
                func.avg(SocialMediaPost.sentiment_score)
            ).filter(SocialMediaPost.platform == 'reddit').scalar() or 0
            
            # Recent activity (last 7 days) - Reddit only
            week_ago = datetime.now() - timedelta(days=7)
            recent_posts = session.query(SocialMediaPost).filter(
                SocialMediaPost.created_at >= week_ago,
                SocialMediaPost.platform == 'reddit'
            ).count()
            
            return jsonify({
                'total_posts': total_posts,
                'platforms': platforms,
                'sentiment_breakdown': sentiment_breakdown,
                'avg_sentiment_score': round(avg_sentiment, 3),
                'recent_posts_7_days': recent_posts,
                'last_updated': datetime.now().isoformat()
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sentiment-trends')
def api_sentiment_trends():
    """Get sentiment trends over time."""
    try:
        days = request.args.get('days', 30, type=int)
        start_date = datetime.now() - timedelta(days=days)
        
        with get_session() as session:
            # Daily sentiment data - Reddit only
            daily_sentiment = session.query(
                func.date(SocialMediaPost.created_at).label('date'),
                func.avg(SocialMediaPost.sentiment_score).label('avg_sentiment'),
                func.count(SocialMediaPost.id).label('post_count'),
                func.count().filter(SocialMediaPost.sentiment_label == 'positive').label('positive_count'),
                func.count().filter(SocialMediaPost.sentiment_label == 'negative').label('negative_count'),
                func.count().filter(SocialMediaPost.sentiment_label == 'neutral').label('neutral_count')
            ).filter(
                SocialMediaPost.created_at >= start_date,
                SocialMediaPost.platform == 'reddit'
            ).group_by(
                func.date(SocialMediaPost.created_at)
            ).order_by('date').all()
            
            trends = []
            for row in daily_sentiment:
                # Convert date to string if it's not already
                date_str = str(row.date) if hasattr(row.date, 'isoformat') else row.date
                trends.append({
                    'date': date_str,
                    'avg_sentiment': round(row.avg_sentiment or 0, 3),
                    'post_count': row.post_count,
                    'positive_count': row.positive_count,
                    'negative_count': row.negative_count,
                    'neutral_count': row.neutral_count
                })
            
            return jsonify({'trends': trends})
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/themes')
def api_themes():
    """Get theme analysis data."""
    try:
        with get_session() as session:
            # Top themes with sentiment breakdown from Reddit posts only
            top_themes_base = session.query(
                Theme.id,
                Theme.name,
                Theme.description,
                Theme.category,
                func.count(PostTheme.id).label('total_mentions')
            ).select_from(Theme).join(PostTheme, Theme.id == PostTheme.theme_id).join(
                SocialMediaPost, PostTheme.post_id == SocialMediaPost.id
            ).filter(
                SocialMediaPost.platform == 'reddit'
            ).group_by(
                Theme.id, Theme.name, Theme.description, Theme.category
            ).order_by(desc('total_mentions')).limit(10).all()
            
            themes = []
            for theme in top_themes_base:
                # Get sentiment breakdown for this theme
                sentiment_counts = session.query(
                    SocialMediaPost.sentiment_label,
                    func.count(PostTheme.id).label('count')
                ).select_from(PostTheme).join(
                    SocialMediaPost, PostTheme.post_id == SocialMediaPost.id
                ).filter(
                    PostTheme.theme_id == theme.id,
                    SocialMediaPost.platform == 'reddit'
                ).group_by(SocialMediaPost.sentiment_label).all()
                
                # Convert to dictionary with default values
                sentiment_breakdown = {'positive': 0, 'negative': 0, 'neutral': 0}
                for sentiment, count in sentiment_counts:
                    if sentiment in sentiment_breakdown:
                        sentiment_breakdown[sentiment] = count
                
                themes.append({
                    'name': theme.name.replace('_', ' ').title(),
                    'description': theme.description,
                    'category': theme.category,
                    'total_mentions': theme.total_mentions,
                    'positive_count': sentiment_breakdown['positive'],
                    'negative_count': sentiment_breakdown['negative'],
                    'neutral_count': sentiment_breakdown['neutral']
                })
            
            # Theme sentiment correlation - Reddit only
            theme_sentiment = session.query(
                Theme.name,
                func.avg(SocialMediaPost.sentiment_score).label('avg_sentiment')
            ).select_from(Theme).join(PostTheme, Theme.id == PostTheme.theme_id).join(
                SocialMediaPost, PostTheme.post_id == SocialMediaPost.id
            ).filter(
                SocialMediaPost.platform == 'reddit'
            ).group_by(
                Theme.id, Theme.name
            ).all()
            
            sentiment_by_theme = {
                theme.name.replace('_', ' ').title(): round(theme.avg_sentiment or 0, 3)
                for theme in theme_sentiment
            }
            
            return jsonify({
                'top_themes': themes,
                'sentiment_by_theme': sentiment_by_theme
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/keywords')
def api_keywords():
    """Get top keywords and their frequencies."""
    try:
        with get_session() as session:
            # Top keywords by mention count
            top_keywords = session.query(
                Keyword.word,
                Keyword.category,
                func.sum(PostKeyword.mention_count).label('total_mentions'),
                func.count(PostKeyword.post_id.distinct()).label('unique_posts')
            ).join(PostKeyword).group_by(
                Keyword.id, Keyword.word, Keyword.category
            ).order_by(desc('total_mentions')).limit(20).all()
            
            keywords = []
            for keyword in top_keywords:
                keywords.append({
                    'word': keyword.word,
                    'category': keyword.category,
                    'total_mentions': keyword.total_mentions,
                    'unique_posts': keyword.unique_posts
                })
            
            return jsonify({'keywords': keywords})
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/competitors')
def api_competitors():
    """Get competitor mention analysis."""
    try:
        with get_session() as session:
            # Competitor mentions
            competitor_data = session.query(
                CompetitorMention.competitor_name,
                func.count(CompetitorMention.id).label('mention_count'),
                func.avg(CompetitorMention.sentiment_towards_competitor).label('avg_sentiment')
            ).group_by(CompetitorMention.competitor_name).order_by(
                desc('mention_count')
            ).all()
            
            competitors = []
            for comp in competitor_data:
                competitors.append({
                    'name': comp.competitor_name,
                    'mention_count': comp.mention_count,
                    'avg_sentiment': round(comp.avg_sentiment or 0, 3)
                })
            
            return jsonify({'competitors': competitors})
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/posts')
def api_posts():
    """Get recent posts with pagination."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        platform = request.args.get('platform', None)
        sentiment = request.args.get('sentiment', None)
        
        with get_session() as session:
            query = session.query(SocialMediaPost).options(
                joinedload(SocialMediaPost.themes).joinedload(PostTheme.theme)
            )
            
            # Show only Reddit posts - exclude all other platforms
            query = query.filter(SocialMediaPost.platform == 'reddit')
            
            # Apply filters
            if platform:
                query = query.filter(SocialMediaPost.platform == platform)
            if sentiment:
                query = query.filter(SocialMediaPost.sentiment_label == sentiment)
            
            # Pagination
            offset = (page - 1) * per_page
            posts = query.order_by(desc(SocialMediaPost.created_at)).offset(offset).limit(per_page).all()
            
            total_count = query.count()
            
            posts_data = []
            for post in posts:
                # Get themes for this post
                themes = [pt.theme.name.replace('_', ' ').title() for pt in post.themes if pt.relevance_score > 0]
                
                posts_data.append({
                    'id': post.id,
                    'platform': post.platform,
                    'title': post.title or '',
                    'content': post.content[:200] + '...' if len(post.content) > 200 else post.content,
                    'author': post.author,
                    'url': post.url,
                    'created_at': post.created_at.isoformat() if post.created_at else None,
                    'sentiment_label': post.sentiment_label,
                    'sentiment_score': round(post.sentiment_score or 0, 3),
                    'confidence_score': round(post.confidence_score or 0, 3),
                    'upvotes': post.upvotes,
                    'comments_count': post.comments_count,
                    'themes': themes
                })
            
            return jsonify({
                'posts': posts_data,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total_count,
                    'pages': (total_count + per_page - 1) // per_page
                }
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/platform-analysis')
def api_platform_analysis():
    """Get platform-specific analysis."""
    try:
        with get_session() as session:
            # Platform sentiment comparison - Reddit only
            platform_sentiment = session.query(
                SocialMediaPost.platform,
                func.avg(SocialMediaPost.sentiment_score).label('avg_sentiment'),
                func.count(SocialMediaPost.id).label('post_count'),
                func.avg(SocialMediaPost.upvotes).label('avg_engagement')
            ).filter(SocialMediaPost.platform == 'reddit').group_by(SocialMediaPost.platform).all()
            
            platforms = []
            for platform in platform_sentiment:
                platforms.append({
                    'platform': platform.platform,
                    'avg_sentiment': round(platform.avg_sentiment or 0, 3),
                    'post_count': platform.post_count,
                    'avg_engagement': round(platform.avg_engagement or 0, 1)
                })
            
            return jsonify({'platforms': platforms})
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export')
def api_export():
    """Export data in various formats."""
    try:
        format_type = request.args.get('format', 'json')
        days = request.args.get('days', 30, type=int)
        
        start_date = datetime.now() - timedelta(days=days)
        
        with get_session() as session:
            posts = session.query(SocialMediaPost).filter(
                SocialMediaPost.created_at >= start_date,
                SocialMediaPost.platform == 'reddit'
            ).all()
            
            data = []
            for post in posts:
                data.append({
                    'platform': post.platform,
                    'post_id': post.post_id,
                    'title': post.title,
                    'content': post.content,
                    'author': post.author,
                    'url': post.url,
                    'created_at': post.created_at.isoformat() if post.created_at else None,
                    'sentiment_label': post.sentiment_label,
                    'sentiment_score': post.sentiment_score,
                    'confidence_score': post.confidence_score,
                    'upvotes': post.upvotes,
                    'downvotes': post.downvotes,
                    'comments_count': post.comments_count
                })
            
            if format_type == 'csv':
                df = pd.DataFrame(data)
                csv_data = df.to_csv(index=False)
                return csv_data, 200, {'Content-Type': 'text/csv'}
            else:
                return jsonify({'data': data})
                
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# YouTube functionality has been removed - focusing on Reddit only

@app.route('/api/posts-by-theme')
def api_posts_by_theme():
    """Get posts filtered by theme and sentiment."""
    try:
        theme_name = request.args.get('theme')
        sentiment = request.args.get('sentiment')
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        if not theme_name or not sentiment:
            return jsonify({'error': 'Both theme and sentiment parameters are required'}), 400
        
        with get_session() as session:
            # Build query to get posts by theme and sentiment
            query = session.query(SocialMediaPost).join(
                PostTheme, SocialMediaPost.id == PostTheme.post_id
            ).join(
                Theme, PostTheme.theme_id == Theme.id
            ).filter(
                SocialMediaPost.platform == 'reddit',
                Theme.name == theme_name.lower().replace(' ', '_'),
                SocialMediaPost.sentiment_label == sentiment
            ).order_by(desc(SocialMediaPost.collected_at))
            
            # Apply pagination
            total = query.count()
            posts = query.offset((page - 1) * per_page).limit(per_page).all()
            
            posts_data = []
            for post in posts:
                # Extract subreddit from raw_data if available
                subreddit = 'Unknown'
                if post.raw_data and isinstance(post.raw_data, dict):
                    subreddit = post.raw_data.get('subreddit', 'Unknown')
                
                posts_data.append({
                    'id': post.id,
                    'title': post.title or 'No title',
                    'content': post.content[:300] + '...' if len(post.content) > 300 else post.content,
                    'sentiment_label': post.sentiment_label,
                    'sentiment_score': round(post.sentiment_score or 0, 3),
                    'upvotes': post.upvotes,
                    'subreddit': subreddit,
                    'author': post.author or 'Unknown',
                    'url': post.url,
                    'collected_at': post.collected_at.isoformat() if post.collected_at else None
                })
            
            return jsonify({
                'posts': posts_data,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page
                },
                'filter': {
                    'theme': theme_name,
                    'sentiment': sentiment
                }
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/competitor-analysis')
def api_competitor_analysis():
    """Get competitive sentiment analysis comparing Gusto vs a competitor for a specific theme."""
    try:
        competitor = request.args.get('competitor')
        theme = request.args.get('theme')
        
        if not competitor or not theme:
            return jsonify({'error': 'Both competitor and theme parameters are required'}), 400
        
        # Valid competitors
        valid_competitors = ['adp', 'paychex', 'quickbooks', 'bamboohr', 'rippling', 'workday', 'deel', 'justworks']
        if competitor not in valid_competitors:
            return jsonify({'error': f'Invalid competitor. Must be one of: {valid_competitors}'}), 400
        
        with get_session() as session:
            from utils.sentiment_analyzer import SentimentAnalyzer
            sentiment_analyzer = SentimentAnalyzer()
            
            # Get Gusto posts for the theme
            gusto_query = session.query(SocialMediaPost).join(
                PostTheme, SocialMediaPost.id == PostTheme.post_id
            ).join(
                Theme, PostTheme.theme_id == Theme.id
            ).filter(
                SocialMediaPost.platform == 'reddit',
                Theme.name == theme.lower().replace(' ', '_'),
                SocialMediaPost.content.contains('gusto')
            )
            
            gusto_posts = gusto_query.all()
            
            # Get competitor posts for the theme
            competitor_query = session.query(SocialMediaPost).join(
                CompetitorMention, SocialMediaPost.id == CompetitorMention.post_id
            ).join(
                PostTheme, SocialMediaPost.id == PostTheme.post_id
            ).join(
                Theme, PostTheme.theme_id == Theme.id
            ).filter(
                SocialMediaPost.platform == 'reddit',
                Theme.name == theme.lower().replace(' ', '_'),
                CompetitorMention.competitor_name == competitor
            )
            
            competitor_posts = competitor_query.all()
            
            # Analyze Gusto sentiment
            gusto_sentiments = {'positive': 0, 'negative': 0, 'neutral': 0}
            gusto_analyzed_posts = []
            
            for post in gusto_posts:
                sentiment = post.sentiment_label or 'neutral'
                gusto_sentiments[sentiment] += 1
                
                gusto_analyzed_posts.append({
                    'id': post.id,
                    'title': post.title,
                    'content': post.content[:200] + '...' if len(post.content) > 200 else post.content,
                    'sentiment': sentiment,
                    'sentiment_score': round(post.sentiment_score or 0, 3),
                    'url': post.url,
                    'collected_at': post.collected_at.isoformat() if post.collected_at else None,
                    'type': 'gusto'
                })
            
            # Analyze competitor sentiment
            competitor_sentiments = {'positive': 0, 'negative': 0, 'neutral': 0}
            competitor_analyzed_posts = []
            
            for post in competitor_posts:
                sentiment = post.sentiment_label or 'neutral'
                competitor_sentiments[sentiment] += 1
                
                competitor_analyzed_posts.append({
                    'id': post.id,
                    'title': post.title,
                    'content': post.content[:200] + '...' if len(post.content) > 200 else post.content,
                    'sentiment': sentiment,
                    'sentiment_score': round(post.sentiment_score or 0, 3),
                    'url': post.url,
                    'collected_at': post.collected_at.isoformat() if post.collected_at else None,
                    'type': 'competitor'
                })
            
            # Combine and sort posts by date
            all_analyzed_posts = gusto_analyzed_posts + competitor_analyzed_posts
            all_analyzed_posts.sort(key=lambda x: x['collected_at'] or '', reverse=True)
            
            return jsonify({
                'comparison': {
                    'competitor': competitor.upper(),
                    'theme': theme.title(),
                    'gusto_posts_count': len(gusto_posts),
                    'competitor_posts_count': len(competitor_posts),
                    'total_posts': len(gusto_posts) + len(competitor_posts)
                },
                'gusto_sentiment': {
                    'positive': gusto_sentiments['positive'],
                    'negative': gusto_sentiments['negative'], 
                    'neutral': gusto_sentiments['neutral'],
                    'total': sum(gusto_sentiments.values())
                },
                'competitor_sentiment': {
                    'positive': competitor_sentiments['positive'],
                    'negative': competitor_sentiments['negative'],
                    'neutral': competitor_sentiments['neutral'], 
                    'total': sum(competitor_sentiments.values())
                },
                'analyzed_posts': all_analyzed_posts[:20]  # Show top 20 posts
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/available-competitors')
def api_available_competitors():
    """Get list of available competitors for analysis."""
    try:
        with get_session() as session:
            from utils.sentiment_analyzer import SentimentAnalyzer
            sentiment_analyzer = SentimentAnalyzer()
            
            # Count posts mentioning each competitor along with Gusto
            competitors_with_counts = []
            
            for competitor, identifiers in sentiment_analyzer.competitor_identifiers.items():
                # Get posts that mention Gusto
                posts = session.query(SocialMediaPost).filter(
                    SocialMediaPost.platform == 'reddit',
                    SocialMediaPost.content.contains('gusto')
                ).all()
                
                competitor_mention_count = 0
                for post in posts:
                    combined_text = f"{post.title or ''} {post.content}".lower()
                    if any(comp_id in combined_text for comp_id in identifiers):
                        competitor_mention_count += 1
                
                if competitor_mention_count > 0:
                    competitors_with_counts.append({
                        'name': competitor,
                        'display_name': competitor.upper(),
                        'post_count': competitor_mention_count
                    })
            
            # Sort by post count descending
            competitors_with_counts.sort(key=lambda x: x['post_count'], reverse=True)
            
            return jsonify({
                'competitors': competitors_with_counts
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    print(f"Starting Gusto Social Monitor Web App on port {port}")
    print(f"Debug mode: {debug}")
    
    app.run(host='0.0.0.0', port=port, debug=debug) 