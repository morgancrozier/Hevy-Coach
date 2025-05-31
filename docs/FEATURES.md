# 🌟 Features Guide

## Overview

Hevy Fitness Coach transforms your raw workout data into intelligent coaching insights using evidence-based exercise science principles.

## 📊 Analysis Components

### 1. Session Quality Assessment

**What it does**: Grades your most recent workout session from A+ to D based on multiple factors.

**Scoring Factors**:
- **RPE Balance (40%)**: How well you managed intensity (target: RPE 7.5-9.0)
- **Progressive Overload (60%)**: Whether you increased, maintained, or decreased weights appropriately

**Example Output**:
```
🎯 Overall Grade: A (85/100)
📝 Assessment: Great session with solid progression.
💪 Progression: 2 progressed, 0 maintained, 1 regressed
🔥 Intensity Score: 96/100 (RPE balance)
📈 Progress Score: 78/100 (weight progression)
```

**Grades Explained**:
- **A+ (90-100)**: Excellent progression and perfect RPE management
- **A (85-89)**: Great session with solid progression
- **B+ (80-84)**: Good session, minor room for improvement
- **B (75-79)**: Decent session, consider adjusting intensity
- **C+ (70-74)**: Average session, focus on progression
- **C (65-69)**: Below average, review training approach
- **D (<65)**: Poor session, consider deload or technique focus

### 2. Exercise Progression Analysis

**What it does**: Tracks weight, reps, and volume changes over your last 3-4 sessions per exercise.

**Key Insights**:
- **Trend Direction**: 📈 increasing, 📉 decreasing, ➡️ maintained, ⚠️ stagnant
- **Percentage Changes**: Exact progression rates over time
- **Time Context**: Days between sessions for each exercise

**Example Output**:
```
**Leg Press Horizontal (Machine)**
   Sessions: 80.0kg×12.0 (today) → 77.5kg×13.0 (3d ago) → 75.8kg×11.0 (6d ago)
   Trend: 📈 +2.5kg (+3.2%)
   Overall: +6.7% over 4 sessions
```

### 3. Historical Exercise Evolution Analysis

**What it does**: Evaluates past training decisions and identifies missed opportunities for progression.

**Analysis Process**:
1. **Retroactive Coaching**: What should have happened vs what actually happened
2. **Decision Efficiency**: Percentage of optimal weight changes made
3. **Missed Opportunities**: Specific instances where different decisions would have been better
4. **Learning Insights**: Personalized recommendations for better decision-making

**Example Output**:
```
**Face Pull** (Decision Efficiency: 67%)
   Sessions: 12.5kg×15.3 ✅ (today) → 12.5kg×15.0 🟠 (5d ago) → 13.1kg×15.0 ✅ (8d ago)
   ⚠️ Missed Opportunities:
     • 5d ago: should have maintained but decreased instead
   💡 Key Learning: Good overall, but a few missed opportunities for faster progression
```

**Efficiency Scoring**:
- **80%+**: Excellent intuitive coaching
- **65-79%**: Good decision making with room for optimization  
- **<65%**: Significant learning opportunity

### 4. Smart Periodization Insights

**What it does**: Analyzes your overall program status and provides periodization recommendations.

**Assessment Categories**:
- **📈 Progressing Well**: More exercises advancing than plateauing
- **🔄 Mixed Progress**: Balanced progression and plateaus
- **⚠️ Moderate Plateau**: 30-50% of exercises stagnant
- **🚨 Major Plateau**: 50%+ of exercises stagnant

**Recommendations**:
- **Deload Candidates**: Exercises stagnant for 3+ sessions
- **Form Check**: Exercises with declining performance
- **Program Adjustments**: When to change training approach

### 5. Volume & Recovery Analysis

**What it does**: Monitors training volume trends and recovery patterns.

**Metrics Tracked**:
- **Weekly Volume Changes**: Increasing/decreasing/stable
- **Recovery Status**: Days since last workout and frequency patterns
- **Muscle Group Distribution**: Volume allocation across body parts
- **Rest Period Analysis**: Average days between sessions

**Recovery Status Indicators**:
- **🔥 High Frequency**: ≤1 day rest
- **⚡ Good Frequency**: 2 days rest
- **✅ Optimal Recovery**: 3-4 days rest
- **😴 Extended Rest**: 5-7 days rest
- **🚨 Long Break**: 7+ days rest

### 6. RPE-Based Coaching

**What it does**: Uses Rate of Perceived Exertion to fine-tune weight recommendations.

**RPE Guidelines**:
- **<7.5**: Too easy → increase weight ~5%
- **7.5-9.0**: Perfect intensity range → maintain
- **>9.0**: Too hard → decrease weight ~5%

**Smart Logic**:
- Even when reps are "in range", RPE can suggest adjustments
- Prioritizes sustainable progression over maximum weight
- Prevents overreaching and promotes recovery

## 🎯 Rep Range Intelligence

### Target Range System

The tool uses exercise-specific rep ranges based on training goals:

```python
REP_RANGE = {
    "Squat": (6, 8),           # Strength focus
    "Leg Press": (10, 12),     # Hypertrophy focus
    "Face Pull": (15, 20),     # Endurance/health focus
}
```

### Verdict System

- **✅ In Range**: Reps within target, weight appropriate
- **⬇️ Too Heavy**: Reps below target, reduce weight ~10%
- **⬆️ Too Light**: Reps above target, increase weight ~5%
- **❓ No Target**: Exercise needs rep range defined

## 🧠 Advanced Analytics

### Plateau Detection Algorithm

**Stagnation Criteria**:
- Same weight for 3+ consecutive sessions
- No progression over 2+ weeks
- Declining volume despite maintained weight

**Auto-Recommendations**:
- Deload suggestions (reduce weight 10-15%)
- Technique focus periods
- Program variation recommendations

### Decision Quality Scoring

**Efficiency Calculation**:
```
Efficiency = (Good Decisions / Total Decisions) × 100
```

**Good Decision Criteria**:
- Weight increased when RPE was low and reps were high
- Weight maintained when RPE was optimal (7.5-9.0)
- Weight decreased when RPE was high or reps were low

## 📈 Progression Tracking

### Multi-Session Analysis

**Time Windows**:
- **Immediate**: Last 2 sessions (recent changes)
- **Short-term**: Last 3-4 sessions (current trend)
- **Medium-term**: Last 4-6 sessions (overall direction)

**Trend Classification**:
- **Progressive**: Consistent upward trend
- **Regressive**: Consistent downward trend
- **Plateau**: No significant change
- **Volatile**: Inconsistent changes

### Volume Calculations

**Total Volume**: Weight × Reps × Sets
**Session Volume**: Sum of all exercise volumes
**Weekly Volume**: Sum of all session volumes per week

## 🎨 Visualization Elements

### Color-Coded Feedback

- **🟢 Green**: Too light, increase weight
- **🟡 Yellow**: Slightly suboptimal RPE  
- **🟠 Orange**: Moderate concerns
- **🔴 Red**: Too heavy, reduce weight
- **✅ Green Check**: Optimal performance

### Trend Indicators

- **📈**: Positive progression
- **📉**: Negative progression  
- **➡️**: Maintained/stable
- **⚠️**: Stagnant/concerning

## 🔧 Customization Options

### Configurable Parameters

1. **RPE Thresholds**: Adjust increase/decrease triggers
2. **Rep Ranges**: Customize per exercise and training style
3. **Time Windows**: Modify analysis periods
4. **Progression Factors**: Adjust increase/decrease percentages

### Training Style Presets

**Powerlifting Focus**:
- Lower rep ranges (3-6 reps)
- Higher RPE tolerance (8-9.5)
- Smaller progression increments

**Bodybuilding Focus**:
- Moderate rep ranges (8-12 reps)
- Optimal RPE range (7.5-9.0)
- Consistent progression targets

**General Fitness**:
- Higher rep ranges (12-20 reps)
- Conservative RPE targets (6.5-8.5)
- Health-focused recommendations 