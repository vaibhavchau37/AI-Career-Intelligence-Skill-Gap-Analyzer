# Installation Instructions

## Quick Fix for Current Error

The error shows that `fuzzywuzzy` is missing. Install it with:

```bash
python -m pip install fuzzywuzzy python-Levenshtein
```

## Complete Installation

### Option 1: Install All Dependencies at Once

```bash
python -m pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### Option 2: Install Manually (Windows)

Run the batch file:
```bash
install_dependencies.bat
```

### Option 3: Install Step by Step

```bash
# Core dependencies
python -m pip install fuzzywuzzy python-Levenshtein
python -m pip install pdfplumber
python -m pip install scikit-learn
python -m pip install pandas numpy
python -m pip install pyyaml
python -m pip install streamlit

# NLP model
python -m spacy download en_core_web_sm
```

## After Installation

Run the app:
```bash
streamlit run app.py
```

The app should open at: http://localhost:8501

## Verify Installation

Run the setup checker:
```bash
python check_setup.py
```

This will verify all dependencies are installed correctly.

