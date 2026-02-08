# API Integration Guide

## Overview

The app now supports real-time job data from India using Adzuna API, with optional AI enhancements using OpenAI and Google Gemini.

## Setup

### 1. Get API Keys

#### Adzuna API (Required for Real-Time Jobs)
1. Go to https://developer.adzuna.com/
2. Sign up for a free account
3. Get your App ID and API Key
4. Free tier: 10,000 requests/month

#### OpenAI API (Optional - for AI enhancements)
1. Go to https://platform.openai.com/
2. Create an account and get API key
3. Add credits to your account

#### Google Gemini API (Optional - for AI enhancements)
1. Go to https://makersuite.google.com/app/apikey
2. Create API key
3. Free tier available

### 2. Configure Environment Variables

**Option 1: Use setup script**
```bash
python setup_env.py
```

**Option 2: Create .env file manually**
Create a `.env` file in the project root:

```env
# API Keys (AI Models)
OPENAI_API_KEY=sk-proj-your-key-here
GOOGLE_GEMINI_API_KEY=your-gemini-key-here

# Job API Keys
ADZUNA_APP_ID=your-app-id
ADZUNA_API_KEY=your-api-key
```

**Option 3: Set environment variables directly**
```bash
# Windows
set ADZUNA_APP_ID=your-app-id
set ADZUNA_API_KEY=your-api-key

# Linux/Mac
export ADZUNA_APP_ID=your-app-id
export ADZUNA_API_KEY=your-api-key
```

### 3. Install Dependencies

```bash
pip install requests python-dotenv

# Optional: For AI enhancements
pip install openai  # For OpenAI
pip install google-generativeai  # For Gemini
```

## Features

### Real-Time Job Listings (India)

The app now fetches real-time job listings from India:

1. **In "Select Role" Tab:**
   - Click "Fetch Real-Time Jobs" button
   - See recent job listings for selected role
   - View job details, salary, location, company

2. **In "Role Suitability" Tab:**
   - See total job count in India for each role
   - Market statistics

### AI Enhancements (Optional)

If OpenAI or Gemini keys are configured:

- Enhanced skill gap explanations
- AI-powered learning suggestions
- Personalized recommendations

## Usage

### Fetching Jobs

```python
from src.api.job_market_analyzer import JobMarketAnalyzer

analyzer = JobMarketAnalyzer()
jobs = analyzer.get_jobs_for_role("ML Engineer", location="India", limit=10)

for job in jobs:
    print(f"{job['title']} at {job['company']}")
    print(f"Location: {job['location']}")
    print(f"URL: {job['url']}")
```

### Getting Market Statistics

```python
stats = analyzer.get_market_statistics("Data Scientist", location="India")
print(f"Total jobs: {stats['total_jobs']}")
```

## API Limits

- **Adzuna Free Tier:** 10,000 requests/month
- **OpenAI:** Pay per use (check pricing)
- **Gemini:** Free tier available

## Troubleshooting

### "API not configured" Error
- Check that .env file exists
- Verify API keys are correct
- Ensure python-dotenv is installed

### "No jobs found"
- Try different keywords
- Check if location is correct
- Verify API keys are valid

### Rate Limiting
- Adzuna: 10,000 requests/month (free tier)
- Add delays between requests if needed

## Security Notes

⚠️ **IMPORTANT:**
- Never commit .env file to git
- .env is already in .gitignore
- Don't share API keys publicly
- Rotate keys if exposed

## Example .env File

```env
# Required for real-time jobs
ADZUNA_APP_ID=77bcc652
ADZUNA_API_KEY=63bb27ed5e9d95dede33739fc8133d4d

# Optional: AI enhancements
OPENAI_API_KEY=sk-proj-...
GOOGLE_GEMINI_API_KEY=AIzaSy...
```

## Next Steps

1. Get Adzuna API keys
2. Create .env file with keys
3. Restart the Streamlit app
4. Click "Fetch Real-Time Jobs" in the app
5. See real job listings from India!

