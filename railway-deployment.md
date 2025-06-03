# 🚂 Railway Deployment (Simpler Option)

## 🎯 **Why Railway?**
- ✅ **Dead simple** deployment (git push)
- ✅ **Built-in cron jobs** 
- ✅ **Environment variables** management
- ✅ **PostgreSQL** included
- ✅ **$5-20/month** for most use cases

## 🚀 **Quick Deploy:**

### **1. Restructure as Web App:**
```bash
# Convert your current script into a web service
mkdir hevy-coach-web
cd hevy-coach-web

# Create minimal web interface
touch app.py          # Flask app
touch requirements.txt # Dependencies
touch railway.json    # Railway config
```

### **2. Flask App (`app.py`):**
```python
from flask import Flask, render_template, request, redirect, session
import os
from hevy_stats import HevyStatsClient, print_comprehensive_report
import schedule
import threading
import time

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-key')

# In-memory user storage (use database in production)
users = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['POST'])
def signup():
    email = request.form['email']
    hevy_api_key = request.form['hevy_api_key']
    email_time = request.form['email_time']
    
    # Store user preferences
    users[email] = {
        'hevy_api_key': hevy_api_key,
        'email_time': email_time,
        'active': True
    }
    
    session['user_email'] = email
    return redirect('/dashboard')

@app.route('/dashboard')
def dashboard():
    if 'user_email' not in session:
        return redirect('/')
    
    user = users.get(session['user_email'])
    return render_template('dashboard.html', user=user)

@app.route('/generate-report')
def generate_report():
    if 'user_email' not in session:
        return redirect('/')
    
    user = users.get(session['user_email'])
    
    # Generate report (simplified)
    client = HevyStatsClient(user['hevy_api_key'])
    events = client.get_all_recent_workouts(days=30)
    
    # Convert to analysis (reuse your existing code)
    # ... analysis logic ...
    
    return "Report generated and sent to your email!"

# Background scheduler for daily emails
def send_daily_reports():
    for email, user in users.items():
        if user['active']:
            # Check if it's time for this user
            # Generate and send report
            pass

# Run scheduler in background
def run_scheduler():
    schedule.every().hour.do(send_daily_reports)
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == '__main__':
    # Start background scheduler
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
```

### **3. Railway Config (`railway.json`):**
```json
{
  "name": "hevy-coach",
  "deploy": {
    "startCommand": "python app.py",
    "restartPolicyType": "always"
  },
  "environments": {
    "production": {
      "variables": {
        "FLASK_ENV": "production"
      }
    }
  }
}
```

### **4. Deploy:**
```bash
# 1. Push to GitHub
git init
git add .
git commit -m "Initial commit"
git push origin main

# 2. Connect to Railway
# Visit railway.app
# Connect GitHub repo
# Add environment variables
# Deploy automatically!
```

## 💰 **Cost Comparison:**

| Platform | Cost/Month | Pros | Cons |
|----------|------------|------|------|
| **Railway** | $5-20 | Simple, included DB | Newer platform |
| **Vercel Pro** | $20 + DB costs | Mature, great DX | More complex setup |
| **Render** | $7-25 | Good middle ground | Less features |
| **DigitalOcean App** | $5-12 | Predictable pricing | Basic features |

## 📱 **Minimal HTML Templates:**

### **Landing Page (`templates/index.html`):**
```html
<!DOCTYPE html>
<html>
<head>
    <title>🏋️‍♂️ Hevy Coach</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: system-ui; max-width: 600px; margin: 0 auto; padding: 20px; }
        .hero { text-align: center; padding: 40px 0; }
        .form { background: #f5f5f5; padding: 20px; border-radius: 8px; }
        input, select { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 4px; }
        button { background: #007bff; color: white; padding: 12px 24px; border: none; border-radius: 4px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="hero">
        <h1>🏋️‍♂️ Your AI Fitness Coach</h1>
        <p>Get personalized workout analysis from your Hevy data, delivered daily to your email.</p>
    </div>
    
    <form class="form" action="/signup" method="POST">
        <h3>Start Your Daily Coaching</h3>
        
        <label>Email Address:</label>
        <input type="email" name="email" required placeholder="your@email.com">
        
        <label>Hevy API Key:</label>
        <input type="text" name="hevy_api_key" required placeholder="Get from Hevy app settings">
        
        <label>Daily Email Time:</label>
        <select name="email_time" required>
            <option value="06:00">6:00 AM</option>
            <option value="07:00">7:00 AM</option>
            <option value="08:00" selected>8:00 AM</option>
            <option value="09:00">9:00 AM</option>
            <option value="18:00">6:00 PM</option>
            <option value="19:00">7:00 PM</option>
            <option value="20:00">8:00 PM</option>
        </select>
        
        <button type="submit">🚀 Start Daily Coaching</button>
    </form>
    
    <div style="margin-top: 40px; padding: 20px; background: #e7f3ff; border-radius: 8px;">
        <h4>📧 What you'll get:</h4>
        <ul>
            <li>Daily session quality grades (A+ to D)</li>
            <li>Specific weight recommendations per exercise</li>
            <li>RPE-based coaching insights</li>
            <li>Progressive overload tracking</li>
            <li>Plateau detection and deload suggestions</li>
        </ul>
    </div>
</body>
</html>
``` 