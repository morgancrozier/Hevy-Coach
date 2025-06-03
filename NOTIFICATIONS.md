# 📧 Email Notifications Setup Guide

This guide shows you how to set up automated email notifications for your Hevy coaching reports. Choose the method that works best for you!

## 🎯 Quick Start Options

### Option 1: Manual Email (Simplest)
Run the script with email flag:
```bash
python hevy_stats.py both --email
```

### Option 2: GitHub Actions (Automated Daily)
Set up automated daily emails using GitHub Actions (see below)

### Option 3: Local Automation
Set up cron jobs or scheduled tasks on your computer

---

## 📧 Email Provider Setup

### Gmail Setup (Recommended)
1. **Enable 2-Factor Authentication** on your Google account
2. **Generate App Password**:
   - Go to Google Account settings → Security
   - Under "2-Step Verification", click "App passwords"
   - Select "Mail" and generate password
3. **Set Environment Variables**:
   ```bash
   export EMAIL_USER="your-email@gmail.com"
   export EMAIL_PASSWORD="your-app-password"  # 16-character app password
   export TO_EMAIL="recipient@email.com"      # Can be same as EMAIL_USER
   ```

### Outlook/Hotmail Setup
1. **Enable App Passwords** in Microsoft Account security settings
2. **Set Environment Variables**:
   ```bash
   export EMAIL_USER="your-email@outlook.com"
   export EMAIL_PASSWORD="your-app-password"
   export TO_EMAIL="recipient@email.com"
   export SMTP_SERVER="smtp-mail.outlook.com"
   export SMTP_PORT="587"
   ```

### Other Email Providers
Set these environment variables for your provider:
```bash
export EMAIL_USER="your-email@provider.com"
export EMAIL_PASSWORD="your-password"
export TO_EMAIL="recipient@email.com"
export SMTP_SERVER="smtp.your-provider.com"  # e.g., smtp.yahoo.com
export SMTP_PORT="587"                        # Usually 587 or 465
```

---

## 🤖 GitHub Actions Automation (Daily Emails)

### Step 1: Fork/Clone This Repository
```bash
git clone https://github.com/your-username/hevy-coach.git
cd hevy-coach
```

### Step 2: Set Repository Secrets
Go to your GitHub repo → Settings → Secrets and variables → Actions

Add these secrets:
- `HEVY_API_KEY`: Your Hevy API key
- `EMAIL_USER`: Your email address
- `EMAIL_PASSWORD`: Your email app password
- `TO_EMAIL`: Recipient email (can be same as EMAIL_USER)

**Optional secrets** (for non-Gmail providers):
- `SMTP_SERVER`: Your SMTP server (default: smtp.gmail.com)
- `SMTP_PORT`: Your SMTP port (default: 587)

### Step 3: Create GitHub Actions Workflow
Create `.github/workflows/daily-hevy-report.yml`:

```yaml
name: Daily Hevy Coaching Report

on:
  schedule:
    - cron: '0 12 * * *'  # Daily at 12:00 UTC (adjust for your timezone)
  workflow_dispatch:      # Allow manual trigger

jobs:
  generate-report:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout repository
      uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install requests pandas tabulate python-dotenv
    
    - name: Generate and email report
      env:
        HEVY_API_KEY: ${{ secrets.HEVY_API_KEY }}
        EMAIL_USER: ${{ secrets.EMAIL_USER }}
        EMAIL_PASSWORD: ${{ secrets.EMAIL_PASSWORD }}
        TO_EMAIL: ${{ secrets.TO_EMAIL }}
        SMTP_SERVER: ${{ secrets.SMTP_SERVER || 'smtp.gmail.com' }}
        SMTP_PORT: ${{ secrets.SMTP_PORT || '587' }}
      run: |
        python hevy_stats.py both --email
```

### Step 4: Customize Schedule
Edit the cron schedule in the workflow file:
- `'0 12 * * *'` = Daily at 12:00 UTC
- `'0 19 * * *'` = Daily at 19:00 UTC (7 PM)
- `'0 8 * * 1,3,5'` = Monday, Wednesday, Friday at 8:00 UTC

**Timezone Conversion Examples:**
- Thailand (UTC+7): Use `'0 12 * * *'` for 7 PM Thailand time
- EST (UTC-5): Use `'0 13 * * *'` for 8 AM EST
- PST (UTC-8): Use `'0 16 * * *'` for 8 AM PST

---

## 🖥️ Local Automation

### macOS/Linux (Cron)
1. **Set up environment variables** in your shell profile (`~/.bashrc`, `~/.zshrc`):
   ```bash
   export HEVY_API_KEY="your-api-key"
   export EMAIL_USER="your-email@gmail.com"
   export EMAIL_PASSWORD="your-app-password"
   export TO_EMAIL="recipient@email.com"
   ```

2. **Add cron job**:
   ```bash
   crontab -e
   ```
   Add this line for daily 8 AM reports:
   ```
   0 8 * * * cd /path/to/hevy-coach && python hevy_stats.py both --email
   ```

### Windows (Task Scheduler)
1. **Create batch file** (`hevy_report.bat`):
   ```batch
   @echo off
   set HEVY_API_KEY=your-api-key
   set EMAIL_USER=your-email@gmail.com
   set EMAIL_PASSWORD=your-app-password
   set TO_EMAIL=recipient@email.com
   cd C:\path\to\hevy-coach
   python hevy_stats.py both --email
   ```

2. **Schedule in Task Scheduler**:
   - Open Task Scheduler
   - Create Basic Task
   - Set trigger (daily, weekly, etc.)
   - Set action to run your batch file

---

## 🧪 Testing Your Setup

### Test Email Configuration
```bash
python hevy_stats.py --test-email
```

### Test Manual Report
```bash
python hevy_stats.py both --email
```

### Test GitHub Actions
- Go to your repo → Actions tab
- Click "Daily Hevy Coaching Report"
- Click "Run workflow" to test manually

---

## 🔧 Troubleshooting

### Common Issues

**"Authentication failed"**
- Double-check your app password (not your regular password)
- Ensure 2FA is enabled for Gmail
- Verify EMAIL_USER and EMAIL_PASSWORD are correct

**"Connection refused"**
- Check SMTP_SERVER and SMTP_PORT settings
- Try port 465 with SSL if 587 doesn't work
- Ensure your email provider allows SMTP access

**"GitHub Actions failing"**
- Verify all required secrets are set
- Check the Actions logs for specific error messages
- Ensure your repository has Actions enabled

**"No workout data"**
- Verify HEVY_API_KEY is correct
- Check that you have recent workouts in Hevy app
- Try running without --email first to test data fetching

### Getting Help
1. Check the Actions logs in GitHub for detailed error messages
2. Run locally first to isolate email vs. data issues
3. Use `--test-email` flag to verify email configuration
4. Ensure all environment variables are properly set

---

## 🎯 Pro Tips

1. **Start Simple**: Test manual email first, then automate
2. **Use App Passwords**: Never use your main email password
3. **Check Spam**: First emails might go to spam folder
4. **Timezone Math**: GitHub Actions run in UTC, convert accordingly
5. **Private Repos**: Consider making your repo private if you're concerned about workout data privacy
6. **Backup Method**: Keep the markdown files as backup even with email

---

## 📱 Alternative Notification Methods

### Slack Integration
Replace email with Slack webhook:
```python
import requests

def send_slack_notification(message):
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if webhook_url:
        requests.post(webhook_url, json={"text": message})
```

### Discord Integration
Use Discord webhook for notifications:
```python
def send_discord_notification(message):
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if webhook_url:
        requests.post(webhook_url, json={"content": message})
```

### Telegram Bot
Set up a Telegram bot for notifications:
```python
def send_telegram_message(message):
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if bot_token and chat_id:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": message})
```

Choose the notification method that works best for your workflow! 