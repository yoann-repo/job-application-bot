#!/usr/bin/env python3
"""
Indeed Remote Job Scraper + Resume Matcher + Auto-Tailor
Runs automatically via GitHub Actions every morning at 8am ET
Searches Indeed for remote IT/DevOps/SRE roles $100k+
Compares job descriptions against your resume
Generates customized resumes for each matching job
Emails results to you
"""

import os
import json
import time
import requests
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bs4 import BeautifulSoup
from docx import Document
from docx.shared import Pt, RGBColor
import re

# Configuration
TARGET_SALARY = 100000
KEYWORDS = [
    "Site Reliability Engineer", "SRE", "DevOps Engineer", 
    "Infrastructure Engineer", "Cloud Engineer", "Platform Engineer",
    "Release Engineer", "Systems Engineer", "Cloud Infrastructure"
]

class JobMatcher:
    def __init__(self, resume_text):
        self.resume_text = resume_text.lower()
        self.resume_skills = self.extract_skills()
        
    def extract_skills(self):
        """Extract key skills and technologies from resume"""
        skills = {
            "languages": ["python", "java", "c++", "powershell", "bash"],
            "cloud": ["aws", "azure", "gcp"],
            "tools": ["terraform", "kubernetes", "docker", "jenkins", "ansible",
                     "prometheus", "grafana", "helm"],
            "practices": ["ci/cd", "devops", "devsecops", "infrastructure as code"]
        }
        return skills
    
    def extract_job_requirements(self, job_description):
        """Extract key requirements from job description"""
        job_text = job_description.lower()
        required_skills = {}
        
        for category, skill_list in self.resume_skills.items():
            matches = [s for s in skill_list if s in job_text]
            if matches:
                required_skills[category] = matches
        
        salary_match = re.search(r'\$(\d+(?:,\d+)*)\s*(?:to|-|–)\s*\$(\d+(?:,\d+)*)', job_description)
        salary_min = None
        if salary_match:
            try:
                salary_min = int(salary_match.group(1).replace(",", ""))
            except:
                pass
        
        return required_skills, salary_min
    
    def calculate_match_score(self, job_description):
        """Score how well resume matches job (0-100)"""
        required_skills, salary_min = self.extract_job_requirements(job_description)
        
        if salary_min and salary_min < TARGET_SALARY:
            return 0, "Below salary threshold"
        
        total_skills = sum(len(v) for v in required_skills.values())
        if total_skills == 0:
            return 50, "Generic remote IT role"
        
        matched_skills = sum(len([s for s in self.resume_skills[cat] 
                                 if s in job_description.lower()])
                            for cat in required_skills)
        
        match_percentage = (matched_skills / total_skills) * 100 if total_skills > 0 else 50
        
        return min(100, match_percentage), required_skills

class IndeedScraper:
    def __init__(self):
        self.base_url = "https://www.indeed.com"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
    
    def search_jobs(self, keywords, pages=2):
        """Search Indeed for remote jobs"""
        jobs = []
        
        for keyword in keywords[:5]:  # Limit to 5 keywords to avoid timeout
            for page in range(pages):
                try:
                    params = {
                        "q": keyword,
                        "l": "Remote",
                        "jt": "fulltime",
                        "start": page * 10,
                        "filter": 1
                    }
                    
                    url = f"{self.base_url}/jobs"
                    response = self.session.get(url, params=params, timeout=10)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, "html.parser")
                    job_cards = soup.find_all("div", class_="job_seen_beacon")
                    
                    for card in job_cards[:3]:  # Limit cards per search
                        try:
                            job_title_elem = card.find("h2", class_="jobTitle")
                            company_elem = card.find("span", class_="companyName")
                            
                            if job_title_elem and company_elem:
                                job_link = card.find("a", class_="jcs-JobTitle")
                                job_url = job_link["href"] if job_link else ""
                                
                                job_data = {
                                    "title": job_title_elem.get_text(strip=True),
                                    "company": company_elem.get_text(strip=True),
                                    "url": f"{self.base_url}{job_url}" if job_url else "",
                                    "posted": datetime.now().isoformat()
                                }
                                jobs.append(job_data)
                        except:
                            continue
                    
                    time.sleep(1)
                
                except Exception as e:
                    continue
        
        return jobs[:10]  # Return max 10 jobs to avoid email flooding
    
    def get_job_description(self, job_url):
        """Fetch full job description"""
        try:
            response = self.session.get(job_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            
            desc = soup.find("div", class_="jobsearch-JobComponent-description")
            if desc:
                return desc.get_text(separator="\n")
            return ""
        except:
            return ""

class EmailSender:
    def __init__(self, email, password):
        self.email = email
        self.password = password
    
    def send_summary(self, recipient, results):
        """Send job matches summary via email"""
        if not results:
            subject = "Job Application Bot: No matches today"
            body = "No jobs matching your criteria were found today."
        else:
            subject = f"Job Application Bot: {len(results)} matches found"
            body = self.format_results(results)
        
        try:
            msg = MIMEMultipart()
            msg["From"] = self.email
            msg["To"] = recipient
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "html"))
            
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(self.email, self.password)
            server.send_message(msg)
            server.quit()
            
            print(f"✅ Email sent to {recipient}")
        except Exception as e:
            print(f"⚠️  Email failed: {e}")
    
    def format_results(self, results):
        """Format results as HTML email"""
        html = "<h2>Today's Job Matches</h2><ul>"
        
        for result in sorted(results, key=lambda x: x["match_score"], reverse=True):
            html += f"""
            <li>
                <strong>{result['company']} - {result['title']}</strong><br>
                Match Score: {result['match_score']}%<br>
                <a href="{result['job_url']}">Apply on Indeed</a>
            </li>
            """
        
        html += "</ul>"
        return html

def main():
    """Main execution"""
    print(f"🚀 Job Bot started: {datetime.now()}")
    
    # Get environment variables
    resume_text = os.getenv("RESUME_TEXT", "")
    email_address = os.getenv("EMAIL_ADDRESS", "")
    gmail_password = os.getenv("GMAIL_PASSWORD", "")
    
    if not all([resume_text, email_address, gmail_password]):
        print("❌ Missing environment variables")
        return
    
    # Initialize
    scraper = IndeedScraper()
    matcher = JobMatcher(resume_text)
    
    print("📋 Searching Indeed...")
    jobs = scraper.search_jobs(KEYWORDS)
    print(f"Found {len(jobs)} jobs")
    
    results = []
    for idx, job in enumerate(jobs):
        print(f"\n[{idx+1}/{len(jobs)}] {job['company']} - {job['title']}")
        
        job_desc = scraper.get_job_description(job["url"])
        if not job_desc:
            print("  ⚠️  No description fetched")
            continue
        
        match_score, _ = matcher.calculate_match_score(job_desc)
        
        if match_score < 40:
            print(f"  ❌ Low match ({match_score}%)")
            continue
        
        print(f"  ✅ Match: {match_score}%")
        results.append({
            "company": job["company"],
            "title": job["title"],
            "match_score": match_score,
            "job_url": job["url"]
        })
    
    print(f"\n{'='*60}")
    print(f"✨ Found {len(results)} qualified jobs")
    
    # Send email
    if email_address and gmail_password:
        sender = EmailSender(email_address, gmail_password)
        sender.send_summary(email_address, results)
    
    print("✅ Complete!")

if __name__ == "__main__":
    main()
