"""
Resume Parser Module
Extracts text and key information from PDF and DOCX resume files.
"""

import PyPDF2
import docx
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional

class ResumeParser:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.default_skills = [
            'python', 'java', 'javascript', 'react', 'django', 'flask',
            'machine learning', 'data science', 'sql', 'aws', 'docker',
            'git', 'agile', 'scrum', 'project management', 'leadership'
        ]
        
    def extract_text_from_pdf(self, file_path: str) -> str:
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text.strip()
        except Exception as e:
            self.logger.error(f"Error extracting PDF text: {e}")
            return ""
    
    def extract_text_from_docx(self, file_path: str) -> str:
        try:
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            self.logger.error(f"Error extracting DOCX text: {e}")
            return ""
    
    def extract_text(self, file_path: str) -> str:
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if file_path.suffix.lower() == '.pdf':
            return self.extract_text_from_pdf(str(file_path))
        elif file_path.suffix.lower() in ['.docx', '.doc']:
            return self.extract_text_from_docx(str(file_path))
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
    
    def extract_email(self, text: str) -> Optional[str]:
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(pattern, text)
        return emails[0] if emails else None
    
    def extract_phone(self, text: str) -> Optional[str]:
        patterns = [
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            r'\b\(\d{3}\)\s*\d{3}[-.]?\d{4}\b',
            r'\+\d{1,3}\s*\d{3,4}\s*\d{3,4}\s*\d{3,4}'
        ]
        for pattern in patterns:
            phones = re.findall(pattern, text)
            if phones:
                return phones[0]
        return None
    
    def extract_skills(self, text: str, skill_keywords: List[str] = None) -> List[str]:
        if skill_keywords is None:
            skill_keywords = self.default_skills
        
        text_lower = text.lower()
        found_skills = []
        for skill in skill_keywords:
            if skill.lower() in text_lower:
                found_skills.append(skill)
        return list(set(found_skills))
    
    def parse_resume(self, file_path: str) -> Dict:
        try:
            text = self.extract_text(file_path)
            if not text:
                raise ValueError("No text extracted")
            
            return {
                'file_path': str(file_path),
                'filename': Path(file_path).name,
                'raw_text': text,
                'email': self.extract_email(text),
                'phone': self.extract_phone(text),
                'skills': self.extract_skills(text),
                'word_count': len(text.split()),
                'parsing_success': True
            }
        except Exception as e:
            return {
                'file_path': str(file_path),
                'filename': Path(file_path).name,
                'raw_text': "",
                'parsing_success': False,
                'error': str(e)
            }
    