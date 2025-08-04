"""
Resume Matcher Package
A collection of modules for parsing resumes and matching them with job descriptions.
"""

__version__ = "1.0.0"
__author__ = "Resume Matcher Team"

from .resume_parser import ResumeParser
from .text_similarity import TextSimilarityEngine, ResumeRanker
from .job_matcher import JobMatcher

__all__ = ["ResumeParser", "TextSimilarityEngine", "ResumeRanker", "JobMatcher"]
