"""
Job Matcher Module
Main class that orchestrates resume parsing and job matching.
"""

import os
import json
import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict
from datetime import datetime
import sys

current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from resume_parser import ResumeParser
from text_similarity import ResumeRanker

class JobMatcher:
    def __init__(self, output_dir: str = "output"):
        self.resume_parser = ResumeParser()
        self.ranker = ResumeRanker()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
    
    def load_job_description(self, job_file_path: str) -> Dict:
        job_path = Path(job_file_path)
        if not job_path.exists():
            raise FileNotFoundError(f"Job file not found: {job_file_path}")
        
        try:
            if job_path.suffix.lower() == '.json':
                with open(job_path, 'r', encoding='utf-8') as f:
                    job_data = json.load(f)
                if 'description' not in job_data:
                    raise ValueError("JSON must contain 'description' field")
            else:
                with open(job_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                if not content:
                    raise ValueError("Job description file is empty")
                job_data = {
                    'title': job_path.stem.replace('_', ' ').title(),
                    'description': content,
                    'keywords': []
                }
            
            job_data.setdefault('title', 'Unknown Position')
            job_data.setdefault('keywords', [])
            return job_data
        except Exception as e:
            self.logger.error(f"Error loading job description: {e}")
            raise
    
    def parse_resumes_from_directory(self, resume_dir: str) -> List[Dict]:
        resume_path = Path(resume_dir)
        if not resume_path.exists():
            raise FileNotFoundError(f"Resume directory not found: {resume_dir}")
        
        resumes = []
        extensions = ['.pdf', '.docx', '.doc']
        resume_files = []
        
        for ext in extensions:
            resume_files.extend(resume_path.glob(f'*{ext}'))
            resume_files.extend(resume_path.glob(f'*{ext.upper()}'))
        
        if not resume_files:
            self.logger.warning(f"No resume files found in {resume_dir}")
            return []
        
        self.logger.info(f"Found {len(resume_files)} resume files")
        
        for file_path in resume_files:
            try:
                self.logger.info(f"Parsing: {file_path.name}")
                resume_data = self.resume_parser.parse_resume(str(file_path))
                resumes.append(resume_data)
            except Exception as e:
                self.logger.error(f"Error parsing {file_path.name}: {e}")
                resumes.append({
                    'file_path': str(file_path),
                    'filename': file_path.name,
                    'parsing_success': False,
                    'error': str(e)
                })
        
        successful = sum(1 for r in resumes if r.get('parsing_success', False))
        self.logger.info(f"Successfully parsed {successful}/{len(resumes)} resumes")
        return resumes
    
    def match_resumes_to_job(self, resumes: List[Dict], job_data: Dict, threshold: float = 0.3) -> Dict:
        if not resumes:
            raise ValueError("No resumes provided")
        
        job_description = job_data.get('description', '')
        job_keywords = job_data.get('keywords', [])
        job_title = job_data.get('title', 'Unknown')
        
        if not job_description:
            raise ValueError("Job description is empty")
        
        valid_resumes = [r for r in resumes if r.get('parsing_success', False)]
        failed_resumes = [r for r in resumes if not r.get('parsing_success', False)]
        
        self.logger.info(f"Matching {len(valid_resumes)} valid resumes to: {job_title}")
        
        ranked_resumes = self.ranker.rank_resumes(valid_resumes, job_description, job_keywords) if valid_resumes else []
        qualified_resumes = [r for r in ranked_resumes if r.get('composite_score', 0) >= threshold]
        
        results = {
            'job_info': job_data,
            'total_resumes': len(resumes),
            'valid_resumes': len(valid_resumes),
            'failed_resumes': len(failed_resumes),
            'qualified_resumes': len(qualified_resumes),
            'threshold': threshold,
            'timestamp': datetime.now().isoformat(),
            'ranked_resumes': ranked_resumes,
            'top_candidates': qualified_resumes[:10],
            'failed_parsing': failed_resumes
        }
        
        if ranked_resumes:
            scores = [r.get('composite_score', 0) for r in ranked_resumes if r.get('composite_score', 0) > 0]
            if scores:
                results['statistics'] = {
                    'max_score': max(scores),
                    'min_score': min(scores),
                    'avg_score': sum(scores) / len(scores),
                    'median_score': sorted(scores)[len(scores) // 2]
                }
        
        return results
    
    def save_results(self, results: Dict, output_filename: str = None) -> str:
        if output_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            job_title = results['job_info'].get('title', 'job').replace(' ', '_').lower()
            output_filename = f"results_{job_title}_{timestamp}"
        
        json_path = self.output_dir / f"{output_filename}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str, ensure_ascii=False)
        
        # Create CSV summary
        csv_path = self.output_dir / f"{output_filename}_summary.csv"
        resume_data = []
        for resume in results['ranked_resumes']:
            resume_data.append({
                'filename': resume.get('filename', 'Unknown'),
                'composite_score': round(resume.get('composite_score', 0), 4),
                'tfidf_score': round(resume.get('tfidf_score', 0), 4),
                'jaccard_score': round(resume.get('jaccard_score', 0), 4),
                'keyword_score': round(resume.get('keyword_score', 0), 4),
                'email': resume.get('email', ''),
                'phone': resume.get('phone', ''),
                'skills_count': len(resume.get('skills', [])),
                'word_count': resume.get('word_count', 0)
            })
        
        if resume_data:
            df = pd.DataFrame(resume_data)
            df.to_csv(csv_path, index=False, encoding='utf-8')
        
        self.logger.info(f"Results saved to: {json_path}")
        return str(json_path)
    
    def generate_report(self, results: Dict) -> str:
        job_title = results['job_info'].get('title', 'Unknown')
        total = results['total_resumes']
        valid = results['valid_resumes']
        qualified = results['qualified_resumes']
        threshold = results['threshold']
        
        report = f"""
═══════════════════════════════════════════════════════════════
                    RESUME MATCHING REPORT
═══════════════════════════════════════════════════════════════

Job Title: {job_title}
Analysis Date: {results['timestamp']}
Matching Threshold: {threshold}

SUMMARY
───────────────────────────────────────────────────────────────
📄 Total Resumes: {total}
✅ Successfully Parsed: {valid}
❌ Parse Failures: {results['failed_resumes']}
🎯 Qualified Candidates: {qualified}
📊 Success Rate: {(qualified/valid)*100 if valid > 0 else 0:.1f}%
"""
        
        if 'statistics' in results:
            stats = results['statistics']
            report += f"""
SCORE STATISTICS
───────────────────────────────────────────────────────────────
🏆 Max Score: {stats['max_score']:.3f}
📈 Avg Score: {stats['avg_score']:.3f}
📊 Median Score: {stats['median_score']:.3f}
📉 Min Score: {stats['min_score']:.3f}
"""
        
        if results['top_candidates']:
            report += "\nTOP CANDIDATES\n" + "─" * 63 + "\n"
            for i, candidate in enumerate(results['top_candidates'][:5], 1):
                name = candidate.get('filename', 'Unknown')
                score = candidate.get('composite_score', 0)
                email = candidate.get('email', 'N/A')
                skills = candidate.get('skills', [])
                
                report += f"\n{i}. {name} (Score: {score:.3f})\n"
                report += f"   📧 {email}\n"
                if skills:
                    report += f"   🛠️  Skills: {', '.join(skills[:3])}\n"
        
        report += "\n" + "═" * 63 + "\n"
        return report
    
    def run_matching_pipeline(self, resume_dir: str, job_file: str, threshold: float = 0.3, save_results: bool = True) -> Dict:
        self.logger.info("🚀 Starting resume matching pipeline...")
        
        try:
            job_data = self.load_job_description(job_file)
            resumes = self.parse_resumes_from_directory(resume_dir)
            
            if not resumes:
                raise ValueError("No resume files found")
            
            results = self.match_resumes_to_job(resumes, job_data, threshold)
            
            if save_results:
                output_path = self.save_results(results)
                results['output_path'] = output_path
            
            report = self.generate_report(results)
            results['report'] = report
            
            self.logger.info("✅ Pipeline completed successfully!")
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Pipeline failed: {e}")
            raise
