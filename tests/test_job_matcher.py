"""
Integration tests for JobMatcher
"""

import unittest
import tempfile
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "src"))

class TestJobMatcher(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.resume_dir = Path(self.temp_dir.name) / "resumes"
        self.job_dir = Path(self.temp_dir.name) / "jobs"
        self.output_dir = Path(self.temp_dir.name) / "output"

        self.resume_dir.mkdir()
        self.job_dir.mkdir()
        self.output_dir.mkdir()
        
        # Add a simple dummy resume file (can be empty for testing)
        (self.resume_dir / "test_resume.txt").write_text("This is a test resume with python and django experience.")

        # Add a simple job description in text
        self.job_text = "Looking for a Python developer with django experience."
        (self.job_dir / "job.txt").write_text(self.job_text)

    def test_load_job_description_text(self):
        from job_matcher import JobMatcher
        matcher = JobMatcher(output_dir=str(self.output_dir))
        job_data = matcher.load_job_description(str(self.job_dir / "job.txt"))
        self.assertIn('description', job_data)
        self.assertEqual(job_data['description'], self.job_text)

    def test_parse_resumes_and_match(self):
        from job_matcher import JobMatcher
        matcher = JobMatcher(output_dir=str(self.output_dir))
        resumes = matcher.parse_resumes_from_directory(str(self.resume_dir))
        self.assertGreater(len(resumes), 0)

        job_data = matcher.load_job_description(str(self.job_dir / "job.txt"))
        results = matcher.match_resumes_to_job(resumes, job_data)
        self.assertIsInstance(results, dict)
        self.assertIn('ranked_resumes', results)

    def tearDown(self):
        self.temp_dir.cleanup()

if __name__ == "__main__":
    unittest.main()
