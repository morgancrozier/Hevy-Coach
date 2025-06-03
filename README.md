# 🏋️‍♂️ Hevy Fitness Coach & Analytics

**AI-powered coaching insights from your Hevy workout data** - Get personalized recommendations, progression tracking, and intelligent RPE-based guidance automatically delivered to your inbox daily!

## ✨ What This Does

🎯 **Intelligent Coaching Analysis**
- Session quality scoring with A+ to D grades
- RPE-aware progression recommendations  
- Smart detection of good vs. problematic weight changes
- Historical decision analysis ("what should I have done?")

📊 **Comprehensive Analytics**
- Exercise progression tracking over time
- Peak performance analysis with context
- Volume trends and recovery insights
- Plateau detection and periodization suggestions

🔄 **NEW: Cyclical Routine Tracking** 
- Automatically detects your workout cycle (e.g., Push/Pull/Legs)
- Provides recommendations for your NEXT upcoming workout
- Exercise-specific weight adjustments based on RPE history
- Fetches your actual routine templates from Hevy for detailed guidance
- **Completely Optional**: Only activates if you configure it
- **Fully Configurable**: Support any cycle length (3, 4, 5, 6+ days)

📧 **Automated Daily Reports**
- Full coaching reports emailed to you daily
- Markdown and CSV exports for deeper analysis
- Runs automatically in the cloud (no server needed!)

## 🚀 Quick Start Options

### Option 1: Cloud Automation (Recommended)
**Best for:** Daily automated reports without any server setup

**📖 [GitHub Actions Setup Guide](GITHUB_ACTIONS_SETUP.md)** ← **Start here!**
- ✅ Completely free (GitHub's 2,000 free minutes/month)
- ✅ Runs in the cloud - laptop can be off
- ✅ Reliable daily email delivery
- ✅ 10-minute setup

### Option 2: Local/Manual Use
**Best for:** Occasional analysis or testing

**📖 [Local Automation Guide](DAILY_AUTOMATION.md)**
- Run on your laptop/desktop
- Cron jobs for scheduling
- Full control over environment

## 📋 Prerequisites

1. **Hevy Account** with workout data
2. **Hevy API Key** from [hevy.com/developer](https://hevy.com/developer)
3. **Gmail Account** (for email reports)
4. **GitHub Account** (for cloud automation)

## ⚡ Quick Demo

```bash
# Test it out locally first
python3 hevy_stats.py analyze

# With email (after setting up environment variables)
python3 hevy_stats.py both --email
```

## 🎯 Sample Output

```
🏋️‍♂️  HEVY COMPREHENSIVE COACHING REPORT
================================================================================

⭐ SESSION QUALITY ASSESSMENT
🎯 Overall Grade: A- (87/100)
📝 Assessment: Great session with solid progression.
💪 Progression: 3 progressed, 2 maintained, 1 smart adjustments, 0 regressed

💡 NEXT SESSION RECOMMENDATIONS  
🔧 Weight Adjustments Needed:
• Chest Dip (Assisted): reduce to 32.5kg next time (peak RPE 9.5 too high)

✅ Keep These Weights (they're working!):
• Seated Dip Machine: perfect intensity - maintain this weight!
• Leg Press: perfect intensity - maintain this weight!
```

## 🔧 Features

### 🔄 **NEW: Cyclical Routine Intelligence**
- **Automatic Cycle Detection**: Analyzes your recent workouts to determine where you are in your routine cycle
- **Next Workout Predictions**: Instead of analyzing today's completed workout, predicts what you should do in your next session
- **Routine Template Integration**: Fetches your saved routines from Hevy to provide specific exercise recommendations
- **RPE-Based Weight Adjustments**: Uses your historical RPE data to suggest precise weight changes for each exercise
- **Fully Configurable**: Support any workout split (Push/Pull/Legs, Upper/Lower, Bro Split, Full Body, etc.)
- **Completely Optional**: Only activates when you create a `routine_config.py` file

**How It Works:**
1. **Configure Your Routine**: Copy `routine_config.example.py` to `routine_config.py` and customize
2. **Cycle Pattern Recognition**: Define your workout pattern (any length: 3, 4, 5, 6+ days)
3. **Hevy API Integration**: Fetches your saved routines via the Hevy API (`/v1/routines` endpoint)
4. **Historical Analysis**: Looks at your last performance for each exercise in that specific routine
5. **Smart Recommendations**: Suggests weight increases/decreases based on your last RPE readings

**Setup (Optional):**
```bash
# 1. Copy the example configuration
cp routine_config.example.py routine_config.py

# 2. Edit with your workout cycle
# Examples included for:
# - 6-Day Push/Pull/Legs (default example)
# - 4-Day Upper/Lower Split  
# - 3-Day Full Body
# - 5-Day Bro Split

# 3. Run analysis to get next workout recommendations
python hevy_stats.py analyze
```

**Data Sources:**
- **Your Hevy Routines**: Fetched from your Hevy account via API
- **Workout History**: Your recent training sessions to determine cycle position
- **Exercise Performance**: Historical weight, reps, and RPE data for each exercise

### 🧠 Smart RPE Analysis
- Detects when weight decreases are **smart deloads** vs. actual regressions
- RPE-justified decisions show as "✅ Smart Adjustments" 
- Provides realistic weight recommendations based on equipment increments

### 📈 Progression Intelligence  
- Tracks 3-4 sessions per exercise for context
- Identifies plateaus and suggests interventions
- Historical "what should I have done?" analysis

### 🎯 Practical Recommendations
- Weight suggestions rounded to realistic gym increments (2.5kg, 5kg)
- RPE-based intensity guidance (target 7.5-9.0 for optimal growth)
- Exercise-specific rep range targeting

### 📊 Export & Backup
- Clean CSV exports for spreadsheet analysis
- Markdown reports for easy reading/sharing
- Automatic file timestamps and organization

## 🛠️ Installation & Setup

### Requirements
```bash
pip install requests pandas tabulate python-dotenv
```

### Environment Setup
```bash
# Copy example file
cp setup_example.env .env

# Edit with your credentials
HEVY_API_KEY=your-api-key-here
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-gmail-app-password

# Optional: Configure cyclical routine tracking
cp routine_config.example.py routine_config.py
# Edit routine_config.py with your workout cycle
```

### Usage
```bash
# Fetch and analyze
python3 hevy_stats.py both

# Analyze existing data
python3 hevy_stats.py analyze

# Export to CSV only
python3 hevy_stats.py export --days 30

# Send email report
python3 hevy_stats.py analyze --email

# Test email setup
python3 hevy_stats.py --test-email
```

## 📧 Email Setup (Gmail)

1. Enable 2-Factor Authentication on Google account
2. Generate an "App Password" for Mail
3. Use the app password in `EMAIL_PASSWORD` (not your regular password)

## 🌟 Why This Is Different

Unlike simple workout loggers, this provides **intelligent coaching context**:

- ❌ **Basic tracker**: "You decreased weight"
- ✅ **This tool**: "Smart weight reduction - responded to high RPE 9.5" 

- ❌ **Basic tracker**: "You're below your peak"  
- ✅ **This tool**: "Below unsustainable peak (peak RPE 10.0 was too high - good deload)"

- ❌ **Basic tracker**: Lists numbers
- ✅ **This tool**: "Should have decreased but maintained instead (previous RPE 9.5 was too high)"

## 🔒 Security & Privacy

- ✅ All credentials stored as environment variables
- ✅ No hardcoded secrets in repository
- ✅ Data stays on GitHub/your local machine
- ✅ Safe to fork and share publicly

## 🤝 Contributing

Found a bug or want to add features? Pull requests welcome!

Common improvements:
- Additional exercise classification
- More email providers
- Advanced analytics
- Mobile app integration

## 📄 License

MIT License - feel free to modify and share!

---

**🎉 Start getting smarter about your workouts today!** 

Choose your automation method:
- 🌐 **[GitHub Actions](GITHUB_ACTIONS_SETUP.md)** - Cloud automation (recommended)
- 💻 **[Local Setup](DAILY_AUTOMATION.md)** - Run on your machine

# 🏋️‍♂️ Hevy Fitness Coach

A comprehensive Python tool that transforms your [Hevy](https://hevy.com) workout data into intelligent coaching insights. Get personalized training recommendations, track progressive overload, detect plateaus, and optimize your fitness journey with data-driven analysis.

## ✨ Features

### 🎯 **Intelligent Session Analysis**
- **Session Quality Grading** (A+ to D) based on progression and RPE balance
- **Exercise-by-Exercise Breakdown** with specific weight recommendations
- **RPE-Based Coaching** that considers both rep ranges and perceived exertion

### 📈 **Progressive Overload Tracking**
- **Multi-Session Progression** analysis (last 3-4 sessions per exercise)
- **Plateau Detection** for exercises that haven't progressed
- **Weight Change Percentage** tracking over time

### 🧠 **Smart Periodization**
- **Program Status Assessment** (Progressing Well, Plateau, etc.)
- **Deload Recommendations** for stagnant exercises
- **Volume & Recovery Analysis** with muscle group breakdowns

### 📊 **Comprehensive Reporting**
- **Automatic Markdown Reports** with timestamped insights
- **Volume Trends** and recovery status monitoring
- **Muscle Group Balance** analysis

## 🚀 Quick Start

### 1. **Get Your Hevy API Key**
1. **Create a Hevy Account** (if you don't have one):
   - Download the Hevy app: [iOS](https://apps.apple.com/app/hevy-workout-tracker/id1512473074) | [Android](https://play.google.com/store/apps/details?id=com.hevy.app)
   - Create your account and log some workouts

2. **Upgrade to Hevy Pro** (required for API access):
   - API access requires a Hevy Pro subscription
   - Upgrade in the app or on the website

3. **Get API Access**:
   - Go to [Hevy Developer Settings](https://hevy.com/settings?developer=)
   - Sign in with your Hevy Pro account
   - Generate a new API key
   - Copy the API key (it looks like: `abc123-def456-ghi789`)

4. **API Documentation**:
   - Full API docs: [https://api.hevyapp.com/docs/](https://api.hevyapp.com/docs/)
   - This tool uses the `/v1/workouts/events` endpoint

### 2. **Installation**
```bash
# Clone the repository
git clone https://github.com/yourusername/hevy-fitness-coach.git
cd hevy-fitness-coach

# Install dependencies
pip install -r requirements.txt

# Set up your API key
cp env.example .env
# Edit .env and add your API key: HEVY_API_KEY=your-key-here

# Set up your rep targets
cp rep_rules.example.py rep_rules.py
# Edit rep_rules.py to match your training goals
```

### 3. **Run Analysis**
```bash
# Fetch data and analyze (default mode)
python hevy_stats.py

# Or run specific modes
python hevy_stats.py fetch    # Only fetch data
python hevy_stats.py analyze  # Only analyze existing data
```

## 📱 Sample Output

```
================================================================================
🏋️‍♂️  HEVY COMPREHENSIVE COACHING REPORT
================================================================================

⭐ **SESSION QUALITY ASSESSMENT**
--------------------------------------------------
🎯 **Overall Grade**: A (85/100)
📝 **Assessment**: Great session with solid progression.
💪 **Progression**: 2 progressed, 0 maintained, 1 regressed
🔥 **Intensity Score**: 96/100 (RPE balance)
📈 **Progress Score**: 78/100 (weight progression)

📈 **EXERCISE PROGRESSION ANALYSIS**
--------------------------------------------------
**Leg Press Horizontal (Machine)**
   Sessions: 80.0kg×12.0 (today) → 77.5kg×13.0 (3d ago) → 75.8kg×11.0 (6d ago)
   Trend: 📈 +2.5kg (+3.2%)
   Overall: +6.7% over 4 sessions

🎯 **TRAINING PERIODIZATION INSIGHTS**
--------------------------------------------------
📊 **Program Status**: 📈 Progressing Well
💡 **Recommendation**: Keep current program, great momentum!
📈 **Plateau Rate**: 0% of exercises
```

## ⚙️ Configuration

### **Rep Range Customization**
Edit `rep_rules.py` to set your target rep ranges:

```python
REP_RANGE = {
    "Squat": (6, 8),           # Compound movements: lower reps
    "Leg Press": (10, 12),     # Machine exercises: moderate reps  
    "Face Pull": (15, 20),     # Accessories: higher reps
}
```

### **RPE Guidelines**
The system uses these RPE thresholds (configurable in `hevy_stats.py`):
- **RPE < 7.5**: Suggest weight increase (too easy)
- **RPE 7.5-9.0**: Perfect intensity range
- **RPE > 9.0**: Suggest weight decrease (too hard)

## 🎯 Command Line Options

```bash
python hevy_stats.py [mode] [options]

Modes:
  fetch      Fetch new data from Hevy API
  analyze    Analyze existing data
  both       Fetch and analyze (default)

Options:
  --days N              Fetch last N days (default: 30)
  --infile FILE         Input JSON file (default: hevy_events.json)
  --outfile FILE        Output JSON file (default: hevy_events.json)
  --save-csv            Save raw data to CSV
  --save-markdown       Save report as Markdown (auto-enabled)
```

## 📁 Project Structure

```
hevy-fitness-coach/
├── hevy_stats.py           # Main application
├── rep_rules.py            # Your rep range targets
├── requirements.txt        # Python dependencies
├── .env                    # Your API key (create from env.example)
├── env.example            # Template for API key setup
├── rep_rules.example.py   # Template for rep ranges
├── README.md              # This file
├── SETUP.md               # Detailed setup guide
├── LICENSE                # MIT license
└── docs/                  # Documentation
    ├── API-REFERENCE.md   # Hevy API integration details
    ├── FEATURES.md        # Comprehensive features guide
    └── TROUBLESHOOTING.md # Common issues and solutions
```

## 📚 Documentation

- **[📋 Setup Guide](SETUP.md)** - Step-by-step installation and configuration
- **[🌟 Features Guide](docs/FEATURES.md)** - Comprehensive analysis capabilities overview
- **[📡 API Reference](docs/API-REFERENCE.md)** - Hevy API integration and data flow
- **[🔧 Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions

## 🔗 Official Links

- **[Hevy App](https://hevy.com)** - The workout tracking app
- **[Hevy API Documentation](https://api.hevyapp.com/docs/)** - Official API docs
- **[Hevy Developer Settings](https://hevy.com/settings?developer=)** - Get your API key (Pro required)

## 🤝 Contributing

Contributions are welcome! Here are some ways you can help:

- **Add More Exercise Categories** for better muscle group classification
- **Improve RPE Analysis** with more sophisticated algorithms  
- **Add Export Formats** (CSV, JSON, PDF reports)
- **Create Visualization** with charts and graphs
- **Add More Periodization Models** (linear, undulating, etc.)

### Development Setup
```bash
# Fork the repo and clone your fork
git clone https://github.com/yourusername/hevy-fitness-coach.git

# Create a feature branch
git checkout -b feature/your-feature-name

# Make your changes and test
python hevy_stats.py analyze

# Submit a pull request
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This tool provides fitness insights based on your workout data. Always consult with qualified fitness professionals for personalized training advice. The authors are not responsible for any injuries or health issues that may result from following the recommendations.

## 🙏 Acknowledgments

- **[Hevy](https://hevy.com)** for providing an excellent workout tracking app and API
- **Exercise Science Community** for RPE and periodization research
- **Open Source Contributors** who help improve this tool

---

**Made with ❤️ for the fitness community**

*Like this project? Give it a ⭐ and share it with fellow lifters!* 

# 🏋️‍♂️ Hevy Coach Pro

An intelligent personal training coach that analyzes your Hevy workout data and provides comprehensive coaching insights with RPE-based recommendations, session quality grading, and automated email reports.

## ✨ Features

- **🎯 Session Quality Grading**: A+ to D grades based on progression and RPE balance
- **📈 Exercise Progression Analysis**: Track weight progression across multiple sessions
- **🔍 Historical Decision Analysis**: Learn from past sessions and identify missed opportunities
- **💪 RPE-Based Coaching**: Intelligent recommendations using Rate of Perceived Exertion
- **📊 Comprehensive Trends**: Volume analysis, strength progression rates, and fitness trajectories
- **🏆 Peak Performance Tracking**: Monitor distance from personal bests
- **📧 Automated Email Reports**: Daily coaching reports delivered to your inbox
- **📝 Markdown Export**: Beautiful, shareable reports

## 🚀 Quick Start

### 1. Get Your Hevy API Key
1. Open the Hevy app
2. Go to Settings → Developer → API Key
3. Copy your API key

### 2. Set Up Environment
```bash
# Required
export HEVY_API_KEY="your-hevy-api-key-here"

# Optional (for email notifications)
export EMAIL_USER="your-email@gmail.com"
export EMAIL_PASSWORD="your-app-password"
export TO_EMAIL="recipient@email.com"
```

### 3. Install Dependencies
```bash
pip install requests pandas tabulate python-dotenv
```

### 4. Run Analysis
```bash
# Basic analysis
python hevy_stats.py

# With email notification
python hevy_stats.py both --email

# Test email setup
python hevy_stats.py --test-email
```

## 📧 Email Notifications

Set up automated daily coaching reports delivered to your email!

### Quick Email Setup (Gmail)
1. **Enable 2-Factor Authentication** on your Google account
2. **Generate App Password**: Google Account → Security → App passwords
3. **Set environment variables**:
   ```bash
   export EMAIL_USER="your-email@gmail.com"
   export EMAIL_PASSWORD="your-16-char-app-password"
   export TO_EMAIL="recipient@email.com"
   ```
4. **Test**: `python hevy_stats.py --test-email`
5. **Send report**: `python hevy_stats.py both --email`

### Automated Daily Reports (GitHub Actions)
1. **Fork this repository**
2. **Add repository secrets**:
   - `HEVY_API_KEY`: Your Hevy API key
   - `EMAIL_USER`: Your email address
   - `EMAIL_PASSWORD`: Your email app password
   - `TO_EMAIL`: Recipient email
3. **The workflow runs daily at 12:00 UTC** (customize in `.github/workflows/daily-hevy-report.yml`)

📖 **Full Setup Guide**: See [NOTIFICATIONS.md](NOTIFICATIONS.md) for detailed instructions including Outlook, local automation, and alternative notification methods.

## 📊 What You Get

### Session Quality Assessment
- **Overall Grade**: A+ to D based on progression and intensity
- **RPE Balance Score**: How well you managed training intensity
- **Progress Score**: Weight progression across exercises

### Exercise Analysis
- **Progression Tracking**: Weight changes over last 3-4 sessions
- **RPE-Based Recommendations**: Increase/decrease/maintain based on effort
- **Historical Decision Analysis**: Learn from past training decisions
- **Missed Opportunities**: Identify when you should have adjusted weights

### Comprehensive Trends
- **Fitness Trajectory**: Overall progress direction and rate
- **Volume Analysis**: Weekly training volume trends
- **Strength Progression**: kg/week progression rates per exercise
- **Peak Performance**: Distance from personal bests

### Smart Recommendations
- **Next Session Weights**: Specific weight adjustments per exercise
- **Training Focus**: Based on plateau detection and progression patterns
- **Recovery Insights**: Volume and frequency analysis

## 🎯 Example Output

```
⭐ SESSION QUALITY ASSESSMENT
🎯 Overall Grade: A- (87/100)
📝 Assessment: Great session with solid progression
💪 Progression: 3 progressed, 2 maintained, 0 regressed

📈 EXERCISE PROGRESSION ANALYSIS
Bench Press: 80kg×8 → 82.5kg×7 → 85kg×6 (📈 +6.3%)
Squat: 100kg×10 → 100kg×9 → 102.5kg×8 (📈 +2.5%)

💡 NEXT SESSION RECOMMENDATIONS
🔧 Weight Adjustments Needed:
• Bench Press: increase to ~87.5kg next time (RPE 7.2 too low)
• Squat: maintain 102.5kg (perfect intensity)
```

## 🔧 Advanced Usage

### Command Line Options
```bash
# Fetch only (no analysis)
python hevy_stats.py fetch --days 60

# Analyze existing data
python hevy_stats.py analyze --infile my_data.json

# Save to CSV
python hevy_stats.py both --save-csv

# Email with custom file
python hevy_stats.py analyze --infile old_data.json --email
```

### Customization
- **Rep Targets**: Edit `rep_rules.py` to set target rep ranges per exercise
- **RPE Guidelines**: Modify `RPE_GUIDELINES` in the script
- **Excluded Exercises**: Update `EXCLUDED_EXERCISES` list for cardio/warm-ups

## 🛠️ Setup for Other Users

This tool is designed to be easily shared! Here's how others can use it:

### For Individual Use
1. **Clone/download** this repository
2. **Set up your API key** and email credentials
3. **Run locally** or set up GitHub Actions automation

### For Sharing
1. **Fork the repository** to your GitHub account
2. **Share the fork** with others
3. **Each user sets their own secrets** in their fork
4. **Everyone gets personalized reports** without sharing data

### Privacy Considerations
- **Workout data stays private** - each user's data only goes to their email
- **API keys are personal** - each user needs their own Hevy API key
- **Email credentials are separate** - no shared email accounts needed

## 📱 Alternative Notifications

Beyond email, you can set up:
- **Slack notifications** via webhooks
- **Discord messages** for community sharing
- **Telegram bots** for mobile notifications
- **Local notifications** on your computer

See [NOTIFICATIONS.md](NOTIFICATIONS.md) for setup instructions.

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Additional exercise analysis algorithms
- New notification methods
- UI improvements
- Performance optimizations

## 📄 License

MIT License - feel free to use, modify, and share!

---

**💡 Pro Tip**: Start with manual reports to understand the analysis, then set up automation for daily insights. The tool learns your patterns and gets more accurate over time! 