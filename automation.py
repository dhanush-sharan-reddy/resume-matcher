"""
Automation Module for Resume Matcher
Provides scheduling and batch processing capabilities.
"""

import schedule
import time
import logging
import os
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict

# Add src directory to path for imports
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

class ResumeMatchingScheduler:
    def __init__(self, config_file: str = "config/automation_config.json"):
        self.config_file = Path(config_file)
        self.logger = logging.getLogger(__name__)
        self.matcher = None
        self.load_config()
        self.setup_logging()

    def setup_logging(self):
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'automation.log'),
                logging.StreamHandler()
            ]
        )

    def load_config(self):
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
                self.logger.info(f"Configuration loaded from {self.config_file}")
            except Exception as e:
                self.logger.error(f"Error loading config: {e}")
                self.config = self.get_default_config()
        else:
            self.config = self.get_default_config()
            self.save_config()
            self.logger.info(f"Default configuration created at {self.config_file}")

    def get_default_config(self) -> Dict:
        return {
            "watch_directories": {
                "resumes": "data/sample_resumes",
                "jobs": "data/job_descriptions"
            },
            "output_directory": "data/output",
            "schedule": {
                "enabled": True,
                "frequency": "daily",
                "time": "09:00"
            },
            "thresholds": {
                "default": 0.3,
                "high_priority": 0.7
            },
            "processing": {
                "max_retries": 3,
                "retry_delay": 300,
                "backup_results": True
            },
            "email_notifications": {
                "enabled": False,
                "smtp_server": "",
                "smtp_port": 587,
                "username": "",
                "password": "",
                "recipients": []
            }
        }

    def save_config(self):
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            self.logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")

    def initialize_matcher(self):
        if self.matcher is None:
            try:
                from job_matcher import JobMatcher
                output_dir = self.config["output_directory"]
                self.matcher = JobMatcher(output_dir=output_dir)
                self.logger.info("JobMatcher initialized successfully")
            except ImportError as e:
                self.logger.error(f"Error importing JobMatcher: {e}")
                raise
            except Exception as e:
                self.logger.error(f"Error initializing JobMatcher: {e}")
                raise

    def process_new_files(self) -> Dict:
        results = {
            "processed_jobs": 0,
            "total_matches": 0,
            "successful_jobs": 0,
            "failed_jobs": 0,
            "timestamp": datetime.now().isoformat(),
            "job_results": []
        }

        self.initialize_matcher()

        resume_dir = Path(self.config["watch_directories"]["resumes"])
        job_dir = Path(self.config["watch_directories"]["jobs"])

        if not resume_dir.exists():
            self.logger.warning(f"Resume directory does not exist: {resume_dir}")
            return results

        if not job_dir.exists():
            self.logger.warning(f"Job directory does not exist: {job_dir}")
            return results

        resume_files = list(resume_dir.glob("*.pdf")) + list(resume_dir.glob("*.docx")) + list(resume_dir.glob("*.doc"))
        if not resume_files:
            self.logger.warning(f"No resume files found in {resume_dir}")
            return results

        job_files = []
        for ext in ['*.txt', '*.json']:
            job_files.extend(job_dir.glob(ext))
        if not job_files:
            self.logger.warning(f"No job description files found in {job_dir}")
            return results

        self.logger.info(f"Found {len(job_files)} job(s) and {len(resume_files)} resume(s) to process")

        for job_file in job_files:
            job_result = {
                "job_file": str(job_file),
                "job_name": job_file.stem,
                "success": False,
                "qualified_candidates": 0,
                "total_resumes": 0,
                "error": None
            }
            try:
                self.logger.info(f"Processing job: {job_file.name}")

                match_results = self.matcher.run_matching_pipeline(
                    resume_dir=str(resume_dir),
                    job_file=str(job_file),
                    threshold=self.config["thresholds"]["default"],
                    save_results=True
                )

                job_result.update({
                    "success": True,
                    "qualified_candidates": match_results["qualified_resumes"],
                    "total_resumes": match_results["total_resumes"],
                    "valid_resumes": match_results["valid_resumes"],
                    "output_path": match_results.get("output_path")
                })

                results["processed_jobs"] += 1
                results["successful_jobs"] += 1
                results["total_matches"] += match_results["qualified_resumes"]

                self.logger.info(f"✅ Successfully processed {job_file.name}: {match_results['qualified_resumes']} qualified candidates")

            except Exception as e:
                self.logger.error(f"❌ Error processing {job_file.name}: {e}")
                job_result.update({
                    "success": False,
                    "error": str(e)
                })
                results["failed_jobs"] += 1
                results["processed_jobs"] += 1

            results["job_results"].append(job_result)

        return results

    def send_notification(self, results: Dict):
        # Placeholder for email notification
        if not self.config["email_notifications"]["enabled"]:
            self.logger.debug("Email notifications disabled")
            return
        try:
            subject = f"Resume Matching Results - {results['successful_jobs']} jobs processed"
            body = f"Resume Matching Automation Report\n\nTimestamp: {results['timestamp']}\nProcessed Jobs: {results['processed_jobs']}\nSuccessful: {results['successful_jobs']}\nFailed: {results['failed_jobs']}\nTotal Qualified Candidates: {results['total_matches']}\n\nJob Details:\n"
            for job in results['job_results']:
                status = "✅" if job['success'] else "❌"
                body += f"\n{status} {job['job_name']}: {job.get('qualified_candidates', 0)} candidates"
                if job.get('error'):
                    body += f" (Error: {job['error']})"
            self.logger.info(f"Email notification prepared: {subject}")
            # TODO: Implement actual email sending
        except Exception as e:
            self.logger.error(f"Error preparing notification: {e}")

    def scheduled_job(self):
        self.logger.info("🚀 Starting scheduled resume matching job")
        try:
            results = self.process_new_files()
            if results["processed_jobs"] > 0:
                self.logger.info(f"✅ Completed scheduled job: {results['successful_jobs']}/{results['processed_jobs']} jobs successful, {results['total_matches']} total qualified candidates found")
                self.send_notification(results)
                for job_result in results["job_results"]:
                    if job_result["success"]:
                        self.logger.info(f"   📋 {job_result['job_name']}: {job_result['qualified_candidates']} qualified candidates")
                    else:
                        self.logger.error(f"   ❌ {job_result['job_name']}: {job_result['error']}")
            else:
                self.logger.info("ℹ️  No jobs processed in this run")
        except Exception as e:
            self.logger.error(f"❌ Scheduled job failed: {e}")
            import traceback
            self.logger.error(traceback.format_exc())

    def start_scheduler(self):
        if not self.config["schedule"]["enabled"]:
            self.logger.info("⏸️  Scheduling is disabled in configuration")
            return

        frequency = self.config["schedule"]["frequency"]
        time_str = self.config["schedule"]["time"]

        try:
            import schedule
            if frequency == "hourly":
                schedule.every().hour.do(self.scheduled_job)
                self.logger.info("⏰ Scheduler started - running every hour")
            elif frequency == "daily":
                schedule.every().day.at(time_str).do(self.scheduled_job)
                self.logger.info(f"⏰ Scheduler started - running daily at {time_str}")
            elif frequency == "weekly":
                schedule.every().week.do(self.scheduled_job)
                self.logger.info("⏰ Scheduler started - running weekly")
            else:
                self.logger.error(f"❌ Invalid frequency: {frequency}")
                return

            self.logger.info("🔄 Scheduler is now running. Press Ctrl+C to stop.")

            while True:
                schedule.run_pending()
                time.sleep(60)

        except KeyboardInterrupt:
            self.logger.info("🛑 Scheduler stopped by user")
        except Exception as e:
            self.logger.error(f"❌ Scheduler error: {e}")

def main():
    import argparse
    print("🤖 Resume Matcher Automation System")
    print("=" * 50)

    parser = argparse.ArgumentParser(description="Resume Matching Automation")
    parser.add_argument("--config", "-c", help="Configuration file path")
    parser.add_argument("--run-once", action="store_true", help="Run once and exit")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        config_file = args.config or "config/automation_config.json"
        scheduler = ResumeMatchingScheduler(config_file)

        if args.run_once:
            print("🔄 Running one-time processing...")
            scheduler.scheduled_job()
            print("✅ One-time processing completed")
        else:
            print("⏰ Starting continuous scheduler...")
            scheduler.start_scheduler()

    except KeyboardInterrupt:
        print("\n🛑 Stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
