"""
CV Parsing Service
Extract text from PDF/DOCX and parse skills, experience, education
"""
import re
import unicodedata
from typing import Dict, List, Optional
from pathlib import Path


# Load skill aliases from CSV
def load_skill_aliases() -> Dict[str, str]:
    """Load skill alias mapping from CSV file"""
    aliases = {}
    csv_path = Path(__file__).parent.parent.parent / 'data' / 'skill_alias.csv'
    
    if not csv_path.exists():
        # Return default aliases if file doesn't exist
        return {
            'python': 'Python',
            'py': 'Python',
            'javascript': 'JavaScript',
            'js': 'JavaScript',
            'react': 'React',
            'reactjs': 'React',
            'react.js': 'React',
            'node': 'Node.js',
            'nodejs': 'Node.js',
            'postgresql': 'PostgreSQL',
            'postgres': 'PostgreSQL',
            'machine learning': 'Machine Learning',
            'ml': 'Machine Learning',
            'deep learning': 'Deep Learning',
            'dl': 'Deep Learning',
            'sql': 'SQL',
            'html': 'HTML',
            'css': 'CSS',
            'docker': 'Docker',
            'kubernetes': 'Kubernetes',
            'aws': 'AWS',
            'azure': 'Azure',
            'gcp': 'GCP',
            'tensorflow': 'TensorFlow',
            'pytorch': 'PyTorch',
            'pandas': 'pandas',
            'numpy': 'NumPy',
            'scikit-learn': 'scikit-learn',
            'fastapi': 'FastAPI',
            'django': 'Django',
            'flask': 'Flask',
            'express': 'Express.js',
            'mongodb': 'MongoDB',
            'redis': 'Redis',
            'git': 'Git',
            'linux': 'Linux',
            'agile': 'Agile',
            'scrum': 'Scrum',
        }
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split(',', 1)
            if len(parts) == 2:
                canonical = parts[0].strip()
                alias_list = parts[1].strip().split(',')
                for alias in alias_list:
                    aliases[alias.strip().lower()] = canonical
    
    return aliases


def normalize_text(text: str) -> str:
    """Normalize Unicode and clean text"""
    # NFC normalization
    text = unicodedata.normalize('NFC', text)
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove special characters but keep Vietnamese
    text = re.sub(r'[^\w\s.,;:!?()\-\n]', '', text)
    
    return text.strip()


def remove_diacritics(text: str) -> str:
    """Remove Vietnamese diacritics for search"""
    nfd = unicodedata.normalize('NFD', text)
    no_combining = ''.join(c for c in nfd if unicodedata.category(c) != 'Mn')
    return no_combining


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF file using PyMuPDF"""
    try:
        import fitz  # PyMuPDF
        
        doc = fitz.open(file_path)
        text = ""
        
        for page in doc:
            text += page.get_text()
        
        doc.close()
        return normalize_text(text)
    
    except ImportError:
        raise Exception("PyMuPDF not installed. Install with: pip install PyMuPDF")
    except Exception as e:
        raise Exception(f"Failed to extract PDF: {str(e)}")


def extract_text_from_docx(file_path: str) -> str:
    """Extract text from DOCX file using python-docx"""
    try:
        from docx import Document
        
        doc = Document(file_path)
        text = ""
        
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        
        return normalize_text(text)
    
    except ImportError:
        raise Exception("python-docx not installed. Install with: pip install python-docx")
    except Exception as e:
        raise Exception(f"Failed to extract DOCX: {str(e)}")


def extract_skills(text: str, skill_aliases: Optional[Dict[str, str]] = None) -> List[str]:
    """Extract skills from CV text using keyword matching"""
    if skill_aliases is None:
        skill_aliases = load_skill_aliases()
    
    found_skills = set()
    text_lower = text.lower()
    
    # Check each alias
    for alias, canonical in skill_aliases.items():
        # Use word boundary matching for better accuracy
        pattern = r'\b' + re.escape(alias) + r'\b'
        if re.search(pattern, text_lower):
            found_skills.add(canonical)
    
    return list(found_skills)


def extract_experience_years(text: str) -> float:
    """Extract years of experience from CV text"""
    # Look for patterns like "X năm kinh nghiệm", "X years experience", "kinh nghiệm X năm"
    patterns = [
        r'(\d+)\s*(?:năm|year|yr)\s*(?:kinh nghiệm|experience|exp)',
        r'(?:kinh nghiệm|experience|exp)\s*(?:[-:]?\s*)?(\d+)\s*(?:năm|year|yr)?',
        r'(\d+)\+?\s*(?:years|năm)\s+(?:of\s+)?(?:experience|kinh nghiệm)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                continue
    
    return 0.0


def extract_education(text: str) -> List[str]:
    """Extract education information from CV"""
    education = []
    
    # Look for degree patterns
    degree_patterns = [
        r'(cử nhân|bachelor|thạc sĩ|master|tiến sĩ|phd|doctorate)[^\n]*',
        r'(đại học|university|college)[^\n]*(?:công nghệ thông tin|computer science|IT)',
    ]
    
    for pattern in degree_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        education.extend(matches)
    
    return list(set(education))[:3]  # Return unique, max 3


def parse_cv(file_path: str, file_type: str = 'pdf') -> Dict:
    """
    Main CV parsing function
    
    Args:
        file_path: Path to CV file
        file_type: 'pdf' or 'docx'
    
    Returns:
        Dict with parsed data: skills, experience_years, education, text
    """
    # Extract text
    if file_type.lower() == 'pdf':
        text = extract_text_from_pdf(file_path)
    elif file_type.lower() == 'docx':
        text = extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")
    
    # Load skill aliases
    skill_aliases = load_skill_aliases()
    
    # Extract information
    skills = extract_skills(text, skill_aliases)
    experience_years = extract_experience_years(text)
    education = extract_education(text)
    
    return {
        'text': text,
        'text_nodiacritic': remove_diacritics(text),
        'skills': skills,
        'experience_years': experience_years,
        'education': education,
    }


if __name__ == '__main__':
    # Test with a sample file
    import sys
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        file_type = file_path.split('.')[-1].lower()
        
        result = parse_cv(file_path, file_type)
        
        print("=== CV Parsing Result ===")
        print(f"Skills found ({len(result['skills'])}): {', '.join(result['skills'])}")
        print(f"Experience: {result['experience_years']} years")
        print(f"Education: {', '.join(result['education'])}")
    else:
        print("Usage: python cv_parser.py <path_to_cv_file>")
