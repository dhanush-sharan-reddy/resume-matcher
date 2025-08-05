
"""
Resume Matcher Web Application
A Flask web application for matching resumes with job descriptions
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import os
import json
import logging
from datetime import datetime
from werkzeug.utils import secure_filename
import sys
from pathlib import Path

# Add src directory to path for imports
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

try:
    from job_matcher import JobMatcher
except ImportError:
    print("Warning: Could not import JobMatcher. Make sure src modules are available.")
    JobMatcher = None

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.doc', '.txt'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'resumes'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'jobs'), exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Home page with upload forms"""
    return render_template('index.html')

@app.route('/upload_job', methods=['POST'])
def upload_job():
    """Handle job description file upload"""
    try:
        if 'job_file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400

        file = request.files['job_file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'jobs', filename)
            file.save(filepath)

            # Read file content
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                return jsonify({'success': True, 'content': content, 'filename': filename})
            except Exception as e:
                return jsonify({'error': f'Could not read file: {str(e)}'}), 400
        else:
            return jsonify({'error': 'Invalid file type. Only PDF, DOCX, DOC, and TXT files are allowed.'}), 400

    except Exception as e:
        logger.error(f"Error uploading job file: {e}")
        return jsonify({'error': 'File upload failed'}), 500

@app.route('/upload_resumes', methods=['POST'])
def upload_resumes():
    """Handle resume file uploads"""
    try:
        if 'resume_files' not in request.files:
            return jsonify({'error': 'No files uploaded'}), 400

        files = request.files.getlist('resume_files')
        if not files or all(f.filename == '' for f in files):
            return jsonify({'error': 'No files selected'}), 400

        uploaded_files = []
        for file in files:
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'resumes', filename)
                file.save(filepath)
                uploaded_files.append({
                    'filename': filename,
                    'size': os.path.getsize(filepath)
                })

        if not uploaded_files:
            return jsonify({'error': 'No valid files uploaded'}), 400

        return jsonify({
            'success': True, 
            'files': uploaded_files,
            'count': len(uploaded_files)
        })

    except Exception as e:
        logger.error(f"Error uploading resume files: {e}")
        return jsonify({'error': 'File upload failed'}), 500

@app.route('/match_resumes', methods=['POST'])
def match_resumes():
    """Process resume matching"""
    try:
        data = request.get_json()
        job_description = data.get('job_description', '').strip()
        threshold = float(data.get('threshold', 0.3))

        if not job_description:
            return jsonify({'error': 'Job description is required'}), 400

        # Check if JobMatcher is available
        if JobMatcher is None:
            # Return mock results for demonstration
            mock_results = get_mock_results()
            return jsonify({
                'success': True,
                'results': mock_results,
                'total_resumes': len(mock_results),
                'qualified_resumes': len([r for r in mock_results if r['composite_score'] >= threshold * 100]),
                'threshold': threshold,
                'timestamp': datetime.now().isoformat()
            })

        # Use actual JobMatcher if available
        resume_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'resumes')

        # Create temporary job file
        job_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'jobs', 'temp_job.txt')
        with open(job_file_path, 'w', encoding='utf-8') as f:
            f.write(job_description)

        # Initialize matcher and run pipeline
        matcher = JobMatcher()
        results = matcher.run_matching_pipeline(
            resume_dir=resume_dir,
            job_file=job_file_path,
            threshold=threshold,
            save_results=False
        )

        # Clean up temp file
        if os.path.exists(job_file_path):
            os.remove(job_file_path)

        # Format results for web display
        formatted_results = []
        for resume in results.get('ranked_resumes', []):
            formatted_results.append({
                'candidateName': Path(resume.get('filename', 'Unknown')).stem.replace('_', ' ').title(),
                'filename': resume.get('filename', 'Unknown'),
                'compositeScore': round(resume.get('composite_score', 0) * 100, 1),
                'tfidfScore': round(resume.get('tfidf_score', 0) * 100, 1),
                'jaccardScore': round(resume.get('jaccard_score', 0) * 100, 1),
                'keywordScore': round(resume.get('keyword_score', 0) * 100, 1),
                'matchExplanation': get_match_explanation(resume.get('composite_score', 0)),
                'email': resume.get('email', 'N/A'),
                'skills': resume.get('skills', [])
            })

        return jsonify({
            'success': True,
            'results': formatted_results,
            'total_resumes': results.get('total_resumes', 0),
            'qualified_resumes': results.get('qualified_resumes', 0),
            'threshold': threshold,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error processing resume matching: {e}")
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500

def get_match_explanation(score):
    """Generate match explanation based on score"""
    if score >= 0.8:
        return "Excellent match with strong alignment to job requirements and relevant experience."
    elif score >= 0.6:
        return "Good match with solid relevant skills and experience. Minor gaps in some areas."
    elif score >= 0.4:
        return "Moderate match with some relevant skills. May require additional training or experience."
    else:
        return "Limited match with job requirements. Significant gaps in required skills and experience."

def get_mock_results():
    """Return mock results for demonstration"""
    return [
        {
            'candidateName': 'John Smith',
            'filename': 'john_smith_resume.pdf',
            'compositeScore': 92,
            'tfidfScore': 89,
            'jaccardScore': 88,
            'keywordScore': 96,
            'matchExplanation': 'Strong match with extensive Python, Django, and AWS experience. 5+ years in web development.',
            'email': 'john.smith@email.com',
            'skills': ['Python', 'Django', 'AWS', 'Machine Learning', 'SQL']
        },
        {
            'candidateName': 'Sarah Johnson',
            'filename': 'sarah_johnson_cv.docx',
            'compositeScore': 87,
            'tfidfScore': 85,
            'jaccardScore': 84,
            'keywordScore': 92,
            'matchExplanation': 'Excellent technical skills with React, Node.js, and cloud platforms. Strong project management background.',
            'email': 's.johnson@email.com',
            'skills': ['React', 'Node.js', 'Python', 'Azure', 'Agile']
        },
        {
            'candidateName': 'Michael Chen',
            'filename': 'michael_chen_resume.pdf',
            'compositeScore': 78,
            'tfidfScore': 76,
            'jaccardScore': 75,
            'keywordScore': 83,
            'matchExplanation': 'Good technical foundation with Java, Spring Boot, and database experience. Growing machine learning skills.',
            'email': 'm.chen@email.com',
            'skills': ['Java', 'Spring Boot', 'SQL', 'Docker', 'Git']
        }
    ]

@app.route('/clear_files', methods=['POST'])
def clear_files():
    """Clear all uploaded files"""
    try:
        # Clear resume files
        resume_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'resumes')
        for filename in os.listdir(resume_dir):
            filepath = os.path.join(resume_dir, filename)
            if os.path.isfile(filepath):
                os.remove(filepath)

        # Clear job files
        job_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'jobs')
        for filename in os.listdir(job_dir):
            filepath = os.path.join(job_dir, filename)
            if os.path.isfile(filepath):
                os.remove(filepath)

        return jsonify({'success': True})

    except Exception as e:
        logger.error(f"Error clearing files: {e}")
        return jsonify({'error': 'Failed to clear files'}), 500

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large. Maximum size is 16MB.'}), 413

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
