"""
Text Similarity Module
Implements various text similarity algorithms for resume-job matching.
"""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
import logging
from typing import List, Dict

# Fallback for NLTK if not available
try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize
    NLTK_AVAILABLE = True
    try:
        stop_words = set(stopwords.words('english'))
    except:
        nltk.download('stopwords', quiet=True)
        stop_words = set(stopwords.words('english'))
except ImportError:
    NLTK_AVAILABLE = False
    stop_words = set(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'])

class TextSimilarityEngine:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.stop_words = stop_words

    def preprocess_text(self, text: str) -> str:
        if not text:
            return ""
        text = text.lower()
        text = re.sub(r'[^a-zA-Z0-9\\s]', ' ', text)
        text = ' '.join(text.split())
        if NLTK_AVAILABLE:
            try:
                tokens = word_tokenize(text)
                tokens = [word for word in tokens if word not in self.stop_words and len(word) > 2]
                return ' '.join(tokens)
            except:
                pass
        words = text.split()
        filtered_words = [word for word in words if word not in self.stop_words and len(word) > 2]
        return ' '.join(filtered_words)

    def calculate_tfidf_similarity(self, resume_text: str, job_description: str) -> float:
        try:
            resume_processed = self.preprocess_text(resume_text)
            job_processed = self.preprocess_text(job_description)
            if not resume_processed or not job_processed:
                return 0.0
            vectorizer = TfidfVectorizer(max_features=1000, ngram_range=(1, 2))
            tfidf_matrix = vectorizer.fit_transform([resume_processed, job_processed])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
            return float(similarity[0][0])
        except Exception as e:
            self.logger.error(f"TF-IDF calculation error: {e}")
            return 0.0

    def calculate_jaccard_similarity(self, resume_text: str, job_description: str) -> float:
        try:
            resume_words = set(self.preprocess_text(resume_text).split())
            job_words = set(self.preprocess_text(job_description).split())
            if not resume_words or not job_words:
                return 0.0
            intersection = resume_words.intersection(job_words)
            union = resume_words.union(job_words)
            return len(intersection) / len(union) if union else 0.0
        except Exception as e:
            self.logger.error(f"Jaccard calculation error: {e}")
            return 0.0

    def calculate_keyword_match_score(self, resume_text: str, job_keywords: List[str]) -> float:
        try:
            if not job_keywords or not resume_text:
                return 0.0
            resume_lower = resume_text.lower()
            matched = sum(1 for keyword in job_keywords if keyword.lower() in resume_lower)
            return matched / len(job_keywords)
        except Exception as e:
            self.logger.error(f"Keyword matching error: {e}")
            return 0.0

    def calculate_composite_score(self, resume_text: str, job_description: str,
                                 job_keywords: List[str] = None, weights: Dict[str, float] = None) -> Dict[str, float]:
        if weights is None:
            weights = {'tfidf': 0.4, 'jaccard': 0.3, 'keyword': 0.3}

        tfidf_score = self.calculate_tfidf_similarity(resume_text, job_description)
        jaccard_score = self.calculate_jaccard_similarity(resume_text, job_description)
        keyword_score = 0.0
        if job_keywords:
            keyword_score = self.calculate_keyword_match_score(resume_text, job_keywords)

        composite_score = (
            weights.get('tfidf', 0.4) * tfidf_score +
            weights.get('jaccard', 0.3) * jaccard_score +
            weights.get('keyword', 0.3) * keyword_score
        )
        return {
            'composite_score': composite_score,
            'tfidf_score': tfidf_score,
            'jaccard_score': jaccard_score,
            'keyword_score': keyword_score
        }

class ResumeRanker:
    def __init__(self):
        self.similarity_engine = TextSimilarityEngine()
        self.logger = logging.getLogger(__name__)

    def rank_resumes(self, resumes: List[Dict], job_description: str,
                     job_keywords: List[str] = None) -> List[Dict]:
        if not resumes:
            return []
        ranked_resumes = []
        for resume in resumes:
            try:
                resume_text = resume.get('raw_text', '')
                if not resume_text:
                    resume_copy = resume.copy()
                    resume_copy.update({'composite_score': 0.0, 'tfidf_score': 0.0, 'jaccard_score': 0.0, 'keyword_score': 0.0})
                    ranked_resumes.append(resume_copy)
                    continue
                scores = self.similarity_engine.calculate_composite_score(resume_text, job_description, job_keywords)
                resume_with_scores = resume.copy()
                resume_with_scores.update(scores)
                ranked_resumes.append(resume_with_scores)
            except Exception as e:
                self.logger.error(f"Error scoring resume: {e}")
                resume_copy = resume.copy()
                resume_copy.update({'composite_score': 0.0, 'scoring_error': str(e)})
                ranked_resumes.append(resume_copy)
        ranked_resumes.sort(key=lambda x: x.get('composite_score', 0), reverse=True)
        return ranked_resumes
