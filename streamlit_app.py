import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sqlite3
import os

# Page configuration
st.set_page_config(
    page_title="Gusto Social Media Monitor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .metric-container {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1.5rem;
        border-radius: 0.8rem;
        margin: 0.5rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .sentiment-positive { color: #28a745; font-weight: bold; }
    .sentiment-negative { color: #dc3545; font-weight: bold; }
    .sentiment-neutral { color: #6c757d; font-weight: bold; }
    .post-card {
        background: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #667eea;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .chart-container {
        background: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for filters
if 'selected_theme' not in st.session_state:
    st.session_state.selected_theme = None
if 'selected_sentiment' not in st.session_state:
    st.session_state.selected_sentiment = None

# Database connection with better error handling
@st.cache_resource
def get_db_connection():
    db_paths = ['gusto_monitor.db', 'backend/gusto_monitor.db', './gusto_monitor.db']
    for db_path in db_paths:
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path, check_same_thread=False)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM social_media_posts LIMIT 1")
                st.success(f"✅ Connected to database: {db_path}")
                return conn
            except Exception as e:
                st.warning(f"⚠️ Database error for {db_path}: {e}")
                continue
    
    st.error("❌ No database found! App will show empty data.")
    return sqlite3.connect(':memory:', check_same_thread=False)

conn = get_db_connection()

# Main header
st.markdown('<h1 class="main-header">🚀 Gusto Social Media Monitor</h1>', unsafe_allow_html=True)

# Sidebar filters
st.sidebar.header("📅 Filters")
today = datetime.now().date()
default_start = today - timedelta(days=30)

date_range = st.sidebar.date_input("Select Date Range", value=(default_start, today), max_value=today)
if len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = default_start, today

start_date_str = start_date.strftime('%Y-%m-%d')
end_date_str = end_date.strftime('%Y-%m-%d')

platform_filter = st.sidebar.selectbox("Platform", ["All", "reddit"], index=0)
sentiment_filter = st.sidebar.selectbox("Sentiment", ["All", "positive", "negative", "neutral"], index=0)

# Data functions with improved error handling
@st.cache_data(ttl=300)
def load_overview_data(start_date, end_date):
    try:
        cursor = conn.cursor()
        where_conditions = ["platform = 'reddit'"]
        if start_date and end_date:
            where_conditions.append(f"DATE(created_at) BETWEEN '{start_date}' AND '{end_date}'")
        where_clause = " AND ".join(where_conditions)
        
        # Test the query first
        cursor.execute(f"SELECT COUNT(*) FROM social_media_posts WHERE {where_clause}")
        total_posts = cursor.fetchone()[0] or 0
        
        if total_posts == 0:
            st.warning("⚠️ No posts found in database for the selected date range")
        
        cursor.execute(f"SELECT sentiment_label, COUNT(*) FROM social_media_posts WHERE {where_clause} AND sentiment_label IS NOT NULL GROUP BY sentiment_label")
        sentiment_data = cursor.fetchall()
        sentiment_breakdown = {row[0]: row[1] for row in sentiment_data}
        for sentiment in ['positive', 'negative', 'neutral']:
            if sentiment not in sentiment_breakdown:
                sentiment_breakdown[sentiment] = 0
        
        cursor.execute(f"SELECT AVG(sentiment_score) FROM social_media_posts WHERE {where_clause} AND sentiment_score IS NOT NULL")
        avg_sentiment = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(*) FROM social_media_posts WHERE platform = 'reddit' AND DATE(created_at) >= DATE('now', '-7 days')")
        recent_posts = cursor.fetchone()[0] or 0
        
        return {
            'total_posts': total_posts,
            'sentiment_breakdown': sentiment_breakdown,
            'avg_sentiment_score': round(avg_sentiment, 3),
            'recent_posts_7_days': recent_posts
        }
    except Exception as e:
        st.error(f"❌ Database error in overview: {e}")
        return {'total_posts': 0, 'sentiment_breakdown': {'positive': 0, 'negative': 0, 'neutral': 0}, 'avg_sentiment_score': 0, 'recent_posts_7_days': 0}

@st.cache_data(ttl=300)
def load_sentiment_trends(start_date, end_date):
    try:
        cursor = conn.cursor()
        where_conditions = ["platform = 'reddit'"]
        if start_date and end_date:
            where_conditions.append(f"DATE(created_at) BETWEEN '{start_date}' AND '{end_date}'")
        where_clause = " AND ".join(where_conditions)
        
        cursor.execute(f"""
            SELECT DATE(created_at) as date, AVG(sentiment_score) as avg_sentiment, COUNT(*) as post_count,
                   SUM(CASE WHEN sentiment_label = 'positive' THEN 1 ELSE 0 END) as positive_count,
                   SUM(CASE WHEN sentiment_label = 'negative' THEN 1 ELSE 0 END) as negative_count,
                   SUM(CASE WHEN sentiment_label = 'neutral' THEN 1 ELSE 0 END) as neutral_count
            FROM social_media_posts WHERE {where_clause}
            GROUP BY DATE(created_at) ORDER BY DATE(created_at)
        """)
        
        trends_data = []
        for row in cursor.fetchall():
            trends_data.append({
                'date': row[0], 'avg_sentiment': round(row[1] or 0, 3), 'post_count': row[2],
                'positive_count': row[3], 'negative_count': row[4], 'neutral_count': row[5]
            })
        
        if not trends_data:
            st.warning("⚠️ No trends data available for selected date range")
        
        return trends_data
    except Exception as e:
        st.error(f"❌ Error loading sentiment trends: {e}")
        return []

@st.cache_data(ttl=300)
def load_themes_data(start_date, end_date):
    try:
        cursor = conn.cursor()
        where_conditions = ["smp.platform = 'reddit'"]
        if start_date and end_date:
            where_conditions.append(f"DATE(smp.created_at) BETWEEN '{start_date}' AND '{end_date}'")
        where_clause = " AND ".join(where_conditions)
        
        cursor.execute(f"""
            SELECT t.name, t.description, t.category, COUNT(pt.id) as total_mentions,
                   SUM(CASE WHEN smp.sentiment_label = 'positive' THEN 1 ELSE 0 END) as positive_count,
                   SUM(CASE WHEN smp.sentiment_label = 'negative' THEN 1 ELSE 0 END) as negative_count,
                   SUM(CASE WHEN smp.sentiment_label = 'neutral' THEN 1 ELSE 0 END) as neutral_count
            FROM themes t
            JOIN post_themes pt ON t.id = pt.theme_id
            JOIN social_media_posts smp ON pt.post_id = smp.id
            WHERE {where_clause}
            GROUP BY t.id, t.name, t.description, t.category
            ORDER BY total_mentions DESC LIMIT 10
        """)
        
        themes = []
        for row in cursor.fetchall():
            themes.append({
                'name': row[0].replace('_', ' ').title(),
                'description': row[1] or '',
                'category': row[2] or '',
                'total_mentions': row[3],
                'positive_count': row[4],
                'negative_count': row[5],
                'neutral_count': row[6]
            })
        
        if not themes:
            st.warning("⚠️ No themes data available for selected date range")
        
        return themes
    except Exception as e:
        st.error(f"❌ Error loading themes data: {e}")
        return []

@st.cache_data(ttl=300)
def load_posts_data(start_date, end_date, sentiment_filter_val="All", limit=50):
    try:
        cursor = conn.cursor()
        where_conditions = ["platform = 'reddit'"]
        if start_date and end_date:
            where_conditions.append(f"DATE(created_at) BETWEEN '{start_date}' AND '{end_date}'")
        if sentiment_filter_val != "All":
            where_conditions.append(f"sentiment_label = '{sentiment_filter_val}'")
        where_clause = " AND ".join(where_conditions)
        
        cursor.execute(f"""
            SELECT title, content, author, sentiment_label, sentiment_score, upvotes, comments_count, created_at, url, id
            FROM social_media_posts WHERE {where_clause} ORDER BY created_at DESC LIMIT {limit}
        """)
        
        posts_data = []
        for row in cursor.fetchall():
            posts_data.append({
                'id': row[9], 'title': row[0] or 'No title',
                'content': row[1][:200] + '...' if row[1] and len(row[1]) > 200 else (row[1] or ''),
                'author': row[2] or 'Unknown', 'sentiment_label': row[3] or 'neutral',
                'sentiment_score': round(row[4] or 0, 3), 'upvotes': row[5] or 0,
                'comments_count': row[6] or 0, 'created_at': row[7], 'url': row[8]
            })
        return posts_data
    except Exception as e:
        st.error(f"❌ Error loading posts data: {e}")
        return []

@st.cache_data(ttl=300)
def load_posts_by_theme_sentiment(theme_name, sentiment_filter, start_date, end_date, limit=50):
    try:
        cursor = conn.cursor()
        query = """
            SELECT DISTINCT smp.title, smp.content, smp.author, smp.sentiment_label, smp.sentiment_score, 
                   smp.upvotes, smp.comments_count, smp.created_at, smp.url, smp.id, t.name as theme_name
            FROM social_media_posts smp
            JOIN post_themes pt ON smp.id = pt.post_id
            JOIN themes t ON pt.theme_id = t.id
        """
        where_conditions = ["smp.platform = 'reddit'"]
        
        if theme_name:
            theme_db_name = theme_name.lower().replace(' ', '_')
            where_conditions.append(f"t.name = '{theme_db_name}'")
        
        if sentiment_filter:
            where_conditions.append(f"smp.sentiment_label = '{sentiment_filter}'")
        
        if start_date and end_date:
            where_conditions.append(f"DATE(smp.created_at) BETWEEN '{start_date}' AND '{end_date}'")
        
        where_clause = " AND ".join(where_conditions)
        query += f" WHERE {where_clause} ORDER BY smp.created_at DESC LIMIT {limit}"
        cursor.execute(query)
        
        posts_data = []
        for row in cursor.fetchall():
            posts_data.append({
                'id': row[9], 'title': row[0] or 'No title',
                'content': row[1][:300] + '...' if row[1] and len(row[1]) > 300 else (row[1] or ''),
                'author': row[2] or 'Unknown', 'sentiment_label': row[3] or 'neutral',
                'sentiment_score': round(row[4] or 0, 3), 'upvotes': row[5] or 0,
                'comments_count': row[6] or 0, 'created_at': row[7], 'url': row[8],
                'theme_name': row[10] if len(row) > 10 else 'N/A'
            })
        return posts_data
    except Exception as e:
        st.error(f"❌ Error loading theme posts: {e}")
        return []

# Load data with progress indicators
with st.spinner("Loading dashboard data..."):
    overview_data = load_overview_data(start_date_str, end_date_str)
    trends_data = load_sentiment_trends(start_date_str, end_date_str)
    themes_data = load_themes_data(start_date_str, end_date_str)

# Overview metrics
st.header("📊 Overview")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown('<div class="metric-container">', unsafe_allow_html=True)
    st.metric("Total Posts", f"{overview_data['total_posts']:,}")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="metric-container">', unsafe_allow_html=True)
    st.metric("Recent (7 days)", f"{overview_data['recent_posts_7_days']:,}")
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    positive_rate = 0
    if overview_data['total_posts'] > 0:
        positive_count = overview_data['sentiment_breakdown'].get('positive', 0)
        positive_rate = round((positive_count / overview_data['total_posts']) * 100, 1)
    st.markdown('<div class="metric-container">', unsafe_allow_html=True)
    st.metric("Positive Rate", f"{positive_rate}%")
    st.markdown('</div>', unsafe_allow_html=True)

with col4:
    st.markdown('<div class="metric-container">', unsafe_allow_html=True)
    st.metric("Avg Sentiment Score", overview_data['avg_sentiment_score'])
    st.markdown('</div>', unsafe_allow_html=True)

# Charts section
st.header("📈 Analytics")
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.subheader("Sentiment Breakdown")
    
    if sum(overview_data['sentiment_breakdown'].values()) > 0:
        sentiments = list(overview_data['sentiment_breakdown'].keys())
        counts = list(overview_data['sentiment_breakdown'].values())
        
        fig = px.pie(values=counts, names=sentiments,
                    color_discrete_map={'positive': '#28a745', 'negative': '#dc3545', 'neutral': '#6c757d'},
                    title="Click pie slices to filter posts below")
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(height=400, showlegend=True)
        
        st.plotly_chart(fig, use_container_width=True, key="sentiment_pie")
        
        st.write("**Quick Filter:**")
        col_a, col_b, col_c, col_d = st.columns(4)
        with col_a:
            if st.button("🟢 Positive", key="pos_btn"):
                st.session_state.selected_sentiment = "positive"
                st.rerun()
        with col_b:
            if st.button("🔴 Negative", key="neg_btn"):
                st.session_state.selected_sentiment = "negative"
                st.rerun()
        with col_c:
            if st.button("⚪ Neutral", key="neu_btn"):
                st.session_state.selected_sentiment = "neutral"
                st.rerun()
        with col_d:
            if st.button("🔄 All", key="all_btn"):
                st.session_state.selected_sentiment = None
                st.rerun()
    else:
        st.info("📊 No sentiment data available for selected date range.")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.subheader("Sentiment Trends")
    
    if trends_data and len(trends_data) > 0:
        try:
            df_trends = pd.DataFrame(trends_data)
            df_trends['date'] = pd.to_datetime(df_trends['date'])
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_trends['date'], y=df_trends['avg_sentiment'],
                mode='lines+markers', name='Average Sentiment',
                line=dict(color='#667eea', width=3), marker=dict(size=6),
                hovertemplate='<b>%{x}</b><br>Avg Sentiment: %{y:.3f}<br>Posts: %{customdata}<extra></extra>',
                customdata=df_trends['post_count']
            ))
            
            fig.update_layout(
                title='Average Sentiment Over Time',
                xaxis_title='Date', yaxis_title='Average Sentiment',
                yaxis=dict(range=[-1, 1]), height=400, hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True, key="trends_chart")
        except Exception as e:
            st.error(f"❌ Error creating trends chart: {e}")
            st.info("📈 Trends chart data is available but chart failed to render")
    else:
        st.info("📈 No trends data available for selected date range.")
    st.markdown('</div>', unsafe_allow_html=True)

# Themes analysis with GROUPED bars (like Flask app)
if themes_data and len(themes_data) > 0:
    st.header("🎯 Top Themes")
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    
    try:
        # Create DataFrame for easier manipulation
        df_themes = pd.DataFrame(themes_data)
        
        # Create grouped bar chart (NOT stacked) like your Flask app
        fig = go.Figure()
        
        # Add each sentiment as separate bars (grouped, not stacked)
        fig.add_trace(go.Bar(
            name='Positive', x=df_themes['name'], y=df_themes['positive_count'],
            marker_color='#28a745', offsetgroup=1,
            hovertemplate='<b>%{x}</b><br>Positive: %{y}<br><i>Click to filter posts</i><extra></extra>'
        ))
        
        fig.add_trace(go.Bar(
            name='Negative', x=df_themes['name'], y=df_themes['negative_count'],
            marker_color='#dc3545', offsetgroup=2,
            hovertemplate='<b>%{x}</b><br>Negative: %{y}<br><i>Click to filter posts</i><extra></extra>'
        ))
        
        fig.add_trace(go.Bar(
            name='Neutral', x=df_themes['name'], y=df_themes['neutral_count'],
            marker_color='#6c757d', offsetgroup=3,
            hovertemplate='<b>%{x}</b><br>Neutral: %{y}<br><i>Click to filter posts</i><extra></extra>'
        ))
        
        # Set layout for grouped bars
        fig.update_layout(
            title='Theme Sentiment Breakdown (Click bars to filter posts below)',
            xaxis_title='Themes', yaxis_title='Number of Posts',
            barmode='group',  # This makes bars grouped instead of stacked
            height=500, hovermode='x unified',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        # Display chart
        st.plotly_chart(fig, use_container_width=True, key="themes_chart")
        
        # Interactive theme and sentiment selection
        col1, col2, col3 = st.columns(3)
        with col1:
            selected_theme = st.selectbox(
                "🎯 Select Theme:",
                ["All Themes"] + [theme['name'] for theme in themes_data],
                key="theme_selector"
            )
        
        with col2:
            selected_sentiment_dropdown = st.selectbox(
                "😊 Select Sentiment:",
                ["All", "positive", "negative", "neutral"],
                key="sentiment_selector"
            )
        
        with col3:
            if st.button("🔄 Reset Filters", key="reset_filters"):
                st.session_state.selected_theme = None
                st.session_state.selected_sentiment = None
                st.rerun()
        
        # Use session state values if they exist, otherwise use dropdown values
        active_theme = st.session_state.selected_theme if st.session_state.selected_theme else (selected_theme if selected_theme != "All Themes" else None)
        active_sentiment = st.session_state.selected_sentiment if st.session_state.selected_sentiment else (selected_sentiment_dropdown if selected_sentiment_dropdown != "All" else None)
        
        # Show filtered posts based on theme and sentiment
        if active_theme or active_sentiment:
            filter_text = []
            if active_theme: filter_text.append(f"Theme: {active_theme}")
            if active_sentiment: filter_text.append(f"Sentiment: {active_sentiment}")
            
            st.subheader(f"📋 Filtered Posts: {' | '.join(filter_text)}")
            
            # Load posts filtered by theme and sentiment
            theme_posts = load_posts_by_theme_sentiment(active_theme, active_sentiment, start_date_str, end_date_str)
            
            if theme_posts:
                st.success(f"📊 Found **{len(theme_posts)}** posts matching your filters")
                
                # Display filtered posts
                for i, post in enumerate(theme_posts[:20]):
                    with st.expander(f"📌 {post['title'][:80]}..." if len(post['title']) > 80 else f"📌 {post['title']}"):
                        col1, col2, col3 = st.columns([3, 1, 1])
                        
                        with col1:
                            st.markdown(f'<div class="post-card">{post["content"]}</div>', unsafe_allow_html=True)
                            if post['url']:
                                st.markdown(f"🔗 [View Original Post]({post['url']})")
                        
                        with col2:
                            sentiment_class = f"sentiment-{post['sentiment_label']}"
                            st.markdown(f"**Sentiment:** <span class='{sentiment_class}'>{post['sentiment_label'].title()}</span>", unsafe_allow_html=True)
                            st.write(f"**Score:** {post['sentiment_score']}")
                            if active_theme:
                                st.write(f"**Theme:** {active_theme}")
                        
                        with col3:
                            st.write(f"**👍 Upvotes:** {post['upvotes']}")
                            st.write(f"**💬 Comments:** {post['comments_count']}")
                            st.write(f"**👤 Author:** {post['author']}")
                            if post['created_at']:
                                try:
                                    created_date = datetime.fromisoformat(post['created_at'].replace('Z', '+00:00'))
                                    st.write(f"**📅 Date:** {created_date.strftime('%m/%d/%Y')}")
                                except:
                                    st.write(f"**📅 Date:** {post['created_at']}")
            else:
                st.info(f"📭 No posts found for the selected filters")
    
    except Exception as e:
        st.error(f"❌ Error creating themes chart: {e}")
        st.info("🎯 Themes data is available but chart failed to render")
    
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("🎯 No themes data available for selected date range.")

# Recent posts section
st.header("📝 Recent Posts")

# Use session state sentiment if available, otherwise use sidebar filter
active_sentiment_filter = st.session_state.selected_sentiment if st.session_state.selected_sentiment else sentiment_filter
posts_data = load_posts_data(start_date_str, end_date_str, active_sentiment_filter if active_sentiment_filter != "All" else "All")

if posts_data:
    if active_sentiment_filter and active_sentiment_filter != "All":
        st.info(f"Showing posts filtered by sentiment: **{active_sentiment_filter}**")
    
    for post in posts_data[:15]:  # Show top 15 posts
        with st.expander(f"🔸 {post['title'][:100]}..." if len(post['title']) > 100 else f"🔸 {post['title']}"):
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.markdown(f'<div class="post-card">{post["content"]}</div>', unsafe_allow_html=True)
                if post['url']:
                    st.markdown(f"🔗 [View Original Post]({post['url']})")
            
            with col2:
                sentiment_class = f"sentiment-{post['sentiment_label']}"
                st.markdown(f"**Sentiment:** <span class='{sentiment_class}'>{post['sentiment_label'].title()}</span>", unsafe_allow_html=True)
                st.write(f"**Score:** {post['sentiment_score']}")
                st.write(f"**Author:** {post['author']}")
            
            with col3:
                st.write(f"**👍 Upvotes:** {post['upvotes']}")
                st.write(f"**💬 Comments:** {post['comments_count']}")
                if post['created_at']:
                    try:
                        created_date = datetime.fromisoformat(post['created_at'].replace('Z', '+00:00'))
                        st.write(f"**📅 Date:** {created_date.strftime('%Y-%m-%d %H:%M')}")
                    except:
                        st.write(f"**📅 Date:** {post['created_at']}")
else:
    st.info("📭 No posts found for the selected filters.")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <b>Gusto Social Media Monitor</b> - Built with Streamlit 🚀<br>
    <small>Real-time social media sentiment analysis and monitoring</small>
</div>
""", unsafe_allow_html=True)
