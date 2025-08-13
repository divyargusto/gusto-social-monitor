# Gusto Social Media Monitor

A comprehensive social media monitoring tool that tracks mentions of Gusto across various platforms, performs sentiment analysis, and identifies themes to provide actionable insights for the business.

## 🚀 Features

- **Multi-Platform Data Collection**: Collects data from Reddit, LinkedIn, Google Reviews, G2, and other platforms
- **Advanced Sentiment Analysis**: Uses multiple NLP techniques including VADER, TextBlob, and business-specific analysis
- **Theme Extraction**: Identifies key topics and themes in discussions using LDA and predefined business categories
- **Real-time Dashboard**: Beautiful web interface with interactive charts and visualizations
- **Database Storage**: Comprehensive data storage with relationship mapping
- **Competitor Analysis**: Tracks mentions of competitors and their sentiment
- **API Endpoints**: RESTful API for data access and integration

## 📁 Project Structure

```
gusto-social-monitor/
├── backend/
│   ├── app/
│   │   ├── app.py              # Flask web application
│   │   └── templates/
│   │       └── index.html      # Dashboard HTML template
│   ├── database/
│   │   ├── models.py           # SQLAlchemy database models
│   │   └── database.py         # Database configuration and management
│   ├── data_collectors/        # Platform-specific data collectors
│   ├── analysis/              # Analysis modules
│   └── config/                # Configuration files
├── collectors/
│   └── reddit_collector.py    # Reddit data collector implementation
├── utils/
│   ├── sentiment_analyzer.py  # Sentiment analysis module
│   ├── theme_extractor.py     # Theme extraction module
│   └── data_processor.py      # Data processing pipeline
├── frontend/                  # React frontend (optional)
├── scripts/                   # Utility scripts
├── logs/                      # Log files
├── requirements.txt           # Python dependencies
├── main.py                    # Main orchestrator script
└── README.md                  # This file
```

## 🛠️ Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Git

### Setup

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd gusto-social-monitor
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your API credentials
   ```

5. **Initialize the database**:
   ```bash
   python -c "from backend.database.database import init_database; init_database()"
   ```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Database Configuration
DATABASE_URL=sqlite:///gusto_monitor.db

# Reddit API Credentials
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=GustoSocialMonitor/1.0
REDDIT_USERNAME=your_reddit_username
REDDIT_PASSWORD=your_reddit_password

# Other API credentials...
```

### Getting API Credentials

#### Reddit API
1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Choose "script" type
4. Copy the client ID and secret

#### Twitter API (Optional)
1. Apply for a Twitter Developer account
2. Create a new app in the Twitter Developer portal
3. Generate API keys and tokens

#### Google APIs (Optional)
1. Go to Google Cloud Console
2. Enable the Google Places API
3. Create credentials and copy the API key

## 🚀 Usage

### Running Data Collection

1. **Run the main monitoring script**:
   ```bash
   python main.py --days 7 --sources reddit google_reviews
   ```

2. **Available command-line options**:
   ```bash
   python main.py --help
   ```

### Starting the Web Dashboard

1. **Start the Flask application**:
   ```bash
   python backend/app/app.py
   ```

2. **Access the dashboard**:
   Open http://localhost:5000 in your web browser

### API Endpoints

The application provides several RESTful API endpoints:

- `GET /api/overview` - Overview statistics
- `GET /api/sentiment-trends` - Sentiment trends over time
- `GET /api/themes` - Theme analysis data
- `GET /api/keywords` - Top keywords and frequencies
- `GET /api/competitors` - Competitor mention analysis
- `GET /api/posts` - Recent posts with filtering
- `GET /api/platform-analysis` - Platform-specific analysis
- `GET /api/export` - Export data in JSON/CSV format

### Scheduled Data Collection

For automated data collection, you can set up a cron job:

```bash
# Run every 6 hours
0 */6 * * * cd /path/to/gusto-social-monitor && python main.py
```

## 📊 Dashboard Features

The web dashboard provides:

1. **Overview Metrics**: Total posts, average sentiment, platform distribution
2. **Sentiment Analysis**: Pie chart of sentiment distribution and trend lines
3. **Theme Analysis**: Bar chart of top themes and their relevance scores
4. **Competitor Tracking**: List of competitors with mention counts and sentiment
5. **Recent Posts**: Filterable list of recent posts with themes and sentiment
6. **Export Functionality**: Download data in CSV or JSON format

## 🔍 Analysis Features

### Sentiment Analysis
- **VADER Sentiment**: Optimized for social media text
- **TextBlob**: General-purpose sentiment analysis
- **Business Context**: Custom analysis for payroll/HR domain
- **Combined Scoring**: Weighted combination of multiple methods

### Theme Extraction
- **Predefined Themes**: Business-specific categories (pricing, customer service, etc.)
- **LDA Topic Modeling**: Automated topic discovery
- **Keyword Extraction**: TF-IDF based important terms
- **Text Clustering**: Groups similar posts together

### Data Processing
- **Deduplication**: Removes duplicate posts across platforms
- **Data Cleaning**: Cleans and normalizes text data
- **Competitor Detection**: Identifies mentions of competing products
- **Engagement Metrics**: Tracks likes, shares, comments, and scores

## 🗃️ Database Schema

The application uses a comprehensive database schema with the following main tables:

- **social_media_posts**: Main posts and comments
- **themes**: Identified themes and topics
- **post_themes**: Relationship between posts and themes
- **keywords**: Extracted keywords
- **post_keywords**: Keyword mentions in posts
- **competitor_mentions**: Competitor references
- **sentiment_trends**: Aggregated sentiment data over time

## 📈 Extending the Tool

### Adding New Data Collectors

1. Create a new collector class in `collectors/` directory
2. Implement the `collect_data()` method
3. Add the collector to the main orchestrator in `main.py`

Example:
```python
class NewPlatformCollector:
    async def collect_data(self, keywords, days_back):
        # Implementation here
        return collected_data
```

### Adding Custom Analysis

1. Extend the analysis modules in `utils/`
2. Add new methods to existing classes or create new ones
3. Integrate with the data processing pipeline

### Customizing Themes

Edit the `predefined_themes` dictionary in `utils/theme_extractor.py` to add business-specific themes.

## 🔐 Security and Rate Limiting

- **API Rate Limiting**: Respects platform rate limits with automatic delays
- **Credential Management**: Uses environment variables for sensitive data
- **Data Privacy**: Stores minimal personal information
- **Error Handling**: Graceful handling of API failures and timeouts

## 🐛 Troubleshooting

### Common Issues

1. **Reddit API "429 Too Many Requests"**:
   - Increase the `rate_limit_delay` in `reddit_collector.py`
   - Ensure your Reddit credentials are correct

2. **Database Connection Errors**:
   - Check the `DATABASE_URL` environment variable
   - Ensure the database file has write permissions

3. **Missing NLTK Data**:
   ```bash
   python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"
   ```

4. **Web Dashboard Not Loading Data**:
   - Check the Flask application logs
   - Ensure the database has been initialized
   - Verify API endpoints are accessible

### Logs

Application logs are stored in:
- Console output (real-time)
- `gusto_monitor.log` file
- Platform-specific log files in `logs/` directory

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For support and questions:
- Create an issue in the GitHub repository
- Check the troubleshooting section above
- Review the application logs for error details

## 🔮 Future Enhancements

- **Real-time Streaming**: WebSocket support for live updates
- **Machine Learning**: Predictive sentiment analysis
- **Advanced Visualizations**: More chart types and interactive features
- **Alerting System**: Email/Slack notifications for significant changes
- **Mobile App**: Native mobile application for monitoring
- **Advanced NLP**: Entity recognition and relationship extraction 