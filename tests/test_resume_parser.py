"""
Unit tests for ResumeParser
"""

import unittest
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "src"))

from resume_parser import ResumeParser

class TestResumeParser(unittest.TestCase):
    def setUp(self):
        self.parser = ResumeParser()

    def test_extract_email(self):
        text = "Contact me at john.doe@example.com"
        email = self.parser.extract_email(text)
        self.assertEqual(email, "john.doe@example.com")

    def test_extract_phone(self):
        text = "Call me at 555-123-4567"
        phone = self.parser.extract_phone(text)
        self.assertTrue(phone in ["555-123-4567", "(555) 123-4567"])

    def test_extract_skills(self):
        text = "Experienced in Python, Java, and machine learning"
        skills = self.parser.extract_skills(text)
        self.assertIn("python", [s.lower() for s in skills])
        self.assertIn("java", [s.lower() for s in skills])
        self.assertIn("machine learning", [s.lower() for s in skills])

if __name__ == "__main__":
    unittest.main()
