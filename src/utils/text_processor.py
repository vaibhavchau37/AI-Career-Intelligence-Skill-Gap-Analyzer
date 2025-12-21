"""Text processing utilities."""

import re
from typing import List, Optional
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False


def clean_text(text: str) -> str:
    """Clean and normalize text."""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s\.\,\;\:\-\/\(\)]', '', text)
    
    return text.strip()


def normalize_skill_name(skill: str) -> str:
    """Normalize skill name for matching."""
    if not skill:
        return ""
    
    # Convert to lowercase
    skill = skill.lower().strip()
    
    # Remove common prefixes/suffixes
    skill = re.sub(r'^(proficient in|experienced with|knowledge of|expert in)\s+', '', skill)
    
    # Normalize common variations
    skill = skill.replace('_', ' ').replace('-', ' ')
    
    # Remove extra spaces
    skill = re.sub(r'\s+', ' ', skill).strip()
    
    return skill


def extract_entities(text: str, entity_types: Optional[List[str]] = None) -> List[str]:
    """
    Extract named entities from text using spaCy.
    
    Args:
        text: Input text
        entity_types: Types of entities to extract (e.g., ['ORG', 'PERSON'])
                     If None, extracts all entities
    
    Returns:
        List of extracted entity texts
    """
    if not SPACY_AVAILABLE:
        return []
    
    try:
        # Try to load spaCy model (user needs to download it)
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        # Model not installed - return empty list
        return []
    
    doc = nlp(text)
    
    entities = []
    for ent in doc.ents:
        if entity_types is None or ent.label_ in entity_types:
            entities.append(ent.text)
    
    return entities


def extract_email(text: str) -> Optional[str]:
    """Extract email address from text."""
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    match = re.search(pattern, text)
    return match.group() if match else None


def extract_phone(text: str) -> Optional[str]:
    """Extract phone number from text."""
    # Common phone patterns
    patterns = [
        r'\b\d{3}-\d{3}-\d{4}\b',  # 123-456-7890
        r'\b\(\d{3}\)\s?\d{3}-\d{4}\b',  # (123) 456-7890
        r'\b\d{10}\b',  # 1234567890
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group()
    
    return None


def extract_degrees(text: str) -> List[str]:
    """Extract degree names from text."""
    degree_patterns = [
        r'\b(BS|B\.S\.|Bachelor|BA|B\.A\.|B\.Sc\.|BSc)\b',
        r'\b(MS|M\.S\.|Master|MA|M\.A\.|M\.Sc\.|MSc|M\.Tech|MTech)\b',
        r'\b(PhD|Ph\.D\.|Doctorate|D\.Sc\.)\b',
    ]
    
    degrees = []
    for pattern in degree_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        degrees.extend(matches)
    
    return list(set(degrees))

