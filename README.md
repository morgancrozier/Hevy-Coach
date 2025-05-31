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