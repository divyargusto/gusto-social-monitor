import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import sys
import os
import time
import json
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Add the project root to the Python path
sys.path.append(os.getcwd())

# Import your existing database models and functions
from backend.database.database import init_database, get_session
from backend.database.models import (
    SocialMediaPost, Theme, PostTheme, Keyword, PostKeyword,
    SentimentTrend, CompetitorMention, DataCollection
)
from sqlalchemy import func, desc

# Initialize database
@st.cache_resource
def initialize_db():
    try:
        init_database()
        return True
    except Exception as e:
        st.error(f"Database initialization failed: {e}")
        return False

# Page configuration
st.set_page_config(
    page_title="Gusto Social Media Monitor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .sentiment-positive { color: #28a745; }
    .sentiment-negative { color: #dc3545; }
    .sentiment-neutral { color: #6c757d; }
</style>
""", unsafe_allow_html=True)

# Initialize database
if not initialize_db():
    st.stop()

# Main header
st.markdown('<h1 class="main-header">🚀 Gusto Social Media Monitor</h1>', unsafe_allow_html=True)

# Sidebar for filters
st.sidebar.header("📅 Filters")

# Add cache clear button for debugging
if st.sidebar.button("🔄 Clear Cache & Refresh Data"):
    st.cache_data.clear()
    st.rerun()

# Date range selector
today = datetime.now().date()
current_year = today.year
default_start = datetime(current_year, 1, 1).date()  # January 1st of current year
default_end = today  # Current date to include all available data including August/September

date_range = st.sidebar.date_input(
    "Select Date Range",
    value=(default_start, default_end),
    max_value=today
)

if len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = default_start
    end_date = default_end

# Platform filter (keeping for consistency, but only Reddit data)
platform_filter = st.sidebar.selectbox(
    "Platform",
    ["All", "reddit"],
    index=0
)

# Sentiment filter
sentiment_filter = st.sidebar.selectbox(
    "Sentiment",
    ["All", "positive", "negative", "neutral"],
    index=0
)

# Auto-refresh option
st.sidebar.markdown("---")
st.sidebar.header("🔄 Auto-Refresh")
auto_refresh = st.sidebar.checkbox("Enable auto-refresh (every 5 minutes)")
if auto_refresh:
    time.sleep(300)  # 5 minutes
    st.rerun()

# Data loading functions
@st.cache_data(ttl=60)  # Cache for 1 minute to help with debugging
def load_overview_data(start_date, end_date):
    """Load overview statistics."""
    try:
        with get_session() as session:
            # Debug: Check total posts in database
            total_posts_db = session.query(SocialMediaPost).count()
            
            # Base query - Reddit only
            base_query = session.query(SocialMediaPost).filter(SocialMediaPost.platform == 'reddit')
            
            # Apply date filtering
            start_dt = datetime.combine(start_date, datetime.min.time())
            end_dt = datetime.combine(end_date, datetime.max.time())
            base_query = base_query.filter(
                SocialMediaPost.created_at >= start_dt,
                SocialMediaPost.created_at <= end_dt
            )
            
            # Basic counts
            total_posts = base_query.count()
            
            # Sentiment breakdown
            sentiment_counts = base_query.with_entities(
                SocialMediaPost.sentiment_label,
                func.count(SocialMediaPost.id).label('count')
            ).group_by(SocialMediaPost.sentiment_label).all()
            
            sentiment_breakdown = {sentiment: count for sentiment, count in sentiment_counts}
            
            # Average sentiment score
            avg_sentiment = base_query.with_entities(
                func.avg(SocialMediaPost.sentiment_score)
            ).scalar() or 0
            
            # Recent activity (last 7 days)
            week_ago = datetime.now() - timedelta(days=7)
            recent_posts = session.query(SocialMediaPost).filter(
                SocialMediaPost.created_at >= week_ago,
                SocialMediaPost.platform == 'reddit'
            ).count()
            
            return {
                'total_posts': total_posts,
                'sentiment_breakdown': sentiment_breakdown,
                'avg_sentiment_score': round(avg_sentiment, 3),
                'recent_posts_7_days': recent_posts,
                'debug_info': {
                    'total_posts_db': total_posts_db,
                    'filtered_posts': total_posts,
                    'date_range': f"{start_date} to {end_date}"
                }
            }
            
    except Exception as e:
        st.error(f"Error loading overview data: {e}")
        return None

@st.cache_data(ttl=60)
def load_sentiment_trends(start_date, end_date):
    """Load sentiment trends over time."""
    try:
        with get_session() as session:
            start_dt = datetime.combine(start_date, datetime.min.time())
            end_dt = datetime.combine(end_date, datetime.max.time())
            
            # Daily sentiment data
            daily_sentiment = session.query(
                func.date(SocialMediaPost.created_at).label('date'),
                func.avg(SocialMediaPost.sentiment_score).label('avg_sentiment'),
                func.count(SocialMediaPost.id).label('post_count'),
                func.count().filter(SocialMediaPost.sentiment_label == 'positive').label('positive_count'),
                func.count().filter(SocialMediaPost.sentiment_label == 'negative').label('negative_count'),
                func.count().filter(SocialMediaPost.sentiment_label == 'neutral').label('neutral_count')
            ).filter(
                SocialMediaPost.created_at >= start_dt,
                SocialMediaPost.created_at <= end_dt,
                SocialMediaPost.platform == 'reddit'
            ).group_by(
                func.date(SocialMediaPost.created_at)
            ).order_by('date').all()
            
            trends_data = []
            for row in daily_sentiment:
                trends_data.append({
                    'date': row.date,
                    'avg_sentiment': round(row.avg_sentiment or 0, 3),
                    'post_count': row.post_count,
                    'positive_count': row.positive_count,
                    'negative_count': row.negative_count,
                    'neutral_count': row.neutral_count
                })
            
            return trends_data
            
    except Exception as e:
        st.error(f"Error loading sentiment trends: {e}")
        return []

@st.cache_data(ttl=60)
def load_themes_data(start_date, end_date):
    """Load themes analysis data."""
    try:
        with get_session() as session:
            start_dt = datetime.combine(start_date, datetime.min.time())
            end_dt = datetime.combine(end_date, datetime.max.time())
            
            # Top themes with sentiment breakdown
            top_themes_base = session.query(
                Theme.id,
                Theme.name,
                Theme.description,
                Theme.category,
                func.count(PostTheme.id).label('total_mentions')
            ).select_from(Theme).join(PostTheme, Theme.id == PostTheme.theme_id).join(
                SocialMediaPost, PostTheme.post_id == SocialMediaPost.id
            ).filter(
                SocialMediaPost.platform == 'reddit',
                SocialMediaPost.created_at >= start_dt,
                SocialMediaPost.created_at <= end_dt
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
                    SocialMediaPost.platform == 'reddit',
                    SocialMediaPost.created_at >= start_dt,
                    SocialMediaPost.created_at <= end_dt
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
            
            return themes
            
    except Exception as e:
        st.error(f"Error loading themes data: {e}")
        return []

@st.cache_data(ttl=60)
def load_posts_data(start_date, end_date, sentiment_filter_val="All", limit=50):
    """Load posts data sorted by engagement (upvotes + comments)."""
    try:
        with get_session() as session:
            start_dt = datetime.combine(start_date, datetime.min.time())
            end_dt = datetime.combine(end_date, datetime.max.time())
            
            query = session.query(SocialMediaPost).filter(
                SocialMediaPost.platform == 'reddit',
                SocialMediaPost.created_at >= start_dt,
                SocialMediaPost.created_at <= end_dt
            )
            
            # Apply sentiment filter
            if sentiment_filter_val != "All":
                query = query.filter(SocialMediaPost.sentiment_label == sentiment_filter_val)
            
            # Sort by engagement (upvotes + comments) descending
            posts = query.order_by(
                desc((SocialMediaPost.upvotes + SocialMediaPost.comments_count))
            ).limit(limit).all()
            
            posts_data = []
            for post in posts:
                posts_data.append({
                    'title': post.title or 'No title',
                    'content': post.content[:200] + '...' if len(post.content) > 200 else post.content,
                    'author': post.author,
                    'sentiment_label': post.sentiment_label,
                    'sentiment_score': round(post.sentiment_score or 0, 3),
                    'upvotes': post.upvotes,
                    'comments_count': post.comments_count,
                    'created_at': post.created_at,
                    'url': post.url
                })
            
            return posts_data
            
    except Exception as e:
        st.error(f"Error loading posts data: {e}")
        return []

@st.cache_data(ttl=60)
def load_posts_for_date(selected_date, limit=20):
    """Load posts for a specific date for AI summary."""
    try:
        with get_session() as session:
            # Convert date to datetime range
            start_dt = datetime.combine(selected_date, datetime.min.time())
            end_dt = datetime.combine(selected_date, datetime.max.time())
            
            posts = session.query(SocialMediaPost).filter(
                SocialMediaPost.platform == 'reddit',
                SocialMediaPost.created_at >= start_dt,
                SocialMediaPost.created_at <= end_dt
            ).order_by(desc(SocialMediaPost.upvotes)).limit(limit).all()
            
            posts_data = []
            for post in posts:
                posts_data.append({
                    'title': post.title or 'No title',
                    'content': post.content[:300] if post.content else '',
                    'sentiment_label': post.sentiment_label,
                    'sentiment_score': post.sentiment_score or 0,
                    'upvotes': post.upvotes or 0,
                    'comments_count': post.comments_count or 0,
                    'author': post.author
                })
            
            return posts_data
            
    except Exception as e:
        st.error(f"Error loading posts for date: {e}")
        return []

def generate_ai_summary(selected_date, posts_data, avg_sentiment):
    """Generate AI summary for a specific date's sentiment trends."""
    if not OPENAI_AVAILABLE:
        return generate_fallback_summary(selected_date, posts_data, avg_sentiment)
    
    try:
        if not posts_data:
            return "No posts found for this date to analyze."
        
        # Get OpenAI API key from environment
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return generate_fallback_summary(selected_date, posts_data, avg_sentiment)
        
        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)
        
        # Prepare context for AI
        date_str = selected_date.strftime('%B %d, %Y')
        total_posts = len(posts_data)
        sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
        
        for post in posts_data:
            sentiment = post.get('sentiment_label', 'neutral')
            if sentiment in sentiment_counts:
                sentiment_counts[sentiment] += 1
        
        # Get top posts by engagement
        top_posts = sorted(posts_data, key=lambda x: x.get('upvotes', 0) + x.get('comments_count', 0), reverse=True)[:3]
        
        # Prepare prompt for AI
        posts_context = ""
        for i, post in enumerate(top_posts, 1):
            posts_context += f"{i}. \"{post['title']}\"\n"
            posts_context += f"   Sentiment: {post['sentiment_label']} ({post['sentiment_score']:.2f})\n"
            posts_context += f"   Engagement: {post['upvotes']} upvotes, {post['comments_count']} comments\n\n"
        
        prompt = f"""Analyze Gusto-related Reddit sentiment for {date_str}:

**Data Summary:**
- Total posts: {total_posts}
- Sentiment: {sentiment_counts['positive']} positive, {sentiment_counts['negative']} negative, {sentiment_counts['neutral']} neutral
- Average sentiment score: {avg_sentiment:.3f}

**Top Posts:**
{posts_context}

Provide a concise analysis in ONE paragraph only covering overall sentiment trend, key drivers, and one actionable insight for Gusto. Keep it professional and under 100 words."""
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a social media analyst for Gusto, a payroll and HR platform."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        return generate_fallback_summary(selected_date, posts_data, avg_sentiment)

def generate_fallback_summary(selected_date, posts_data, avg_sentiment):
    """Generate a rule-based summary when AI is not available."""
    date_str = selected_date.strftime('%B %d, %Y')
    total_posts = len(posts_data)
    
    # Determine overall sentiment
    if avg_sentiment > 0.1:
        sentiment_desc = "positive"
        trend_desc = "Users expressed generally favorable views"
    elif avg_sentiment < -0.1:
        sentiment_desc = "negative"
        trend_desc = "Users expressed concerns or criticism"
    else:
        sentiment_desc = "neutral"
        trend_desc = "Users maintained a balanced perspective"
    
    # Analyze engagement
    total_engagement = sum(post.get('upvotes', 0) + post.get('comments_count', 0) for post in posts_data)
    avg_engagement = total_engagement / total_posts if total_posts > 0 else 0
    
    engagement_desc = "high" if avg_engagement > 10 else "moderate" if avg_engagement > 5 else "low"
    
    # Get most discussed topics
    top_post = max(posts_data, key=lambda x: x.get('upvotes', 0) + x.get('comments_count', 0)) if posts_data else None
    
    summary = f"""**📊 Analysis for {date_str}:** Gusto-related discussions showed **{sentiment_desc}** sentiment (score: {avg_sentiment:.3f}) across {total_posts} posts with {engagement_desc} community engagement. {trend_desc} about Gusto's services."""
    
    if top_post:
        summary += f" Most discussed topic: \"{top_post['title'][:50]}...\" received {top_post.get('upvotes', 0)} upvotes."
    
    summary += f" **Recommendation:** {'Continue monitoring positive momentum.' if avg_sentiment > 0 else 'Investigate concerns and consider response strategy.' if avg_sentiment < -0.1 else 'Maintain current engagement strategy.'}"
    
    return summary

@st.cache_data(ttl=60)
def load_posts_by_theme_sentiment(theme_name, sentiment_filter, start_date, end_date, limit=20):
    """Load posts filtered by theme and sentiment."""
    try:
        with get_session() as session:
            start_dt = datetime.combine(start_date, datetime.min.time())
            end_dt = datetime.combine(end_date, datetime.max.time())
            
            # Base query with joins to get theme-related posts
            query = session.query(SocialMediaPost).select_from(SocialMediaPost).join(
                PostTheme, SocialMediaPost.id == PostTheme.post_id
            ).join(
                Theme, PostTheme.theme_id == Theme.id
            ).filter(
                SocialMediaPost.platform == 'reddit',
                SocialMediaPost.created_at >= start_dt,
                SocialMediaPost.created_at <= end_dt
            )
            
            # Add theme filtering
            if theme_name:
                # Convert display name back to database format
                theme_db_name = theme_name.lower().replace(' ', '_')
                query = query.filter(Theme.name == theme_db_name)
            
            # Add sentiment filtering
            if sentiment_filter and sentiment_filter != "All":
                query = query.filter(SocialMediaPost.sentiment_label == sentiment_filter)
            
            posts = query.order_by(desc(SocialMediaPost.created_at)).limit(limit).all()
            
            posts_data = []
            for post in posts:
                posts_data.append({
                    'id': post.id,
                    'title': post.title or 'No title',
                    'content': post.content[:300] + '...' if post.content and len(post.content) > 300 else (post.content or ''),
                    'author': post.author or 'Unknown',
                    'sentiment_label': post.sentiment_label or 'neutral',
                    'sentiment_score': round(post.sentiment_score or 0, 3),
                    'upvotes': post.upvotes or 0,
                    'comments_count': post.comments_count or 0,
                    'created_at': post.created_at,
                    'url': post.url
                })
            
            return posts_data
            
    except Exception as e:
        st.error(f"Error loading theme posts: {e}")
        return []

# Load data
overview_data = load_overview_data(start_date, end_date)
trends_data = load_sentiment_trends(start_date, end_date)
themes_data = load_themes_data(start_date, end_date)

if overview_data:
    # Debug information
    if 'debug_info' in overview_data:
        debug = overview_data['debug_info']
        st.info(f"🔍 Debug Info: {debug['total_posts_db']} total posts in DB, {debug['filtered_posts']} posts in date range ({debug['date_range']})")
    
    # Overview metrics row
    st.header("📊 Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Posts",
            value=overview_data['total_posts'],
            delta=None
        )
    
    with col2:
        st.metric(
            label="Recent (7 days)",
            value=overview_data['recent_posts_7_days'],
            delta=None
        )
    
    with col3:
        positive_rate = 0
        if overview_data['total_posts'] > 0:
            positive_count = overview_data['sentiment_breakdown'].get('positive', 0)
            positive_rate = round((positive_count / overview_data['total_posts']) * 100, 1)
        
        st.metric(
            label="Positive Rate",
            value=f"{positive_rate}%",
            delta=None
        )
    
    with col4:
        st.metric(
            label="Avg Sentiment Score",
            value=overview_data['avg_sentiment_score'],
            delta=None
        )

    # Charts row
    st.header("📈 Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Sentiment Breakdown")
        
        if overview_data['sentiment_breakdown']:
            # Prepare data for pie chart
            sentiments = list(overview_data['sentiment_breakdown'].keys())
            counts = list(overview_data['sentiment_breakdown'].values())
            
            # Create pie chart with explicit colors to ensure proper green/red/gray scheme
            colors = []
            for sentiment in sentiments:
                if sentiment == "positive":
                    colors.append("#28a745")  # Green
                elif sentiment == "negative":
                    colors.append("#dc3545")  # Red
                elif sentiment == "neutral":
                    colors.append("#6c757d")  # Gray
                else:
                    colors.append("#6c757d")  # Default to gray
            
            fig = go.Figure(data=[go.Pie(
                labels=sentiments,
                values=counts,
                marker=dict(colors=colors),
                textposition="inside",
                textinfo="percent+label",
                hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<br><i>Click buttons below to filter posts</i><extra></extra>"
            )])
            fig.update_layout(title="Sentiment Distribution")
            st.plotly_chart(fig, use_container_width=True)
            
            # Add sentiment filter buttons
            st.markdown("**Quick Filter Posts:**")
            col_a, col_b, col_c, col_d = st.columns(4)
            with col_a:
                if st.button("🟢 Positive", key="pos_btn"):
                    st.session_state.sentiment_filter = "positive"
                    st.rerun()
            with col_b:
                if st.button("🔴 Negative", key="neg_btn"):
                    st.session_state.sentiment_filter = "negative"
                    st.rerun()
            with col_c:
                if st.button("⚪ Neutral", key="neu_btn"):
                    st.session_state.sentiment_filter = "neutral"
                    st.rerun()
            with col_d:
                if st.button("🔄 All", key="all_btn"):
                    st.session_state.sentiment_filter = "All"
                    st.rerun()
        else:
            st.info("No sentiment data available for the selected date range.")
    
    with col2:
        st.subheader("Sentiment Trends")
        
        if trends_data:
            # Create interactive trends chart
            df_trends = pd.DataFrame(trends_data)
            df_trends['date'] = pd.to_datetime(df_trends['date'])
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_trends['date'],
                y=df_trends['avg_sentiment'],
                mode='lines+markers',
                name='Average Sentiment',
                line=dict(color='#1f77b4', width=3),
                marker=dict(size=8, color='#1f77b4'),
                hovertemplate='<b>%{x|%B %d, %Y}</b><br>' +
                             'Avg Sentiment: %{y:.3f}<br>' +
                             'Posts: %{customdata}<br>' +
                             '<i>Select date below for AI analysis</i><extra></extra>',
                customdata=df_trends['post_count']
            ))
            
            fig.update_layout(
                title='Average Sentiment Over Time',
                xaxis_title='Date',
                yaxis_title='Average Sentiment',
                yaxis_range=[-1, 1],
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # AI Analysis Section
            st.markdown("### 🤖 AI Sentiment Analysis")
            
            # Date selector for AI analysis
            available_dates = [pd.to_datetime(item['date']).date() for item in trends_data]
            
            if available_dates:
                col_date, col_button = st.columns([2, 1])
                
                with col_date:
                    selected_date = st.selectbox(
                        "📅 Select date for AI insights:",
                        available_dates,
                        format_func=lambda x: x.strftime('%B %d, %Y'),
                        key="ai_analysis_date"
                    )
                
                with col_button:
                    st.markdown("<br>", unsafe_allow_html=True)  # Add spacing
                    if st.button("🚀 Generate AI Summary", key="generate_summary", type="primary"):
                        st.session_state.show_ai_summary = True
                        st.session_state.selected_analysis_date = selected_date
                
                # Show AI summary if requested
                if hasattr(st.session_state, 'show_ai_summary') and st.session_state.show_ai_summary:
                    analysis_date = st.session_state.get('selected_analysis_date')
                    if analysis_date:
                        with st.spinner('🤖 Analyzing sentiment trends and generating insights...'):
                            # Find the corresponding trends data point
                            trends_point = next(
                                (item for item in trends_data if pd.to_datetime(item['date']).date() == analysis_date), 
                                None
                            )
                            
                            if trends_point:
                                # Load posts for the selected date
                                posts_for_date = load_posts_for_date(analysis_date)
                                
                                if posts_for_date:
                                    # Generate AI summary
                                    ai_summary = generate_ai_summary(analysis_date, posts_for_date, trends_point['avg_sentiment'])
                                    
                                    # Display the summary in a nice container
                                    st.markdown("""
                                    <div style='background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); 
                                                padding: 1.5rem; border-radius: 0.8rem; margin: 1rem 0;
                                                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);'>
                                    """, unsafe_allow_html=True)
                                    
                                    st.markdown(ai_summary)
                                    
                                    st.markdown("</div>", unsafe_allow_html=True)
                                    
                                    # Add some quick stats
                                    st.markdown("---")
                                    col_stat1, col_stat2, col_stat3 = st.columns(3)
                                    with col_stat1:
                                        st.metric("📊 Posts Analyzed", len(posts_for_date))
                                    with col_stat2:
                                        st.metric("📈 Avg Sentiment", f"{trends_point['avg_sentiment']:.3f}")
                                    with col_stat3:
                                        total_engagement = sum(p.get('upvotes', 0) + p.get('comments_count', 0) for p in posts_for_date)
                                        st.metric("💬 Total Engagement", total_engagement)
                                else:
                                    st.info(f"📭 No posts found for {analysis_date.strftime('%B %d, %Y')} to analyze.")
                            else:
                                st.error("Could not find trend data for the selected date.")
                else:
                    st.info("👆 Select a date above and click 'Generate AI Summary' to get detailed insights about sentiment trends for that specific day.")
        else:
            st.info("No trends data available for the selected date range.")

    # Interactive Themes Analysis
    if themes_data:
        st.header("🎯 Top Themes")
        
        # Prepare data for themes chart
        theme_names = [theme['name'] for theme in themes_data]
        positive_counts = [theme['positive_count'] for theme in themes_data]
        negative_counts = [theme['negative_count'] for theme in themes_data]
        neutral_counts = [theme['neutral_count'] for theme in themes_data]
        
        # Create interactive stacked bar chart
        fig = go.Figure(data=[
            go.Bar(
                name='Positive', 
                x=theme_names, 
                y=positive_counts, 
                marker_color='#28a745',
                hovertemplate='<b>%{x}</b><br>Positive: %{y}<br><i>Click to filter posts!</i><extra></extra>',
                customdata=['positive'] * len(theme_names)
            ),
            go.Bar(
                name='Negative', 
                x=theme_names, 
                y=negative_counts, 
                marker_color='#dc3545',
                hovertemplate='<b>%{x}</b><br>Negative: %{y}<br><i>Click to filter posts!</i><extra></extra>',
                customdata=['negative'] * len(theme_names)
            ),
            go.Bar(
                name='Neutral', 
                x=theme_names, 
                y=neutral_counts, 
                marker_color='#6c757d',
                hovertemplate='<b>%{x}</b><br>Neutral: %{y}<br><i>Click to filter posts!</i><extra></extra>',
                customdata=['neutral'] * len(theme_names)
            )
        ])
        
        fig.update_layout(
            barmode='stack',
            title='Theme Sentiment Breakdown (Click bars to filter posts below)',
            xaxis_title='Themes',
            yaxis_title='Number of Posts',
            height=500,
            hovermode='closest'
        )
        
        # Display the chart
        st.plotly_chart(fig, use_container_width=True, key="themes_chart")
        
        # Quick action buttons for each theme-sentiment combination
        st.markdown("### 🎯 Quick Theme Filters")
        st.markdown("Click any button below to filter posts by theme and sentiment:")
        
        # Create buttons for each theme-sentiment combination
        for theme in themes_data:
            if theme['positive_count'] > 0 or theme['negative_count'] > 0 or theme['neutral_count'] > 0:
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                
                with col1:
                    st.write(f"**{theme['name']}**")
                
                with col2:
                    if theme['positive_count'] > 0:
                        if st.button(f"🟢 {theme['positive_count']}", key=f"pos_{theme['name']}"):
                            st.session_state.selected_theme_filter = theme['name']
                            st.session_state.selected_sentiment_filter = "positive"
                            st.session_state.show_filtered_posts = True
                            st.rerun()
                
                with col3:
                    if theme['negative_count'] > 0:
                        if st.button(f"🔴 {theme['negative_count']}", key=f"neg_{theme['name']}"):
                            st.session_state.selected_theme_filter = theme['name']
                            st.session_state.selected_sentiment_filter = "negative"
                            st.session_state.show_filtered_posts = True
                            st.rerun()
                
                with col4:
                    if theme['neutral_count'] > 0:
                        if st.button(f"⚪ {theme['neutral_count']}", key=f"neu_{theme['name']}"):
                            st.session_state.selected_theme_filter = theme['name']
                            st.session_state.selected_sentiment_filter = "neutral"
                            st.session_state.show_filtered_posts = True
                            st.rerun()
        
        # Clear filter button
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("🔄 Clear All Filters", key="clear_all_filters"):
                if 'selected_theme_filter' in st.session_state:
                    del st.session_state.selected_theme_filter
                if 'selected_sentiment_filter' in st.session_state:
                    del st.session_state.selected_sentiment_filter
                if 'show_filtered_posts' in st.session_state:
                    del st.session_state.show_filtered_posts
                st.rerun()
        
        # Alternative manual selection
        st.markdown("### 📋 Manual Selection")
        
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            manual_theme = st.selectbox(
                "🎯 Select Theme:",
                ["All Themes"] + [theme['name'] for theme in themes_data],
                key="manual_theme_selector"
            )
        
        with col2:
            manual_sentiment = st.selectbox(
                "😊 Select Sentiment:",
                ["All", "positive", "negative", "neutral"],
                key="manual_sentiment_selector"
            )
        
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔍 Apply Filter", key="apply_manual_filter"):
                st.session_state.selected_theme_filter = manual_theme if manual_theme != "All Themes" else None
                st.session_state.selected_sentiment_filter = manual_sentiment if manual_sentiment != "All" else None
                st.session_state.show_filtered_posts = True
                st.rerun()
        
        # Display filtered posts based on session state
        if hasattr(st.session_state, 'show_filtered_posts') and st.session_state.show_filtered_posts:
            theme_filter = st.session_state.get('selected_theme_filter')
            sentiment_filter = st.session_state.get('selected_sentiment_filter')
            
            if theme_filter or sentiment_filter:
                display_theme = theme_filter or "All Themes"
                display_sentiment = sentiment_filter or "All"
                
                st.markdown("### 📋 Filtered Posts")
                st.info(f"🔍 **Active Filter:** {display_theme} → {display_sentiment}")
                
                # Load theme-filtered posts
                theme_posts = load_posts_by_theme_sentiment(
                    theme_filter,
                    sentiment_filter,
                    start_date,
                    end_date
                )
                
                if theme_posts:
                    st.success(f"📊 Found **{len(theme_posts)}** posts matching your filters")
                    
                    # Display filtered posts
                    for i, post in enumerate(theme_posts[:15]):  # Show top 15
                        with st.expander(f"📌 {post['title'][:80]}..." if len(post['title']) > 80 else f"📌 {post['title']}"):
                            col1, col2, col3 = st.columns([3, 1, 1])
                            
                            with col1:
                                st.markdown(f'<div style="background: #ffffff; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #667eea;">{post["content"]}</div>', unsafe_allow_html=True)
                                if post['url']:
                                    st.markdown(f"🔗 [View Original Post]({post['url']})")
                            
                            with col2:
                                sentiment_color = {'positive': '#28a745', 'negative': '#dc3545', 'neutral': '#6c757d'}
                                color = sentiment_color.get(post['sentiment_label'], '#6c757d')
                                st.markdown(f"**Sentiment:** <span style='color: {color}; font-weight: bold;'>{post['sentiment_label'].title()}</span>", unsafe_allow_html=True)
                                st.write(f"**Score:** {post['sentiment_score']}")
                                st.write(f"**Author:** {post['author']}")
                            
                            with col3:
                                st.write(f"**👍 Upvotes:** {post['upvotes']}")
                                st.write(f"**💬 Comments:** {post['comments_count']}")
                                if post['created_at']:
                                    try:
                                        if isinstance(post['created_at'], str):
                                            created_date = datetime.fromisoformat(post['created_at'].replace('Z', '+00:00'))
                                        else:
                                            created_date = post['created_at']
                                        st.write(f"**📅 Date:** {created_date.strftime('%m/%d/%Y')}")
                                    except:
                                        st.write(f"**📅 Date:** {post['created_at']}")
                else:
                    st.warning(f"📭 No posts found for theme '{display_theme}' with sentiment '{display_sentiment}'")
        else:
            st.info("👆 Click any colored button above to filter posts by theme and sentiment!")

    # Recent posts section
    st.header("📝 Posts (Sorted by Engagement)")
    
    # Use session state filter if available, otherwise use sidebar filter
    active_sentiment_filter = st.session_state.get('sentiment_filter', sentiment_filter)
    if active_sentiment_filter != sentiment_filter:
        st.info(f"🔍 Filtered by: **{active_sentiment_filter}** sentiment (click 'All' button above to reset)")
    
    posts_data = load_posts_data(start_date, end_date, active_sentiment_filter, limit=1000)  # Get all posts
    
    if posts_data:
        st.write(f"**Showing {len(posts_data)} posts**")
        
        for i, post in enumerate(posts_data):  # Show ALL posts
            col1, col2, col3 = st.columns([2.5, 1, 0.7])  # Narrower columns: 2.5, 1, 0.7
            
            with col1:
                # Compact title and content
                st.markdown(f"**{post['title'][:80]}{'...' if len(post['title']) > 80 else ''}**")
                # Shorter content preview
                if post['content']:
                    content_preview = post['content'][:150] + "..." if len(post['content']) > 150 else post['content']
                    st.caption(content_preview)
                if post['url']:
                    st.markdown(f"[🔗 View]({post['url']})")
            
            with col2:
                # Compact sentiment info
                sentiment_emoji = {'positive': '🟢', 'negative': '🔴', 'neutral': '⚪'}
                emoji = sentiment_emoji.get(post['sentiment_label'], '⚪')
                st.write(f"{emoji} {post['sentiment_label'].title()}")
                st.caption(f"Score: {post['sentiment_score']:.2f}")
            
            with col3:
                # Very compact stats
                st.caption(f"👍 {post['upvotes'] or 0}")
                st.caption(f"💬 {post['comments_count'] or 0}")
                if post['created_at']:
                    date_str = post['created_at'].strftime('%m/%d/%y')
                    st.caption(f"📅 {date_str}")
            
            st.divider()  # Clean separator
    else:
        st.info("No posts found for the selected filters.")

else:
    st.error("Failed to load overview data. Please check your database connection.")

# Footer
st.markdown("---")
st.markdown("**Gusto Social Media Monitor** - Built with Streamlit 🚀")
