from flask import Flask, render_template, request, redirect, url_for, flash
import os
from werkzeug.utils import secure_filename
from src.job_matcher import JobMatcher

app = Flask(__name__)
app.secret_key = 'your-secret-key'

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
            # Format results for template
            formatted_results = []
            for resume in results.get('ranked_resumes', []):
                formatted_results.append({
                    'candidateName': os.path.splitext(resume.get('filename', 'Unknown'))[0].replace('_', ' ').title(),
                    'compositeScore': round(resume.get('composite_score', 0) * 100, 1),
                    'email': resume.get('email', 'N/A'),
                    'skills': ', '.join(resume.get('skills', []))
                })
            return render_template('index.html', results=formatted_results)
        except Exception as e:
            flash(f'Error during matching: {str(e)}')
            return render_template('index.html', results=None)
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

if __name__ == '__main__':
    app.run(debug=True)