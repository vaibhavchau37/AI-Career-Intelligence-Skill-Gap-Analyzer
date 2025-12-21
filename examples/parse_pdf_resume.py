"""
Example: Parse a PDF Resume

This script demonstrates how to use the PDFResumeParser to extract
structured information from a resume PDF file.

Usage:
    python examples/parse_pdf_resume.py path/to/resume.pdf
"""

import sys
import json
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.pdf_resume_parser import PDFResumeParser


def main():
    """
    Main function to parse a PDF resume.
    """
    print("=" * 60)
    print("PDF Resume Parser - Example")
    print("=" * 60)
    print()
    
    # Step 1: Initialize the parser
    print("Initializing PDF Resume Parser...")
    parser = PDFResumeParser()
    print("✓ Parser initialized\n")
    
    # Step 2: Get PDF file path
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        # Default: look for sample PDF in data/examples
        pdf_path = "data/examples/sample_resume.pdf"
        print(f"No PDF path provided. Looking for: {pdf_path}")
        print("Usage: python examples/parse_pdf_resume.py <path_to_pdf>")
        print()
    
    # Check if file exists
    if not Path(pdf_path).exists():
        print(f"❌ Error: PDF file not found: {pdf_path}")
        print("\nPlease provide a valid PDF file path.")
        print("Example: python examples/parse_pdf_resume.py my_resume.pdf")
        return
    
    # Step 3: Parse the PDF
    print(f"Parsing PDF: {pdf_path}")
    print("-" * 60)
    
    try:
        # Parse the PDF and get structured data
        result = parser.parse_pdf(pdf_path)
        
        # Step 4: Display results
        print("\n📄 Parsed Resume Data:")
        print("=" * 60)
        
        # Display basic information
        if result.get("name"):
            print(f"\n👤 Name: {result['name']}")
        if result.get("email"):
            print(f"📧 Email: {result['email']}")
        if result.get("phone"):
            print(f"📞 Phone: {result['phone']}")
        
        # Display skills
        if result.get("skills"):
            print(f"\n💼 Skills ({len(result['skills'])} found):")
            for skill in result['skills']:
                print(f"  • {skill}")
        else:
            print("\n💼 Skills: No skills found")
        
        # Display education
        if result.get("education"):
            print(f"\n🎓 Education ({len(result['education'])} entries):")
            for edu in result['education']:
                edu_str = ""
                if edu.get("degree"):
                    edu_str += edu["degree"]
                if edu.get("institution"):
                    if edu_str:
                        edu_str += " from "
                    edu_str += edu["institution"]
                if edu.get("year"):
                    edu_str += f" ({edu['year']})"
                print(f"  • {edu_str if edu_str else str(edu)}")
        else:
            print("\n🎓 Education: No education information found")
        
        # Display experience
        if result.get("experience"):
            print(f"\n💼 Experience ({len(result['experience'])} entries):")
            for exp in result['experience']:
                exp_str = ""
                if exp.get("title"):
                    exp_str += exp["title"]
                if exp.get("company"):
                    if exp_str:
                        exp_str += " at "
                    exp_str += exp["company"]
                if exp.get("dates"):
                    exp_str += f" ({exp['dates']})"
                print(f"  • {exp_str if exp_str else str(exp)}")
        else:
            print("\n💼 Experience: No experience information found")
        
        # Display projects
        if result.get("projects"):
            print(f"\n🚀 Projects ({len(result['projects'])} found):")
            for i, project in enumerate(result['projects'], 1):
                print(f"  {i}. {project[:100]}{'...' if len(project) > 100 else ''}")
        else:
            print("\n🚀 Projects: No projects found")
        
        # Step 5: Save to JSON file
        output_json_path = Path(pdf_path).stem + "_parsed.json"
        json_output = parser.parse_to_json(pdf_path, output_json_path)
        
        print("\n" + "=" * 60)
        print(f"✅ Parsing complete!")
        print(f"📁 JSON output saved to: {output_json_path}")
        print("=" * 60)
        
        # Display JSON (first 500 chars)
        print("\n📋 JSON Output Preview:")
        print("-" * 60)
        print(json_output[:500] + "..." if len(json_output) > 500 else json_output)
        
    except Exception as e:
        print(f"\n❌ Error parsing PDF: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure the PDF is not password-protected")
        print("2. Ensure the PDF contains text (not just images)")
        print("3. Install required libraries: pip install pdfplumber spacy")
        print("4. Download spaCy model: python -m spacy download en_core_web_sm")


if __name__ == "__main__":
    main()

