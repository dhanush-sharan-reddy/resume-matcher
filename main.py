#!/usr/bin/env python3
"""
Resume Matcher - Main Execution Script
A comprehensive tool for matching resumes to job descriptions using NLP and ML.
"""

import argparse
import sys
import os
from pathlib import Path

# Add src directory to path for imports
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

def main():
    print("🎯 Resume Matcher - Automated Resume-Job Matching System")
    print("=" * 60)
    
    parser = argparse.ArgumentParser(description="Match resumes to job descriptions using NLP and ML")
    parser.add_argument("--resume-dir", "-r", type=str, required=True, help="Directory containing resume files (PDF/DOCX)")
    parser.add_argument("--job-file", "-j", type=str, required=True, help="Job description file (TXT/JSON)")
    parser.add_argument("--threshold", "-t", type=float, default=0.3, help="Minimum similarity threshold for qualification (0.0-1.0, default: 0.3)")
    parser.add_argument("--output-dir", "-o", type=str, default="data/output", help="Output directory for results")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Validate arguments
    if not (0.0 <= args.threshold <= 1.0):
        print("❌ Error: Threshold must be between 0.0 and 1.0")
        sys.exit(1)
    
    if not Path(args.resume_dir).exists():
        print(f"❌ Error: Resume directory not found: {args.resume_dir}")
        sys.exit(1)
    
    if not Path(args.job_file).exists():
        print(f"❌ Error: Job description file not found: {args.job_file}")
        sys.exit(1)
    
    try:
        from job_matcher import JobMatcher
        
        print(f"📂 Resume Directory: {args.resume_dir}")
        print(f"📋 Job Description: {args.job_file}")
        print(f"🎯 Threshold: {args.threshold}")
        print(f"📁 Output Directory: {args.output_dir}")
        print("-" * 60)
        
        matcher = JobMatcher(output_dir=args.output_dir)
        
        if args.verbose:
            import logging
            logging.getLogger().setLevel(logging.DEBUG)
        
        results = matcher.run_matching_pipeline(
            resume_dir=args.resume_dir,
            job_file=args.job_file,
            threshold=args.threshold,
            save_results=True
        )
        
        print(results.get('report', 'No report generated'))
        
        print(f"\n🎉 SUCCESS! Processed {results['total_resumes']} resumes")
        print(f"✅ Valid resumes: {results['valid_resumes']}")
        print(f"🎯 Qualified candidates: {results['qualified_resumes']}")
        
        if results.get('failed_resumes', 0) > 0:
            print(f"⚠️  Failed to parse: {results['failed_resumes']} resumes")
        
        if 'output_path' in results:
            print(f"💾 Results saved to: {results['output_path']}")
        
        return 0
    
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("💡 Make sure all required packages are installed:")
        print("   pip install -r requirements.txt")
        print("   python -m spacy download en_core_web_sm")
        sys.exit(1)
    
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
