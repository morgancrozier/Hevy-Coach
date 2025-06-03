# 🌐 GitHub Actions Automation Setup

**The BEST way to run your Hevy reports daily** - completely free, reliable, and runs in the cloud!

## 🎯 Why GitHub Actions?

✅ **Free** - GitHub gives you 2,000 minutes/month for free
✅ **Reliable** - Runs in GitHub's cloud infrastructure  
✅ **No server needed** - Your laptop can be off
✅ **Version controlled** - All changes tracked in git
✅ **Easy setup** - Just add secrets and push

## 🚀 Quick Setup (10 minutes)

### Step 1: Push Your Code to GitHub

If you haven't already:
```bash
git init
git add .
git commit -m "Add Hevy automation"
git remote add origin https://github.com/yourusername/hevy-automation.git
git push -u origin main
```

### Step 2: Add GitHub Secrets

1. Go to your repo on GitHub.com
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **"New repository secret"** and add these:

| Secret Name | Value | Notes |
|-------------|--------|-------|
| `HEVY_API_KEY` | `your-actual-api-key` | From hevy.com/developer |
| `EMAIL_USER` | `your-email@gmail.com` | Your Gmail address |
| `EMAIL_PASSWORD` | `your-app-password` | Gmail App Password (not regular password) |
| `TO_EMAIL` | `your-email@gmail.com` | Where to send reports (can be same as EMAIL_USER) |
| `SMTP_SERVER` | `smtp.gmail.com` | Gmail SMTP server |
| `SMTP_PORT` | `587` | Gmail SMTP port |

### Step 3: Enable Actions

1. Go to **Actions** tab in your repo
2. If prompted, click **"I understand my workflows, go ahead and enable them"**
3. Your workflow will be listed as "🏋️‍♂️ Daily Hevy Coaching Report"

### Step 4: Test It!

Click on your workflow → **"Run workflow"** → **"Run workflow"** button

Watch it run and check your email! 🎉

## ⏰ Scheduling

The workflow runs at **8:00 AM UTC** daily. Adjust for your timezone:

| Your Timezone | UTC Time | Cron Setting |
|---------------|----------|-------------|
| **EST (UTC-5)** | 13:00 UTC | `0 13 * * *` |
| **PST (UTC-8)** | 16:00 UTC | `0 16 * * *` |
| **GMT (UTC+0)** | 08:00 UTC | `0 8 * * *` |
| **CET (UTC+1)** | 07:00 UTC | `0 7 * * *` |

Edit `.github/workflows/daily-hevy-report.yml` to change the schedule:
```yaml
schedule:
  - cron: '0 13 * * *'  # 8 AM EST
```

## 📧 What You'll Get

**Every day automatically:**
- 📧 Email with your coaching report
- 📄 Full markdown report attached
- 📊 CSV data export attached
- 🔍 Backup files stored in GitHub for 30 days

## 🛠️ Advanced Configuration

### Multiple Schedules
Want reports at different times? Add multiple cron entries:

```yaml
schedule:
  - cron: '0 13 * * *'  # Morning report (8 AM EST)
  - cron: '0 23 * * *'  # Evening report (6 PM EST)
```

### Workflow on Push
Want a report every time you update the code?

```yaml
on:
  schedule:
    - cron: '0 13 * * *'
  push:
    branches: [ main ]
  workflow_dispatch:
```

### Custom Email Settings
Using a different email provider? Update the secrets:

| Provider | SMTP_SERVER | SMTP_PORT |
|----------|-------------|-----------|
| **Gmail** | `smtp.gmail.com` | `587` |
| **Outlook** | `smtp-mail.outlook.com` | `587` |
| **Yahoo** | `smtp.mail.yahoo.com` | `587` |
| **ProtonMail** | `127.0.0.1` | `1025` (with bridge) |

## 🔧 Troubleshooting

### Check Workflow Logs
1. Go to **Actions** tab
2. Click on the latest run
3. Click on **"generate-report"**
4. Expand any step to see detailed logs

### Common Issues

**❌ "HEVY_API_KEY not set"**
- Add the secret in GitHub repo settings
- Make sure the name is exactly `HEVY_API_KEY`

**❌ "Email failed"**
- Use Gmail App Password, not regular password
- Enable 2-Factor Auth on Google account first
- Check EMAIL_USER and EMAIL_PASSWORD secrets

**❌ "No workout data"**
- Make sure you've logged workouts in Hevy recently
- Check if HEVY_API_KEY is correct

**❌ Workflow not running**
- Check if Actions are enabled in repo settings
- Verify cron syntax with [crontab guru](https://crontab.guru/)

### Manual Testing
Click **"Run workflow"** button to test anytime!

## 💰 Cost & Limits

**GitHub Free Tier:**
- ✅ 2,000 minutes/month (about 67 minutes/day)
- ✅ Your script takes ~1-2 minutes per run
- ✅ Running daily = ~30-60 minutes/month
- ✅ **You'll use less than 5% of your free quota!**

## 📱 Pro Tips

1. **Test First**: Always use "Run workflow" to test before relying on scheduling
2. **Check Email**: Reports go to spam sometimes - add a filter
3. **Backup Access**: Download artifacts from GitHub if email fails
4. **Multiple Repos**: You can fork this for different configurations
5. **Notifications**: GitHub can notify you if workflows fail

## 🔄 Alternative Cloud Options

If you want other cloud options:

### Option 2: Railway (Paid but Simple)
- Deploy with one click
- $5/month for always-on service
- Great for beginners

### Option 3: AWS Lambda (Advanced)
- Free tier: 1M requests/month
- More complex setup
- Great for high-volume usage

### Option 4: Google Cloud Functions (Advanced)  
- Free tier: 2M invocations/month
- Similar to AWS Lambda
- Good Google integration

---

## 🎉 You're All Set!

With GitHub Actions, you'll get reliable daily fitness reports without any server management. Your laptop can be off, you can be traveling, and you'll still get your coaching insights every single day!

**Next Steps:**
1. Set up the secrets
2. Test with "Run workflow"  
3. Enjoy automated fitness coaching! 🏋️‍♂️ 