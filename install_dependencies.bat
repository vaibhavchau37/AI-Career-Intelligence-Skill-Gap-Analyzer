@echo off
echo Installing required dependencies...
echo.

python -m pip install fuzzywuzzy python-Levenshtein
python -m pip install pdfplumber
python -m pip install scikit-learn
python -m pip install pandas numpy
python -m pip install pyyaml
python -m pip install streamlit

echo.
echo Installing spaCy model...
python -m spacy download en_core_web_sm

echo.
echo Installation complete!
echo.
echo To run the app, use: streamlit run app.py
pause

