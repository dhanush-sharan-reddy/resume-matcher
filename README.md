# Resume Matcher 🎯

An AI-powered resume matching system that uses Natural Language Processing (NLP) and Machine Learning (ML) to automatically match resumes with job descriptions, helping recruiters efficiently shortlist candidates.

## ✨ Features

- ✅ Multi-format resume parsing (PDF, DOCX)
- ✅ Advanced text similarity algorithms (TF-IDF, Cosine Similarity, Jaccard Index)
- ✅ Machine learning classification with KNN
- ✅ Batch processing of multiple resumes
- ✅ Command-line interface for easy usage
- ✅ Docker containerization for portable deployment
- ✅ CI/CD pipeline with GitHub Actions
- ✅ Comprehensive logging and error handling
- ✅ JSON and CSV output for integration and analysis
- ✅ Automated scheduling and automation support

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- pip package manager

### Installation

git clone https://github.com/dhanush-sharan-reddy/resume-matcher.git
cd resume-matcher
pip install -r requirements.txt
python -m space download en_core_web_sm

text

### Basic Usage

python main.py -r data/sample_resumes -j data/job_descriptions/python_developer.txt

text

Results will be saved in the `data/output/` directory.

## 📁 Project Structure

resume-matcher/
├── src/# Core Python modules
├── data/# Input and output data folders
│ ├── sample_resumes/# Your resume files go here
│ ├── job_descriptions/# Job descriptions go here
│ └── output/# Generated results
├── config/ # Configuration files (YAML/JSON)
├── tests/# Unit and integration tests
├── docs/ # Documentation files
├── main.py # Main script to run the matcher
├── requirements.txt # Python dependencies
├── Dockerfile # Docker container config
├── docker-compose.yml # Multi-service deployment configuration
└── README.md # This documentation file

text

## 💡 How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature-name`)
3. Commit your changes (`git commit -m 'Add feature'`)
4. Push to the branch (`git push origin feature-name`)
5. Create a Pull Request

Please follow coding standards and write clear commit messages.

## 📝 License

This project is licensed under the MIT License.

---

Built with ❤️ for recruiters and developers.