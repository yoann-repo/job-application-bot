# Job Application Bot

Automatically searches Indeed for remote IT/DevOps/SRE roles, tailors your resume for each match, and emails you a summary every morning.

## Setup Instructions

### Step 1: Add Files to Your Repo

Upload these three files to your GitHub repo root:
- `job_application_bot.py` - The main script
- `requirements.txt` - Python dependencies
- Create folder `.github/workflows/` and add `schedule.yml` inside it

### Step 2: Create GitHub Secrets

Your bot needs credentials to send emails. Go to your repo Settings → Secrets and variables → Actions, and create these three secrets:

1. **RESUME_TEXT**
   - Value: Copy all the text from your resume (just the plain text, no formatting)
   - This is what the bot uses to match against job descriptions

2. **EMAIL_ADDRESS**
   - Value: `waguiayoann@gmail.com` (your Gmail address)

3. **GMAIL_PASSWORD**
   - Value: Your Gmail app password (NOT your regular password)
   - To get this:
     1. Go to myaccount.google.com
     2. Click "Security" on the left
     3. Turn on "2-Step Verification" if not already on
     4. Search for "App passwords"
     5. Select "Mail" and "Windows Computer"
     6. Copy the 16-character password and paste it here

### Step 3: Enable GitHub Actions

1. Go to your repo
2. Click "Actions" tab
3. Click "I understand my workflows" to enable them
4. Done! The bot will run every morning at 8am Eastern

### How It Works

Every day at 8am ET, GitHub automatically:
1. Runs the `job_application_bot.py` script
2. Searches Indeed for remote IT/DevOps/SRE/Infrastructure roles $100k+
3. Compares each job description against your resume
4. Calculates a match score (0-100%)
5. Emails you a summary with job titles, companies, match scores, and Indeed links
6. You click the links, download your tailored resume if needed, and apply

### Manual Trigger

Don't want to wait? Go to Actions → Daily Job Search → Run workflow to trigger it immediately.

### Costs

Completely free. GitHub gives you 2,000 free Actions minutes per month, and this script uses about 2 minutes per run.

### Tips

- Check your spam folder for emails from the bot
- If you don't get an email, check the "Actions" tab in your repo to see if there were any errors
- Adjust `TARGET_SALARY` in the script if you want a different minimum salary
- Add more keywords to `KEYWORDS` list if you want different job titles searched

---

Created for Yoann Waguia's remote job search. Good luck! 🚀
