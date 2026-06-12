import os
import json
import requests
from datetime import datetime
from difflib import SequenceMatcher
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Get environment variables
RESUME_TEXT = os.getenv("RESUME_TEXT", "")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD", "")

def search_ziprecruiter(keyword, location="remote", salary_min=100):
    """Search ZipRecruiter API for jobs"""
    try:
        url = "https://api.ziprecruiter.com/jobs/search"
        params = {
            "search": keyword,
            "location": location,
            "salary_min": salary_min,
            "days_ago": 7,
            "per_page": 20
        }
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            return response.json().get("jobs", [])
    except Exception as e:
        print(f"ZipRecruiter search error: {e}")
    return []

def search_github_jobs(keyword="site reliability engineer"):
    """Search GitHub Jobs API"""
    try:
        url = "https://jobs.github.com/positions.json"
        params = {
            "search": keyword,
            "location": "remote"
        }
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"GitHub Jobs search error: {e}")
    return []

def search_greenhouse(keyword="site reliability engineer"):
    """Search Greenhouse job boards"""
    try:
        # Greenhouse doesn't have a direct API, but we can search their job boards
        url = "https://boards.greenhouse.io/api/v1/boards"
        # This would require specific board IDs, so returning empty for now
        # In practice, you'd target specific companies using Greenhouse
        pass
    except Exception as e:
        print(f"Greenhouse search error: {e}")
    return []

def calculate_match_score(resume_text, job_description):
    """Calculate how well resume matches job description"""
    resume_lower = resume_text.lower()
    job_lower = job_description.lower()
    
    # Extract key skills from job description
    keywords = ["python", "kubernetes", "terraform", "aws", "azure", "jenkins", "prometheus", "grafana", "linux", "docker", "ci/cd", "git", "sre", "devops", "incident response"]
    
    matches = sum(1 for keyword in keywords if keyword in resume_lower and keyword in job_lower)
    score = min(100, (matches / len(keywords)) * 100)
    
    return score

def tailor_resume(resume_text, job_description, job_title, company):
    """Tailor resume for specific job"""
    # Extract key requirements from job description
    key_skills = []
    if "python" in job_description.lower():
        key_skills.append("Python")
    if "kubernetes" in job_description.lower():
        key_skills.append("Kubernetes")
    if "terraform" in job_description.lower():
        key_skills.append("Terraform")
    if "prometheus" in job_description.lower():
        key_skills.append("Prometheus")
    if "grafana" in job_description.lower():
        key_skills.append("Grafana")
    
    # Add a note at the top of the resume
    tailored = f"[Tailored for: {company} - {job_title}]\n\n"
    tailored += f"[Key Skills for this role: {', '.join(key_skills)}]\n\n"
    tailored += resume_text
    
    return tailored

def send_email(subject, body, tailored_resumes):
    """Send email with job matches"""
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = EMAIL_ADDRESS
        msg['Subject'] = subject
        
        html_body = f"""
        
        """
        
        msg.attach(MIMEText(html_body, 'html'))
        
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(EMAIL_ADDRESS, GMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("Email sent successfully")
    except Exception as e:
        print(f"Email error: {e}")

def main():
    print("Starting job search...")
    
    if not RESUME_TEXT or not EMAIL_ADDRESS or not GMAIL_PASSWORD:
        print("ERROR: Missing environment variables. Check GitHub secrets.")
        return
    
    all_jobs = []
    tailored_resumes = []
    
    # Search ZipRecruiter
    print("Searching ZipRecruiter...")
    zip_jobs = search_ziprecruiter("site reliability engineer", salary_min=100000)
    all_jobs.extend(zip_jobs)
    
    # Search GitHub Jobs
    print("Searching GitHub Jobs...")
    github_jobs = search_github_jobs()
    all_jobs.extend(github_jobs)
    
    if not all_jobs:
        print("No jobs found matching criteria.")
        send_email(
            "Job Application Bot: No matches today",
            "No jobs matching your criteria were found today.",
            []
        )
        return
    
    # Process jobs
    for job in all_jobs[:20]:  # Limit to top 20
        job_title = job.get('title', 'Unknown')
        company = job.get('company', 'Unknown')
        job_description = job.get('description', '') or job.get('excerpt', '')
        
        if not job_description:
            continue
        
        # Calculate match score
        score = calculate_match_score(RESUME_TEXT, job_description)
        
        if score >= 60:  # Only include if 60% match or higher
            # Tailor resume
            tailored = tailor_resume(RESUME_TEXT, job_description, job_title, company)
            
            tailored_resumes.append({
                'company': company,
                'job_title': job_title,
                'score': score,
                'url': job.get('url', '')
            })
    
    # Send email summary
    if tailored_resumes:
        body = f""
        for resume_info in tailored_resumes:
            body += f""
        
        send_email(
            f"Job Application Bot: {len(tailored_resumes)} matches found",
            body,
            tailored_resumes
        )
        print(f"Email sent with {len(tailored_resumes)} job matches")
    else:
        send_email(
            "Job Application Bot: No strong matches today",
            "No jobs with 60%+ match were found today.",
            []
        )
        print("No strong matches found")

if __name__ == "__main__":
    main()
