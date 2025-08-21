# 🚀 Gusto Social Media Monitor - Streamlit Version

A beautiful, interactive dashboard for monitoring Gusto's social media presence and sentiment analysis.

## 📊 Features

- **Real-time Analytics**: Overview metrics and sentiment breakdown
- **Interactive Charts**: Sentiment trends and theme analysis with Plotly
- **Date Filtering**: Filter all data by custom date ranges
- **Theme Analysis**: Deep dive into specific topics and their sentiment
- **Recent Posts**: View and filter recent social media posts
- **Mobile Responsive**: Works perfectly on all devices

## 🎯 Live Demo

Once deployed, your dashboard will be available at: `https://your-app-name.streamlit.app`

## 🚀 Quick Deployment to Streamlit Cloud

### Step 1: Push to GitHub
1. Create a new repository on GitHub
2. Push this code to your repository

### Step 2: Deploy on Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with your GitHub account
3. Click "New app"
4. Select your repository and branch
5. Set main file path: `streamlit_app.py`
6. Click "Deploy!"

That's it! Your dashboard will be live in minutes.

## 🛠️ Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run streamlit_app.py
```

## 📁 Project Structure

```
gusto-social-monitor/
├── streamlit_app.py          # Main Streamlit application
├── requirements.txt          # Python dependencies
├── backend/                  # Your existing backend code
│   ├── database/            # Database models and connection
│   └── ...
└── README.md                # This file
```

## 🎨 Dashboard Sections

1. **Overview Metrics**: Total posts, recent activity, positive rate
2. **Sentiment Charts**: Pie chart and trend analysis
3. **Theme Analysis**: Top themes with sentiment breakdown
4. **Recent Posts**: Filterable list of social media posts

## 🔧 Configuration

The app uses your existing database models and configurations from the `backend/` directory. No additional setup required!

## 📱 Mobile Friendly

The dashboard is fully responsive and works great on:
- 📱 Mobile phones
- 📋 Tablets  
- 💻 Desktop computers

## 🌟 Advantages over Flask Version

- ✅ **Zero deployment complexity** - just push to GitHub
- ✅ **Built-in responsive design** - looks great on all devices
- ✅ **Interactive charts** - hover, zoom, pan capabilities
- ✅ **Automatic HTTPS** - secure by default
- ✅ **Free hosting** - completely free on Streamlit Cloud
- ✅ **Auto-updates** - deploys automatically when you push to GitHub

Enjoy your new Streamlit dashboard! 🎉
