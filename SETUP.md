# 🚀 Setup Guide

## Prerequisites

- Python 3.7 or higher
- A [Hevy](https://hevy.com) account with workout data
- **Hevy Pro subscription** (required for API access)

## Step-by-Step Setup

### 1. Get Your Hevy API Key

1. **Create a Hevy Account** (if you don't have one):
   - Download the Hevy app: [iOS](https://apps.apple.com/app/hevy-workout-tracker/id1512473074) | [Android](https://play.google.com/store/apps/details?id=com.hevy.app)
   - Create your account and log some workouts

2. **Upgrade to Hevy Pro**:
   - API access requires a Hevy Pro subscription
   - Upgrade in the Hevy app or on their website
   - Pro includes additional features beyond API access

3. **Get API Access**:
   - Go to [Hevy Developer Settings](https://hevy.com/settings?developer=)
   - Sign in with your Hevy Pro account
   - Generate a new API key
   - Copy the API key (it looks like: `abc123-def456-ghi789`)

4. **API Documentation**:
   - Official API docs: [https://api.hevyapp.com/docs/](https://api.hevyapp.com/docs/)
   - This tool primarily uses the `/v1/workouts/events` endpoint

### 2. Clone and Install

```bash
# Clone the repository
git clone https://github.com/yourusername/hevy-fitness-coach.git
cd hevy-fitness-coach

# Create a virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Your Settings

#### API Key Setup
```bash
# Copy the environment template
cp env.example .env

# Edit .env file and add your API key
# HEVY_API_KEY=your-actual-api-key-here
```

#### Rep Range Setup
```bash
# Copy the rep rules template
cp rep_rules.example.py rep_rules.py

# Edit rep_rules.py to match your training goals
# Examples:
# - Powerlifting: Lower rep ranges (3-6 reps)
# - Bodybuilding: Moderate rep ranges (8-12 reps)
# - Endurance: Higher rep ranges (15-20 reps)
```

### 4. Test Your Setup

```bash
# Test API connection
python hevy_stats.py fetch --days 7

# If successful, you should see:
# 🚀 Fetching Hevy workout data...
# ✅ Total events fetched: X

# Run full analysis
python hevy_stats.py
```

## Troubleshooting

### Common Issues

**❌ "API key not found"**
- Check that your `.env` file exists and contains `HEVY_API_KEY=your-key`
- Verify your API key is correct (copy-paste from Hevy developer portal)

**❌ "No workout data found"**
- Make sure you have recent workouts in Hevy (last 30 days)
- Try fetching more days: `python hevy_stats.py fetch --days 90`

**❌ "Module not found"**
- Activate your virtual environment: `source venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`

**❌ "Permission denied"**
- Check your API key permissions in Hevy developer portal
- Try regenerating your API key

### Getting Help

1. **Check the logs** - any error messages will guide you to the issue
2. **Verify your Hevy data** - make sure you have workouts with exercises and sets
3. **Test with minimal data** - try `--days 7` first, then increase
4. **Check your internet connection** - API calls need internet access

## Next Steps

Once setup is complete:

1. **Customize your rep ranges** in `rep_rules.py`
2. **Run your first analysis**: `python hevy_stats.py`
3. **Check the generated report** (automatically saved as markdown)
4. **Schedule regular analysis** (daily/weekly) to track progress

Enjoy your data-driven fitness journey! 💪 