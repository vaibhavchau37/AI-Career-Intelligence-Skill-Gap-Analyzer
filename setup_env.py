"""
Setup environment variables for API keys.

Run this script to create .env file with your API keys.
"""

import os
from pathlib import Path

def setup_env():
    """Create .env file with API keys."""
    env_file = Path(".env")
    
    if env_file.exists():
        print("⚠️  .env file already exists!")
        response = input("Do you want to overwrite it? (y/n): ")
        if response.lower() != 'y':
            print("Cancelled.")
            return
    
    print("Setting up .env file...")
    print("Enter your API keys (press Enter to skip):")
    print()
    
    openai_key = input("OpenAI API Key (optional): ").strip()
    gemini_key = input("Google Gemini API Key (optional): ").strip()
    adzuna_app_id = input("Adzuna App ID: ").strip()
    adzuna_api_key = input("Adzuna API Key: ").strip()
    
    if not adzuna_app_id or not adzuna_api_key:
        print("⚠️  Warning: Adzuna API keys are required for real-time job data!")
    
    env_content = f"""# API Keys (AI Models)
OPENAI_API_KEY={openai_key or 'your_openai_api_key_here'}
GOOGLE_GEMINI_API_KEY={gemini_key or 'your_gemini_api_key_here'}

# Job API Keys
# Adzuna API - Get your keys from https://developer.adzuna.com/
ADZUNA_APP_ID={adzuna_app_id or 'your_adzuna_app_id_here'}
ADZUNA_API_KEY={adzuna_api_key or 'your_adzuna_api_key_here'}
"""
    
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    print()
    print("✅ .env file created successfully!")
    print("⚠️  Remember: Never commit .env file to version control!")


if __name__ == "__main__":
    setup_env()

