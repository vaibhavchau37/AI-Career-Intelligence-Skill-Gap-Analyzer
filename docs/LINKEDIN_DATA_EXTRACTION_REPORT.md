# LinkedIn Jobs Data Extraction Summary

## 📊 Extraction Results

### Dataset Information
- **Source**: LinkedIn_Jobs_Data_India.csv
- **Total Jobs**: 949
- **Unique Job Titles**: 495
- **Unique Skills Extracted**: 128

---

## 🎯 Top 20 Job Titles (by frequency)

| Rank | Job Title | Count |
|------|-----------|-------|
| 1 | Data Scientist | 47 |
| 2 | Product Manager | 35 |
| 3 | Business Development Manager | 28 |
| 4 | Content Writer | 22 |
| 5 | Financial Analyst | 20 |
| 6 | Copywriter | 19 |
| 7 | Software Engineer | 18 |
| 8 | Mechanical Design Engineer | 18 |
| 9 | Human Resources Business Partner | 17 |
| 10 | Human Resources Manager | 16 |
| 11 | Assistant Manager - Field Sales | 15 |
| 12 | Social Media Executive | 15 |
| 13 | Web Developer | 14 |
| 14 | Associate Product Manager | 12 |
| 15 | Machine Learning Engineer | 10 |
| 16 | Finance Analyst | 9 |
| 17 | Mechanical Engineer | 9 |
| 18 | Business Development Executive | 7 |
| 19 | Staff Product Manager | 7 |
| 20 | Product manager | 7 |

---

## 💡 Top 30 Skills (by frequency)

| Rank | Skill | Jobs |
|------|-------|------|
| 1 | JavaScript | 6 |
| 2 | Web Developer | 4 |
| 3 | HTML5 | 4 |
| 4 | CSS | 4 |
| 5 | Problem Solving | 3 |
| 6 | Security | 3 |
| 7 | AJAX | 2 |
| 8 | Data Structures | 2 |
| 9 | MySQL | 2 |
| 10 | OOP | 2 |
| 11 | GitHub | 2 |
| 12 | Debugging | 2 |
| 13 | REST | 2 |
| 14 | Java | 2 |
| 15 | JSON | 2 |
| 16 | Web Technologies | 2 |
| 17 | PHP | 2 |
| 18 | HTML | 2 |
| 19 | Machine Learning | 2 |
| 20 | MVC | 1 |
| 21 | Git | 1 |
| 22 | AngularJS | 1 |
| 23 | PostgreSQL | 1 |
| 24 | Android Development | 1 |
| 25 | Algorithms | 1 |
| 26 | Mobile | 1 |
| 27 | MVVM | 1 |
| 28 | XML | 1 |
| 29 | Visual Studio | 1 |
| 30 | Bootstrap | 1 |

---

## 📁 Generated Files

### 1. **data/extracted_skills.json**
   - Complete list of all extracted skills
   - Skills sorted by frequency
   - Total count: 128 unique skills

### 2. **data/extracted_job_titles.json**
   - Complete list of all job titles
   - Titles sorted by frequency
   - Total count: 495 unique titles

### 3. **data/skills/extracted_skill_taxonomy.json**
   - Skills categorized into:
     - Programming Languages
     - Frameworks & Libraries
     - Databases
     - Tools & Technologies
     - Concepts & Methodologies
     - Soft Skills

### 4. **New Job Role YAML Files Created**
   - `software_engineer.yaml` (18 jobs in dataset)
   - `web_developer.yaml` (14 jobs in dataset)
   - `product_manager.yaml` (35 jobs in dataset)
   - `financial_analyst.yaml` (20 jobs in dataset)
   - `business_development_manager.yaml` (28 jobs in dataset)

---

## 🎯 Available Job Roles in Project

The project now supports **7 job roles**:

1. **Data Scientist** (Original - 47 jobs in LinkedIn data)
2. **ML Engineer** (Original - 10 jobs in LinkedIn data)
3. **Software Engineer** (New - 18 jobs)
4. **Web Developer** (New - 14 jobs)
5. **Product Manager** (New - 35 jobs)
6. **Financial Analyst** (New - 20 jobs)
7. **Business Development Manager** (New - 28 jobs)

---

## 🔧 How to Use

### 1. Run Extraction Script
```bash
python extract_skills_titles.py
```

### 2. Run Demo
```bash
python demo_linkedin_data.py
```

### 3. Start Web App
```bash
streamlit run app.py
```

---

## 📈 Key Insights

### Most In-Demand Roles (India Market)
1. **Data Scientist** - 47 jobs
2. **Product Manager** - 35 jobs
3. **Business Development Manager** - 28 jobs

### Most Required Skills
1. **JavaScript** - Frontend development
2. **HTML5 & CSS** - Web fundamentals
3. **Problem Solving** - Universal skill

### Industry Focus
- **Engineering & IT**: Majority of jobs
- **Business & Sales**: Significant presence
- **Finance & Analytics**: Growing demand

---

## 🚀 Project Enhancement Features

1. **Real Job Data Integration**: Based on actual LinkedIn job postings from India
2. **Skill Mapping**: 128 real-world skills extracted
3. **Multi-Role Support**: 7 diverse career paths
4. **Data-Driven**: Analysis based on 949 actual job listings
5. **API Integration**: Ready for real-time job matching with Adzuna API

---

## 📊 Next Steps

1. ✅ Skills and job titles extracted
2. ✅ Job role profiles created
3. ✅ Data files generated
4. 🎯 Use in Streamlit app for:
   - Resume parsing
   - Skill gap analysis
   - Job readiness scoring
   - Career recommendations
   - Real-time job matching

---

## 🔗 Data Sources

- **LinkedIn Jobs Data**: 949 job postings from India
- **Job Roles**: Data Scientist, Software Engineer, Product Manager, etc.
- **Skills**: JavaScript, Python, Machine Learning, etc.
- **Locations**: Bangalore, Mumbai, Delhi, Hyderabad, Chennai, Pune, etc.

---

**Generated on**: January 17, 2026
**Project**: AI Career Intelligence & Skill Gap Analyzer
