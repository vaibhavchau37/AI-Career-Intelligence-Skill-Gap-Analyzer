"""Create .env file with API keys."""

env_content = """# API Keys (AI Models)
# Replace with your actual API keys
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_GEMINI_API_KEY=your_google_gemini_api_key_here

# Job API Keys
# Adzuna API - Get your keys from https://developer.adzuna.com/
ADZUNA_APP_ID=your_adzuna_app_id_here
ADZUNA_API_KEY=your_adzuna_api_key_here
"""

with open(".env", "w") as f:
    f.write(env_content)

print("✅ .env file created successfully!")

