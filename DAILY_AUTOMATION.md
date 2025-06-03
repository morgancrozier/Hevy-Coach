# 🏋️‍♂️ Daily Automation Setup Guide

Get your Hevy coaching reports delivered automatically every day!

## 🚀 Quick Start (5 minutes)

### Step 1: Run the Setup Script
```bash
./setup_daily_automation.sh
```

This will:
- Create your `.env` file with placeholders
- Guide you through configuration options
- Help set up automated scheduling

### Step 2: Get Your Credentials

**Hevy API Key:**
1. Go to [hevy.com/developer](https://hevy.com/developer)
2. Sign in with your Hevy account  
3. Generate an API key
4. Copy it to your `.env` file

**Gmail Setup (for email reports):**
1. Enable 2-Factor Authentication on your Google account
2. Go to Google Account Settings > Security > App Passwords
3. Generate an "App Password" for "Mail"
4. Use this app password (not your regular Gmail password)

### Step 3: Test Everything
```bash
python3 hevy_stats.py --test-email  # Test email setup
python3 hevy_stats.py both --email  # Test full workflow
```

## 📧 Automation Options

### Option 1: Daily Email Reports (Recommended)
Perfect for busy people - get reports in your inbox every morning:

```bash
# Add to crontab (run: crontab -e)
0 8 * * * cd /path/to/hevy && python3 hevy_stats.py both --email >> hevy_automation.log 2>&1
```

**What you get:**
- 📧 Email with summary + full report attachment
- 📄 Local markdown file saved
- 📊 CSV export file saved
- 🔄 Fresh data fetched automatically

### Option 2: Local Reports Only
If you prefer local files without email:

```bash
# Add to crontab (run: crontab -e)  
0 8 * * * cd /path/to/hevy && python3 hevy_stats.py both >> hevy_automation.log 2>&1
```

### Option 3: Manual Runs
Run whenever you want a fresh report:

```bash
python3 hevy_stats.py both          # Fetch data + analyze
python3 hevy_stats.py both --email  # + send email
python3 hevy_stats.py analyze       # Just analyze existing data
python3 hevy_stats.py export        # Just export CSV
```

## 🛠️ Configuration

### Environment Variables (.env file)
```bash
HEVY_API_KEY=your-actual-api-key-here
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-gmail-app-password
TO_EMAIL=your-email@gmail.com
```

### Timing Recommendations
- **8 AM**: Great for morning motivation
- **7 PM**: Good for post-workout analysis
- **9 AM**: After you've likely worked out (if you're a morning person)

## 🔧 Troubleshooting

### Check the logs:
```bash
tail -f hevy_automation.log
```

### Common issues:
- **"API key not set"**: Edit `.env` with your real Hevy API key
- **"Email failed"**: Use Gmail App Password, not regular password
- **"No workout data"**: Make sure you've logged workouts in Hevy recently

### Manual testing:
```bash
# Test API connection only
python3 hevy_stats.py fetch --days 7

# Test email only  
python3 hevy_stats.py --test-email

# Full test with output
python3 hevy_stats.py both --email
```

## 📱 Pro Tips

1. **Morning Reports**: Set for 8 AM to review yesterday's workout
2. **Email Filters**: Create Gmail filters to organize your reports
3. **Multiple Schedules**: Run different reports at different times
4. **Backup**: Reports are auto-saved locally even with email
5. **Data Export**: CSV files are perfect for spreadsheet analysis

## 🎯 What You'll Get Daily

**📧 Email Subject:** "🏋️‍♂️ Hevy Coaching Report - 2024-12-03"

**📝 Email Content:**
- Session quality score
- Key insights summary  
- Full detailed report attached

**💾 Local Files:**
- `hevy_coaching_report_YYYYMMDD_HHMMSS.md` - Full analysis
- `hevy_workouts_export_YYYYMMDD_HHMMSS.csv` - Raw data
- `hevy_events.json` - Latest fetched data

---

**🎉 Enjoy your automated fitness coaching!** No more manual report generation - just consistent, data-driven insights delivered to your inbox every day. 