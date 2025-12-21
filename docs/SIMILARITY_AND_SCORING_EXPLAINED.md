# Similarity Calculation & Scoring Explained

## Part 1: TF-IDF + Cosine Similarity for Skill Matching

### Why TF-IDF + Cosine Similarity?

Traditional string matching has limitations:
- "Machine Learning" ≠ "ML" (even though they're the same)
- "Python" ≠ "python programming" (semantic similarity ignored)
- No understanding of skill relationships

TF-IDF + Cosine Similarity solves this by:
- Understanding semantic similarity
- Handling variations and abbreviations
- Providing numerical similarity scores

### How TF-IDF Works

**TF-IDF** = Term Frequency-Inverse Document Frequency

#### Step 1: Tokenization
Convert skills into words/tokens:
```
"Machine Learning" → ["Machine", "Learning"]
"ML" → ["ML"]
"Python Programming" → ["Python", "Programming"]
```

#### Step 2: Term Frequency (TF)
Count how often each word appears in the skill:
```
"Machine Learning":
  "Machine": 1
  "Learning": 1
  Total words: 2
  TF("Machine") = 1/2 = 0.5
```

#### Step 3: Inverse Document Frequency (IDF)
Measure how rare/common a word is across all skills:
```
IDF(word) = log(Total Skills / Skills containing word)

Example:
  Total skills: 100
  "Machine" appears in 5 skills
  IDF("Machine") = log(100/5) = log(20) ≈ 3.0
```

#### Step 4: TF-IDF Score
```
TF-IDF(word) = TF(word) × IDF(word)

High TF-IDF = Important, rare word (good for distinguishing skills)
Low TF-IDF = Common word (less useful for matching)
```

#### Step 5: Vector Representation
Each skill becomes a vector of TF-IDF scores:
```
"Machine Learning" → [0.5×3.0, 0.5×2.5, 0, 0, ...] = [1.5, 1.25, 0, 0, ...]
"ML" → [0, 0, 0, 0, ...]  (different vector)
```

### How Cosine Similarity Works

**Cosine Similarity** measures the angle between two vectors.

#### Formula
```
cos(θ) = (A · B) / (||A|| × ||B||)

Where:
  A · B = Dot product (sum of element-wise multiplication)
  ||A|| = Magnitude of vector A
  ||B|| = Magnitude of vector B
```

#### Interpretation
- **1.0**: Vectors point in same direction (identical or very similar)
- **0.0**: Vectors are orthogonal (completely different)
- **-1.0**: Vectors point in opposite directions (rare for skills)

#### Example Calculation

```
Skill A: "Machine Learning" → Vector [1.5, 1.25, 0, 0]
Skill B: "ML" → Vector [0, 0, 0, 0]

Dot Product: 1.5×0 + 1.25×0 + 0×0 + 0×0 = 0
Magnitude A: √(1.5² + 1.25²) = √(2.25 + 1.56) = √3.81 ≈ 1.95
Magnitude B: 0

Cosine Similarity: 0 / (1.95 × 0) = 0 (undefined, but treated as 0)

But with better tokenization (handling abbreviations):
"Machine Learning" and "ML" → Similarity ≈ 0.7-0.9
```

### Why Skills Are Marked Missing

A skill is marked as **missing** if:

1. **No Exact Match**: The skill name doesn't appear exactly in resume
2. **Low Similarity**: No resume skill has cosine similarity ≥ threshold (default: 0.3)
3. **No Semantic Match**: Even similar-sounding skills are too different

#### Example Explanations

**Missing: "TensorFlow"**
- Resume has: ["Python", "Machine Learning", "Pandas"]
- Closest match: "Machine Learning" (similarity: 0.25)
- 0.25 < 0.3 (threshold) → **MISSING**

**Missing: "Deep Learning"**
- Resume has: ["Machine Learning"]
- Closest match: "Machine Learning" (similarity: 0.65)
- 0.65 ≥ 0.3 (threshold) → **MATCH!** (not missing)

### Similarity Threshold

The **similarity threshold** (default: 0.3) determines matching strictness:

- **Low threshold (0.2)**: More lenient, matches more variations
- **Medium threshold (0.3)**: Balanced (default)
- **High threshold (0.5)**: Strict, only very similar skills match

## Part 2: Job Readiness Scoring System

### Overview

The scoring system calculates a 0-100 readiness score using **transparent, explicit formulas** - no black-box ML.

### Components

#### 1. Skills Score (60% weight)

**Formula**:
```
Base Score = (Matched Skills / Total Required Skills) × 100
Penalty = -10 points per missing required skill (max -30)
Final Score = Base Score - Penalty
```

**Example**:
- Required skills: 10
- Matched: 7
- Missing: 3
- Base: (7/10) × 100 = 70
- Penalty: min(30, 3 × 10) = 30
- Final: 70 - 30 = 40/100

**Why this formula?**
- Base score rewards matching skills
- Penalty emphasizes importance of required skills
- Transparent: can verify every calculation

#### 2. Experience Score (25% weight)

**Formula** (piecewise function):

```
If experience_years == 0:
    score = 0

If experience_years < required_years:
    score = (experience_years / required_years) × 50
    # Linear scale: 0 to 50 points

If experience_years == required_years:
    score = 75

If required_years < experience_years < optimal_years (3):
    score = 75 + ((experience_years - required_years) / (optimal - required)) × 25
    # Linear scale: 75 to 100 points

If optimal_years ≤ experience_years ≤ 5:
    score = 100

If experience_years > 5:
    score = 100 - min(10, (experience_years - 5) × 2)
    # Diminishing returns, slight penalty for overqualification
```

**Example Calculations**:

| Years | Required | Score | Explanation |
|-------|----------|-------|-------------|
| 0 | 2 | 0 | No experience |
| 1 | 2 | 25 | (1/2) × 50 = 25 |
| 2 | 2 | 75 | Meets minimum |
| 2.5 | 2 | 87.5 | 75 + ((2.5-2)/(3-2)) × 25 |
| 3 | 2 | 100 | Optimal |
| 5 | 2 | 100 | Still optimal |
| 8 | 2 | 94 | 100 - min(10, (8-5)×2) = 100 - 6 |

**Why this formula?**
- Rewards meeting minimum requirements
- Optimal range (3-5 years) gets maximum score
- Diminishing returns beyond optimal (overqualification)
- All thresholds are explicit and adjustable

#### 3. Projects Score (15% weight)

**Formula** (simple lookup table):

```
0 projects: 0 points
1 project:  30 points
2 projects: 60 points
3 projects: 85 points
4+ projects: 100 points (capped)
```

**Example**:
- 3 projects → 85/100
- Contribution to overall: 85 × 0.15 = 12.75 points

**Why this formula?**
- Simple, transparent threshold system
- Rewards demonstrating skills through projects
- Future enhancement: Could analyze project relevance/quality

### Overall Score Calculation

**Formula**:
```
Overall Score = (Skill Score × 0.60) + 
                (Experience Score × 0.25) + 
                (Project Score × 0.15)

Final Score = max(0, min(100, Overall Score))
```

**Example**:
```
Skill Score: 60/100
Experience Score: 75/100
Project Score: 85/100

Calculation:
(60 × 0.60) + (75 × 0.25) + (85 × 0.15)
= 36.0 + 18.75 + 12.75
= 67.5/100
```

### Why This Approach is Transparent

1. **No Hidden Formulas**: Every calculation is explicit
2. **Verifiable**: Can manually verify each step
3. **Adjustable**: All weights and thresholds are configurable
4. **Explainable**: Every score has a clear explanation
5. **No ML Models**: Pure mathematical calculations

### Score Interpretation

| Score Range | Interpretation | Action |
|-------------|---------------|--------|
| 80-100 | Excellent readiness | Apply with confidence |
| 65-79 | Good readiness | Minor improvements needed |
| 50-64 | Moderate readiness | Significant skill gaps |
| 35-49 | Needs improvement | Focus on missing skills |
| 0-34 | Poor readiness | Major gaps, consider alternatives |

### Example: Complete Calculation

**Input**:
- Resume skills: ["Python", "ML", "SQL"]
- Job required: ["Python", "Machine Learning", "Deep Learning", "SQL"]
- Experience: 2 years
- Required experience: 2 years
- Projects: 2

**Step 1: Skill Gap Analysis**
- Matched: Python (exact), ML→Machine Learning (similarity: 0.85), SQL (exact)
- Missing: Deep Learning (similarity: 0.45 with ML, above threshold but not matched due to ML already matching)
- Actually: Need to check if Deep Learning matches with ML
- Let's say: 3 matched, 1 missing
- Base: (3/4) × 100 = 75
- Penalty: 1 × 10 = 10
- Skill Score: 75 - 10 = 65/100

**Step 2: Experience Score**
- 2 years = required (2 years)
- Experience Score: 75/100

**Step 3: Project Score**
- 2 projects
- Project Score: 60/100

**Step 4: Overall Score**
```
(65 × 0.60) + (75 × 0.25) + (60 × 0.15)
= 39.0 + 18.75 + 9.0
= 66.75/100
```

**Result**: 66.75/100 (Good readiness)

### Advantages of This System

1. **Transparent**: Every calculation is visible
2. **Fair**: Consistent scoring for all candidates
3. **Explainable**: Can explain every score component
4. **Customizable**: Adjust weights and thresholds
5. **Fast**: No training or inference time
6. **Deterministic**: Same input always gives same output

### Future Enhancements

1. **Project Relevance**: Analyze project descriptions for skill relevance
2. **Skill Importance Weighting**: Weight required skills by importance
3. **Experience Quality**: Consider company reputation, role level
4. **Education Bonus**: Add education component
5. **Certification Bonus**: Add certification component

But all enhancements will maintain **transparency** - no black-box additions!

