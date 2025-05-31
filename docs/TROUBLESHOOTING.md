# 🔧 Troubleshooting Guide

## Common Setup Issues

### 1. API Key Problems

#### ❌ "HEVY_API_KEY environment variable not set"

**Symptoms**:
```
❌ Error: HEVY_API_KEY environment variable not set
Please run: export HEVY_API_KEY='your-api-key-here'
```

**Solutions**:
1. **Check `.env` file exists**:
   ```bash
   ls -la .env
   ```
   If missing, copy from template:
   ```bash
   cp env.example .env
   ```

2. **Verify `.env` file contents**:
   ```bash
   cat .env
   ```
   Should contain:
   ```
   HEVY_API_KEY=your-actual-api-key-here
   ```

3. **Check API key format**:
   - Should be UUID format: `abc123de-f456-7890-abcd-ef1234567890`
   - No quotes or extra spaces
   - Generated from [Hevy Developer Settings](https://hevy.com/settings?developer=)

#### ❌ "401 Unauthorized" or "403 Forbidden"

**Symptoms**:
```
❌ Error fetching workout events: 401 Unauthorized
```

**Solutions**:
1. **Verify Hevy Pro subscription**:
   - API access requires Hevy Pro
   - Check subscription status in Hevy app

2. **Regenerate API key**:
   - Go to [Hevy Developer Settings](https://hevy.com/settings?developer=)
   - Delete old key and generate new one
   - Update `.env` file with new key

3. **Check API key permissions**:
   - Ensure key has workout data access
   - Try logging out/in of Hevy web interface

### 2. Data Issues

#### ❌ "No workout events found"

**Symptoms**:
```
❌ No workout events found
```

**Solutions**:
1. **Check date range**:
   ```bash
   # Try more days
   python hevy_stats.py fetch --days 90
   ```

2. **Verify Hevy data**:
   - Ensure you have logged workouts in Hevy app
   - Check that workouts are complete (not just planned)
   - Verify workouts have exercises with sets/reps

3. **Test with minimal fetch**:
   ```bash
   # Test with just 7 days
   python hevy_stats.py fetch --days 7
   ```

#### ❌ "No relevant exercise data found after filtering"

**Symptoms**:
```
🚫 Excluded 50 sets from 10 exercise types: Warm Up, Treadmill, Walking...
❌ No relevant exercise data found after filtering
```

**Solutions**:
1. **Check excluded exercises**:
   - Tool filters out cardio and warm-ups
   - Ensure you have strength training exercises
   - Add strength exercises to your Hevy workouts

2. **Review workout structure**:
   - Use exercise names that match strength patterns
   - Avoid naming strength exercises like cardio
   - Include proper weight and rep data

### 3. Python Environment Issues

#### ❌ "Module not found" errors

**Symptoms**:
```
ModuleNotFoundError: No module named 'pandas'
ModuleNotFoundError: No module named 'requests'
```

**Solutions**:
1. **Activate virtual environment**:
   ```bash
   # On macOS/Linux
   source venv/bin/activate
   
   # On Windows
   venv\Scripts\activate
   ```

2. **Reinstall dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Check Python version**:
   ```bash
   python --version  # Should be 3.7+
   ```

4. **Create fresh virtual environment**:
   ```bash
   rm -rf venv
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

#### ❌ Permission denied errors

**Symptoms**:
```
PermissionError: [Errno 13] Permission denied
```

**Solutions**:
1. **Check file permissions**:
   ```bash
   chmod 755 hevy_stats.py
   ```

2. **Run without sudo**:
   - Don't use `sudo` with pip in virtual environments
   - Ensure virtual environment is properly activated

### 4. Analysis Issues

#### ❌ "KeyError" or "AttributeError" in analysis

**Symptoms**:
```
KeyError: 'exercise'
AttributeError: 'NoneType' object has no attribute 'mean'
```

**Solutions**:
1. **Check data integrity**:
   ```bash
   # Re-fetch data
   python hevy_stats.py fetch --days 30
   ```

2. **Verify JSON file**:
   ```bash
   # Check file size and format
   ls -lh hevy_events.json
   head -n 20 hevy_events.json
   ```

3. **Clear and re-fetch**:
   ```bash
   rm hevy_events.json
   python hevy_stats.py fetch
   ```

#### ❌ Rep rules not working

**Symptoms**:
```
❓ no target
Exercise needs a target rep range
```

**Solutions**:
1. **Check rep_rules.py exists**:
   ```bash
   ls -la rep_rules.py
   ```
   If missing:
   ```bash
   cp rep_rules.example.py rep_rules.py
   ```

2. **Verify exercise names match**:
   - Check exact spelling in Hevy vs rep_rules.py
   - Exercise names are case-sensitive
   - Add missing exercises to rep_rules.py

3. **Example rep_rules.py entry**:
   ```python
   REP_RANGE = {
       "Bench Press": (6, 10),
       "Leg Press Horizontal (Machine)": (10, 12),
       # Add your exercises here
   }
   ```

## Performance Issues

### Slow API Fetching

**Symptoms**: Long wait times during data fetch

**Solutions**:
1. **Reduce date range**:
   ```bash
   python hevy_stats.py fetch --days 14
   ```

2. **Check internet connection**:
   - Verify stable internet connection
   - Try different network if having issues

3. **Monitor rate limiting**:
   - Tool automatically handles rate limits
   - Large date ranges take longer due to pagination

### Large File Sizes

**Symptoms**: hevy_events.json is very large

**Solutions**:
1. **Tool automatically cleans nulls**:
   - File size is optimized automatically
   - Null values are removed during processing

2. **Reduce data range**:
   ```bash
   # Fetch less historical data
   python hevy_stats.py fetch --days 30
   ```

## Advanced Debugging

### Enable Verbose Logging

Add debug prints to troubleshoot:

```python
# Add to hevy_stats.py temporarily
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Manual API Testing

Test API connection manually:

```bash
curl -H "api-key: your-key-here" \
     "https://api.hevyapp.com/v1/workouts/events?pageSize=1"
```

### Check Data Structure

Inspect your data:

```python
import json
import pandas as pd

# Load and inspect
with open('hevy_events.json', 'r') as f:
    data = json.load(f)

print(f"Events: {len(data)}")
print(f"First event keys: {data[0].keys()}")
```

## Getting Help

### Check GitHub Issues

1. Search existing issues: `[Repository URL]/issues`
2. Create new issue with:
   - Error message (full stack trace)
   - Steps to reproduce
   - System information (OS, Python version)
   - Sample data (anonymized)

### Discord/Community

- Join fitness programming communities
- Share anonymized output for feedback
- Ask for help with rep range setup

### Professional Support

For personalized training advice:
- Consult certified personal trainers
- Consider sports science professionals
- This tool provides data insights, not medical advice

## Diagnostic Commands

Run these to gather system information:

```bash
# System info
python --version
pip --version
pip list | grep -E "(pandas|requests|tabulate)"

# File permissions
ls -la hevy_stats.py rep_rules.py .env

# Environment variables
echo $HEVY_API_KEY | head -c 10  # Shows first 10 chars only

# Test basic functionality
python -c "import pandas, requests, tabulate; print('All modules imported successfully')"
```

## Emergency Reset

If all else fails, start fresh:

```bash
# 1. Backup any custom rep_rules.py
cp rep_rules.py rep_rules_backup.py

# 2. Clean everything
rm -rf venv hevy_events.json hevy_coaching_report_*.md

# 3. Fresh install
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Reconfigure
cp env.example .env
cp rep_rules.example.py rep_rules.py
# Edit .env with your API key
# Edit rep_rules.py with your exercises

# 5. Test
python hevy_stats.py fetch --days 7
``` 