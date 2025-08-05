from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask import session
import os
import json
import csv
from io import StringIO, BytesIO
from datetime import datetime
from werkzeug.utils import secure_filename
from src.job_matcher import JobMatcher

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this'

# Set up upload folders
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.abspath(os.path.join(BASE_DIR, '..', 'uploads'))
JOB_FOLDER = os.path.join(UPLOAD_FOLDER, 'jobs')
RESUME_FOLDER = os.path.join(UPLOAD_FOLDER, 'resumes')
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.doc', '.txt'}

os.makedirs(JOB_FOLDER, exist_ok=True)
os.makedirs(RESUME_FOLDER, exist_ok=True)

def allowed_file(filename):
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS

# Update your main matching route to store results in session
@app.route('/', methods=['GET', 'POST'])
def index():
    results = None
    if request.method == 'POST' and 'match' in request.form:
        # Find the latest job description file
        job_files = [os.path.join(JOB_FOLDER, f) for f in os.listdir(JOB_FOLDER) if allowed_file(f)]
        if not job_files:
            flash('No job description uploaded.')
            return render_template('index.html', results=None)
        latest_job = max(job_files, key=os.path.getctime)

        matcher = JobMatcher()
        try:
            results = matcher.run_matching_pipeline(
                resume_dir=RESUME_FOLDER,
                job_file=latest_job,
                threshold=0.3,
                save_results=False
            )
            # Format results for template and remove duplicates
            formatted_results = []
            seen_candidates = set()

            for resume in results.get('ranked_resumes', []):
                candidate_name = os.path.splitext(resume.get('filename', 'Unknown'))[0].replace('_', ' ').title()
                email = resume.get('email', 'N/A')
                
                # Create a unique key based on name and email
                candidate_key = (candidate_name, email)
                
                # Only add if we haven't seen this candidate before
                if candidate_key not in seen_candidates:
                    seen_candidates.add(candidate_key)
                    formatted_results.append({
                        'candidateName': candidate_name,
                        'compositeScore': round(resume.get('composite_score', 0) * 100, 1),
                        'email': email,
                        'phone': resume.get('phone', 'N/A'),
                        'skills': ', '.join(resume.get('skills', [])),
                        'wordCount': resume.get('word_count', 0),
                        'skillsCount': len(resume.get('skills', [])),
                        'filename': resume.get('filename', 'Unknown')
                    })
            
            # Store results in session for download
            session['last_results'] = formatted_results
            session['job_title'] = results.get('job_info', {}).get('title', 'Unknown Position')
            
            return render_template('index.html', results=formatted_results)
        except Exception as e:
            flash(f'Error during matching: {str(e)}')
            return render_template('index.html', results=None)
    
    # Check if we have stored results to display
    if 'last_results' in session:
        results = session['last_results']
    
    return render_template('index.html', results=results)

@app.route('/upload_job', methods=['POST'])
def upload_job():
    if 'job_file' not in request.files:
        flash('No job file part')
        return redirect(url_for('index'))
    file = request.files['job_file']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('index'))
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(JOB_FOLDER, filename))
        flash('Job description uploaded successfully!')
    else:
        flash('Invalid file type for job description.')
    return redirect(url_for('index'))

@app.route('/upload_resumes', methods=['POST'])
def upload_resumes():
    if 'resume_files' not in request.files:
        flash('No resume files part')
        return redirect(url_for('index'))
    files = request.files.getlist('resume_files')
    uploaded = 0
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(RESUME_FOLDER, filename))
            uploaded += 1
    if uploaded:
        flash(f'{uploaded} resume(s) uploaded successfully!')
    else:
        flash('No valid resumes uploaded.')
    return redirect(url_for('index'))

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500


@app.route('/download_csv')
def download_csv():
    """Download results as CSV file"""
    if 'last_results' not in session:
        flash('No results available for download. Please run matching first.')
        return redirect(url_for('index'))
    
    try:
        # Create CSV data
        si = StringIO()
        cw = csv.writer(si)
        
        # Write header
        cw.writerow(['Rank', 'Candidate Name', 'Score (%)', 'Email', 'Phone', 'Skills', 'Word Count', 'Skills Count', 'Filename'])
        
        # Write data from session
        for i, result in enumerate(session['last_results'], 1):
            cw.writerow([
                i,
                result['candidateName'],
                result['compositeScore'],
                result['email'],
                result['phone'],
                result['skills'],
                result['wordCount'],
                result['skillsCount'],
                result['filename']
            ])
        
        output = si.getvalue()
        si.close()
        
        # Create BytesIO object for send_file
        bio = BytesIO()
        bio.write(output.encode('utf-8'))
        bio.seek(0)
        
        # Create file response
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        job_title = session.get('job_title', 'resume_matching').replace(' ', '_')
        filename = f"{job_title}_results_{timestamp}.csv"
        
        return send_file(
            bio,
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        flash(f'Error generating CSV: {str(e)}')
        return redirect(url_for('index'))

@app.route('/download_json')
def download_json():
    """Download results as JSON file"""
    if 'last_results' not in session:
        flash('No results available for download. Please run matching first.')
        return redirect(url_for('index'))
    
    try:
        # Format results for JSON
        json_results = {
            'job_title': session.get('job_title', 'Unknown Position'),
            'timestamp': datetime.now().isoformat(),
            'candidates': []
        }
        
        for i, result in enumerate(session['last_results'], 1):
            json_results['candidates'].append({
                'rank': i,
                'candidate_name': result['candidateName'],
                'composite_score': result['compositeScore'],
                'email': result['email'],
                'phone': result['phone'],
                'skills': result['skills'].split(', ') if result['skills'] else [],
                'word_count': result['wordCount'],
                'skills_count': result['skillsCount'],
                'filename': result['filename']
            })
        
        # Create BytesIO object for send_file
        bio = BytesIO()
        bio.write(json.dumps(json_results, indent=2).encode('utf-8'))
        bio.seek(0)
        
        # Create file response
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        job_title = session.get('job_title', 'resume_matching').replace(' ', '_')
        filename = f"{job_title}_results_{timestamp}.json"
        
        return send_file(
            bio,
            mimetype='application/json',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        flash(f'Error generating JSON: {str(e)}')
        return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)