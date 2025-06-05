#!/usr/bin/env python3
"""
Hevy Stats Fetcher & Coach-Style Analysis
A comprehensive script to fetch and analyze your Hevy workout statistics with intelligent coaching feedback.
"""

import requests
import json
import pandas as pd
import argparse
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from tabulate import tabulate
from rep_rules import REP_RANGE
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not installed, skip
    pass

# OpenAI integration for AI-powered insights
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
    
    # Set up OpenAI client
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key:
        openai_client = OpenAI(api_key=openai_api_key)
    else:
        OPENAI_AVAILABLE = False
        openai_client = None
except ImportError:
    OPENAI_AVAILABLE = False
    openai_api_key = None
    openai_client = None

# RPE-based coaching guidelines
RPE_GUIDELINES = {
    "increase_threshold": 7.5,     # If RPE below this, suggest weight increase
    "decrease_threshold": 9.0,     # If RPE above this, suggest weight decrease
    "increase_factor": 1.05,       # 5% weight increase
    "decrease_factor": 0.95,       # 5% weight decrease
}

def is_assisted_exercise(exercise_name: str) -> bool:
    """
    Check if an exercise is an assisted exercise where higher weight = easier.
    
    Args:
        exercise_name: Name of the exercise
        
    Returns:
        True if this is an assisted exercise
    """
    assisted_keywords = [
        "assisted", "assist", "band assisted", "machine assisted",
        "counterweight", "counter weight", "help", "support"
    ]
    
    exercise_lower = exercise_name.lower()
    return any(keyword in exercise_lower for keyword in assisted_keywords)

class AICoach:
    """AI-powered coaching insights using GPT-4o-mini."""
    
    def __init__(self):
        self.available = OPENAI_AVAILABLE and openai_api_key and openai_client is not None
        self.model = "gpt-4o-mini"  # Cost-effective model for coaching insights
        
    def is_available(self) -> bool:
        """Check if AI coaching is available."""
        return self.available
    
    def generate_session_summary(self, session_quality: Dict, last_session: Dict, 
                                comprehensive_trends: Dict, user_context: Dict = None) -> str:
        """
        Generate an AI-powered, personalized session summary.
        
        Args:
            session_quality: Session quality metrics
            last_session: Last session data
            comprehensive_trends: Overall progress trends
            user_context: Optional user profile/preferences
            
        Returns:
            Personalized coaching summary string
        """
        if not self.available:
            return None
            
        try:
            # Prepare structured data for AI analysis
            session_data = {
                "grade": session_quality.get("grade", "Unknown"),
                "overall_score": session_quality.get("overall_score", 0),
                "description": session_quality.get("description", ""),
                "progressed": session_quality.get("progressed", 0),
                "smart_adjustments": session_quality.get("smart_adjustments", 0),
                "regressed": session_quality.get("regressed", 0)
            }
            
            # Count adjustments needed
            adjustments_needed = 0
            priority_exercises = []
            if last_session and last_session.get("exercises"):
                for ex in last_session["exercises"]:
                    if ex["verdict"] in ["⬇️ too heavy", "⬆️ too light"]:
                        adjustments_needed += 1
                        peak_rpe = ex.get("peak_rpe", 8.0)
                        if peak_rpe:
                            priority = abs(peak_rpe - 8.5)  # Distance from ideal RPE
                            priority_exercises.append((priority, ex["name"], ex["verdict"]))
                
                priority_exercises.sort(reverse=True)  # Highest priority first
            
            # Overall progress context
            progress_data = {
                "trajectory": comprehensive_trends.get("fitness_trajectory", "Unknown"),
                "avg_rate": comprehensive_trends.get("avg_progression_rate", 0),
                "frequency": comprehensive_trends.get("training_frequency", 0)
            }
            
            # Create coaching prompt
            prompt = f"""You are an expert strength coach providing personalized feedback. Analyze this workout session and provide encouraging, actionable insights.

SESSION METRICS:
- Grade: {session_data['grade']} ({session_data['overall_score']:.0f}/100)
- Progress: {session_data['progressed']} exercises progressed, {session_data['smart_adjustments']} smart adjustments, {session_data['regressed']} regressed
- Adjustments needed: {adjustments_needed} exercises need weight changes

OVERALL PROGRESS:
- Trajectory: {progress_data['trajectory']}
- Average progression: {progress_data['avg_rate']:+.1f}kg/week
- Training frequency: {progress_data['frequency']:.1f} sessions/week

TOP PRIORITY EXERCISE:
{priority_exercises[0][1] if priority_exercises else "None"}: {priority_exercises[0][2] if priority_exercises else "All exercises optimal"}

COACHING STYLE:
- Be encouraging but honest
- Use 2-3 sentences maximum
- Focus on the most important takeaway
- Use motivational language but stay technical
- Include specific next steps
- Use fitness emojis sparingly (1-2 max)

Provide a personalized summary that feels like it's from an experienced coach who knows the athlete."""

            # Call OpenAI API
            response = openai_client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "system",
                    "content": "You are an expert strength coach with 10+ years of experience. You provide personalized, encouraging feedback that motivates athletes while keeping them focused on proper progression."
                }, {
                    "role": "user", 
                    "content": prompt
                }],
                max_tokens=120,  # Keep it concise
                temperature=0.7,  # Some creativity but stay factual
                top_p=0.9
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"⚠️ AI coaching unavailable: {e}")
            return None
    
    def generate_next_session_focus(self, last_session: Dict, progression_data: Dict) -> str:
        """Generate AI-powered focus points for the next session."""
        if not self.available or not last_session:
            return None
            
        try:
            # Analyze exercise-specific challenges
            challenging_exercises = []
            form_focus_exercises = []
            confidence_builders = []
            
            for ex in last_session.get("exercises", []):
                peak_rpe = ex.get("peak_rpe")
                verdict = ex.get("verdict", "")
                
                if peak_rpe and peak_rpe >= 9.5:
                    challenging_exercises.append(ex["name"])
                elif peak_rpe and peak_rpe <= 7.0:
                    confidence_builders.append(ex["name"])
                elif verdict == "⬇️ too heavy":
                    form_focus_exercises.append(ex["name"])
            
            prompt = f"""As a strength coach, provide 1-2 specific focus points for the next training session.

CURRENT SESSION ANALYSIS:
- Challenging exercises (RPE 9.5+): {', '.join(challenging_exercises[:2]) if challenging_exercises else 'None'}
- Form focus needed: {', '.join(form_focus_exercises[:2]) if form_focus_exercises else 'None'}  
- Confidence builders (RPE ≤7): {', '.join(confidence_builders[:2]) if confidence_builders else 'None'}

Give practical, specific advice for the next session. Keep it to 1-2 actionable focus points maximum."""

            response = openai_client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "system",
                    "content": "You are a practical strength coach. Give specific, actionable advice."
                }, {
                    "role": "user",
                    "content": prompt
                }],
                max_tokens=80,
                temperature=0.6
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"⚠️ AI focus generation unavailable: {e}")
            return None

    def generate_exercise_insights(self, exercise_data: List[Dict], progression_data: Dict) -> Dict:
        """Generate AI insights for specific exercises that need attention."""
        if not self.available or not exercise_data:
            return {}
            
        try:
            # Focus on exercises that need adjustments or have interesting patterns
            priority_exercises = []
            
            for ex in exercise_data[:8]:  # Top 8 exercises
                exercise_name = ex["name"]
                verdict = ex.get("verdict", "")
                peak_rpe = ex.get("peak_rpe")
                
                # Add exercises that need attention
                if verdict in ["⬇️ too heavy", "⬆️ too light"]:
                    priority_exercises.append({
                        "name": exercise_name,
                        "verdict": verdict,
                        "rpe": peak_rpe,
                        "weight": ex.get("avg_weight", 0),
                        "reps": ex.get("avg_reps", 0)
                    })
            
            if not priority_exercises:
                return {}
            
            # Create prompt for exercise-specific insights
            exercise_lines = []
            for ex in priority_exercises[:3]:
                rpe_str = f"{ex['rpe']:.1f}" if ex['rpe'] is not None else "N/A"
                exercise_lines.append(f"- {ex['name']}: {ex['verdict']}, RPE {rpe_str}, {ex['weight']:.1f}kg×{ex['reps']:.1f}")
            exercise_list = "\n".join(exercise_lines)
            
            prompt = f"""As a strength coach, provide brief, specific insights for these exercises that need attention:

{exercise_list}

For each exercise, give ONE practical tip focusing on:
- Why this happened (RPE context, technique, programming)
- What to do next session
- Keep each tip to 1 sentence maximum

Format: "Exercise: insight"
Example: "Bench Press: RPE 9.5+ indicates weight too high - focus on controlled reps with 5kg less next session"
"""

            response = openai_client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "system",
                    "content": "You are a technical strength coach. Provide specific, actionable exercise advice."
                }, {
                    "role": "user",
                    "content": prompt
                }],
                max_tokens=150,
                temperature=0.5
            )
            
            # Parse the response into a dictionary
            insights = {}
            response_text = response.choices[0].message.content.strip()
            
            for line in response_text.split('\n'):
                if ':' in line and any(ex['name'] in line for ex in priority_exercises):
                    # Try to match exercise name
                    for ex in priority_exercises:
                        if ex['name'] in line:
                            insight = line.split(':', 1)[1].strip()
                            insights[ex['name']] = insight
                            break
            
            return insights
            
        except Exception as e:
            print(f"⚠️ AI exercise insights unavailable: {e}")
            return {}

    def generate_trend_analysis(self, comprehensive_trends: Dict, periodization: Dict) -> str:
        """Generate AI analysis of overall trends and patterns."""
        if not self.available:
            return None
            
        try:
            # Extract key trend data
            trajectory = comprehensive_trends.get("fitness_trajectory", "Unknown")
            avg_progression = comprehensive_trends.get("avg_progression_rate", 0)
            frequency = comprehensive_trends.get("training_frequency", 0)
            program_status = periodization.get("program_status", "Unknown")
            plateau_pct = periodization.get("plateau_percentage", 0)
            
            # Count exercise categories
            progressing = len(periodization.get("progressing_exercises", []))
            plateaued = len(periodization.get("plateaued_exercises", []))
            smart_adjustments = len(periodization.get("smart_adjustments", []))
            
            prompt = f"""As an experienced strength coach, analyze these training trends and provide strategic insights:

OVERALL TRENDS:
- Trajectory: {trajectory}
- Average progression: {avg_progression:+.1f}kg/week
- Training frequency: {frequency:.1f} sessions/week
- Program status: {program_status}
- Plateau rate: {plateau_pct:.0f}%

EXERCISE BREAKDOWN:
- Progressing: {progressing} exercises
- Plateaued: {plateaued} exercises  
- Smart adjustments: {smart_adjustments} exercises

Provide 2-3 strategic insights about:
1. What these trends reveal about training effectiveness
2. One key recommendation for program optimization
3. Any warning signs or positive indicators to note

Keep response to 2-3 sentences maximum. Be specific and actionable."""

            response = openai_client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "system",
                    "content": "You are a strategic strength coach who analyzes training patterns to optimize long-term progress."
                }, {
                    "role": "user",
                    "content": prompt
                }],
                max_tokens=120,
                temperature=0.6
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"⚠️ AI trend analysis unavailable: {e}")
            return None

    def generate_next_day_overview(self, last_session: Dict, next_workout_info: Dict, 
                                 comprehensive_trends: Dict, volume_recovery: Dict) -> str:
        """Generate comprehensive AI overview and recommendations for the next day."""
        if not self.available:
            return None
            
        try:
            # Determine next session type
            next_workout = next_workout_info.get("workout_name", "Unknown")
            is_rest_day = next_workout_info.get("is_rest_day", False)
            days_since_last = volume_recovery.get("days_since_last", 0)
            recovery_status = volume_recovery.get("recovery_status", "Unknown")
            
            # Get adjustment count
            adjustments_needed = 0
            if last_session and last_session.get("exercises"):
                for ex in last_session["exercises"]:
                    if ex["verdict"] in ["⬇️ too heavy", "⬆️ too light"]:
                        adjustments_needed += 1
            
            # Overall trajectory
            trajectory = comprehensive_trends.get("fitness_trajectory", "Unknown")
            avg_progression = comprehensive_trends.get("avg_progression_rate", 0)
            
            if is_rest_day:
                prompt = f"""As a recovery specialist coach, provide a comprehensive rest day plan:

RECOVERY CONTEXT:
- Last session grade: {last_session.get('workout_title', 'Unknown') if last_session else 'No recent session'}
- Days since last workout: {days_since_last}
- Recovery status: {recovery_status}
- Overall progress: {trajectory} ({avg_progression:+.1f}kg/week)

Create a strategic rest day plan covering:
1. Recovery priorities (sleep, nutrition, mobility)
2. Light activity recommendations
3. Mental preparation for next training session

Keep to 3-4 actionable points. Be specific and encouraging."""
            else:
                prompt = f"""As a workout planning coach, create a comprehensive next session strategy:

NEXT SESSION INFO:
- Workout: {next_workout}
- Adjustments needed: {adjustments_needed} exercises from last session
- Recovery status: {recovery_status}
- Overall progress: {trajectory} ({avg_progression:+.1f}kg/week)

Create a strategic training day plan covering:
1. Pre-workout preparation (warm-up focus, mindset)
2. Key execution priorities (RPE targets, form cues)
3. Post-workout optimization (cool-down, recovery)

Keep to 3-4 actionable points. Be specific and motivational."""

            response = openai_client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "system",
                    "content": "You are a comprehensive strength coach who plans optimal training and recovery strategies."
                }, {
                    "role": "user",
                    "content": prompt
                }],
                max_tokens=180,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"⚠️ AI next day overview unavailable: {e}")
            return None

    def generate_recovery_insights(self, volume_recovery: Dict, comprehensive_trends: Dict) -> str:
        """Generate AI insights for recovery and preparation."""
        if not self.available:
            return None
            
        try:
            # Extract recovery data
            days_since_last = volume_recovery.get("days_since_last", 0)
            frequency = comprehensive_trends.get("training_frequency", 0)
            volume_trend = volume_recovery.get("volume_trend", "stable")
            recovery_status = volume_recovery.get("recovery_status", "Unknown")
            
            prompt = f"""As a recovery specialist, analyze this training pattern and provide recovery insights:

RECOVERY METRICS:
- Days since last session: {days_since_last}
- Training frequency: {frequency:.1f} sessions/week
- Volume trend: {volume_trend}
- Recovery status: {recovery_status}

Provide 1-2 specific recovery recommendations focusing on:
- Sleep/nutrition priorities
- Active recovery suggestions
- Signs to watch for overtraining/underrecovery

Keep concise and actionable (2 sentences max)."""

            response = openai_client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "system",
                    "content": "You are a recovery specialist coach focused on optimizing training adaptations through smart recovery."
                }, {
                    "role": "user",
                    "content": prompt
                }],
                max_tokens=100,
                temperature=0.6
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"⚠️ AI recovery insights unavailable: {e}")
            return None

# Import routine configuration
try:
    from routine_config import CYCLE_PATTERN, ROUTINE_TITLE_MAPPING, EXERCISE_PATTERNS
    ROUTINE_CONFIG_AVAILABLE = True
except ImportError:
    # No routine configuration - skip cyclical routine tracking
    CYCLE_PATTERN = None
    ROUTINE_TITLE_MAPPING = None
    EXERCISE_PATTERNS = None
    ROUTINE_CONFIG_AVAILABLE = False

class WorkoutCycle:
    """Manages cyclical workout routines and determines next workout day."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        
        # Check if routine configuration is available
        if not ROUTINE_CONFIG_AVAILABLE:
            self.cycle_pattern = None
            self.routine_title_mapping = None
            self.exercise_patterns = None
            self.config_available = False
        else:
            self.cycle_pattern = CYCLE_PATTERN
            self.routine_title_mapping = ROUTINE_TITLE_MAPPING
            self.exercise_patterns = EXERCISE_PATTERNS
            self.config_available = True
        
        self.client = None
    
    def is_available(self) -> bool:
        """Check if cyclical routine tracking is available."""
        return self.config_available
    
    def _get_client(self):
        """Lazy initialization of Hevy client."""
        if self.client is None:
            self.client = HevyStatsClient(self.api_key)
        return self.client
    
    def get_user_routines(self) -> List[Dict]:
        """Fetch user's defined routines from Hevy API."""
        try:
            client = self._get_client()
            response = requests.get(
                "https://api.hevyapp.com/v1/routines",
                headers={
                    "accept": "application/json",
                    "api-key": self.api_key
                },
                params={"page": 1, "pageSize": 10}
            )
            response.raise_for_status()
            data = response.json()
            return data.get("routines", [])
        except Exception as e:
            print(f"⚠️ Could not fetch routines: {e}")
            return []
    
    def determine_current_cycle_day(self, df: pd.DataFrame) -> int:
        """Determine which day of the cycle the user is currently on based on recent workouts."""
        if not self.config_available:
            return 0  # No configuration available
            
        if len(df) == 0:
            return 0  # Default to Day 1
        
        # Get unique workouts (by date and title) rather than individual exercise sets
        workout_info = df.groupby(['date', 'workout']).first().reset_index()
        recent_workouts = workout_info.sort_values('date').tail(5)  # Look at last 5 workouts
        
        # First, check if the most recent workout (regardless of type) is a rest day
        last_workout = recent_workouts.iloc[-1]
        last_workout_title = last_workout.get('workout', '').lower()
        last_workout_date = last_workout.get('date')
        exercises = df[df['date'] == last_workout_date]['exercise'].unique()
        
        # Detect rest days by title patterns or cardio-only workouts
        rest_day_indicators = ['rest', 'treadmill', 'cardio', 'recovery']
        is_likely_rest_day = (
            any(indicator in last_workout_title for indicator in rest_day_indicators) or
            (len(exercises) == 1 and 'treadmill' in ' '.join(exercises).lower())
        )
        
        if is_likely_rest_day:
            # Find which rest day this might be by matching title patterns
            rest_day_match = None
            for i, cycle_day in enumerate(self.cycle_pattern):
                cycle_day_lower = cycle_day.lower()
                if 'rest' in cycle_day_lower or 'treadmill' in cycle_day_lower:
                    # Check if this specific rest day matches the workout title better
                    if 'treadmill' in last_workout_title and 'treadmill' in cycle_day_lower:
                        rest_day_match = i
                        break
                    elif 'rest' in last_workout_title and 'rest' in cycle_day_lower and 'treadmill' not in cycle_day_lower:
                        rest_day_match = i
                        break
                    elif rest_day_match is None:  # First rest day found as fallback
                        rest_day_match = i
            
            if rest_day_match is not None:
                # This was a rest day, so next day is the one after this rest day
                return (rest_day_match + 1) % len(self.cycle_pattern)
            
            # If no rest day found in cycle pattern, assume it was day 3 (your typical rest day)
            return 3  # Day 4 - Upper (Pull) comes after Day 3 - Rest / Treadmill
        
        # If most recent workout is not a rest day, look for strength training workouts
        for _, workout in recent_workouts.iloc[::-1].iterrows():  # Reverse order - most recent first
            workout_title = workout.get('workout', '')
            if workout_title in self.routine_title_mapping:
                last_cycle_day = self.routine_title_mapping[workout_title]
                # Next day in cycle
                return (last_cycle_day + 1) % len(self.cycle_pattern)
        
        # Use configurable exercise patterns for strength training workouts
        exercise_str = ' '.join(exercises).lower()
        
        for pattern_name, pattern_config in self.exercise_patterns.items():
            keywords = pattern_config["keywords"]
            next_cycle_day = pattern_config["next_cycle_day"]
            
            if any(word in exercise_str for word in keywords):
                return next_cycle_day
        
        # Default to Day 1 if can't determine
        return 0
    
    def get_next_workout_info(self, df: pd.DataFrame) -> Dict:
        """Get information about the next workout in the cycle."""
        if not self.config_available:
            return {"error": "No routine configuration available"}
            
        current_day_idx = self.determine_current_cycle_day(df)
        next_workout = self.cycle_pattern[current_day_idx]
        
        # Get routine info if available
        routines = self.get_user_routines()
        matching_routine = None
        
        for routine in routines:
            if routine['title'] in self.routine_title_mapping:
                if self.routine_title_mapping[routine['title']] == current_day_idx:
                    matching_routine = routine
                    break
        
        return {
            "cycle_day_index": current_day_idx,
            "workout_name": next_workout,
            "is_rest_day": "rest" in next_workout.lower(),
            "routine_data": matching_routine,
            "days_until_same_workout": len(self.cycle_pattern)
        }
    
    def get_routine_specific_recommendations(self, df: pd.DataFrame, next_workout_info: Dict) -> Dict:
        """Generate recommendations specific to the upcoming workout routine."""
        if next_workout_info["is_rest_day"]:
            return {
                "type": "rest_day",
                "recommendations": [
                    "🛌 Focus on recovery and sleep quality",
                    "🚶‍♂️ Light cardio (treadmill walking) is optional",
                    "💧 Stay hydrated and maintain nutrition",
                    "📱 Review form videos for your next training day"
                ]
            }
        
        routine_data = next_workout_info.get("routine_data")
        if not routine_data:
            return {"type": "general", "recommendations": ["No specific routine data available"]}
        
        # Filter historical data for this specific routine
        cycle_day_idx = next_workout_info["cycle_day_index"]
        matching_workouts = []
        
        # Find historical data for this same workout type
        for routine_title, day_idx in self.routine_title_mapping.items():
            if day_idx == cycle_day_idx:
                matching_workouts = df[df['workout'].str.contains(routine_title.split(' -')[0], na=False)]
                break
        
        recommendations = []
        exercise_recommendations = {}
        
        # Analyze each exercise in the upcoming routine
        for exercise_data in routine_data["exercises"]:
            exercise_name = exercise_data["title"]
            
            if exercise_name in ["Warm Up", "Notes", "Treadmill"]:
                continue
                
            # Find historical data for this exercise
            exercise_history = df[df['exercise'] == exercise_name].sort_values('date')
            
            if len(exercise_history) > 0:
                latest = exercise_history.iloc[-1]
                
                # Get the target weight/reps from routine template
                normal_sets = [s for s in exercise_data["sets"] if s["type"] == "normal"]
                if normal_sets:
                    template_weight = normal_sets[0].get("weight_kg")
                    template_reps = normal_sets[0].get("reps")
                    
                    # Compare with latest performance
                    last_weight = latest.get('weight', 0)
                    last_reps = latest.get('reps', 0)
                    last_rpe = latest.get('rpe', 8.0)
                    
                    recommendation = self._generate_exercise_recommendation(
                        exercise_name, last_weight, last_reps, last_rpe, 
                        template_weight, template_reps
                    )
                    
                    if recommendation:
                        exercise_recommendations[exercise_name] = recommendation
        
        return {
            "type": "workout_specific",
            "workout_name": next_workout_info["workout_name"],
            "exercise_recommendations": exercise_recommendations,
            "general_recommendations": [
                f"📋 Preparing for: {next_workout_info['workout_name']}",
                f"⏰ This workout repeats every {next_workout_info['days_until_same_workout']} days",
                "🎯 Focus on progressive overload where RPE allows"
            ]
        }
    
    def _generate_exercise_recommendation(self, exercise_name: str, last_weight: float, 
                                        last_reps: float, last_rpe: float,
                                        template_weight: Optional[float], 
                                        template_reps: Optional[int]) -> Dict:
        """Generate specific recommendation for an exercise."""
        recommendation = {
            "current_weight": last_weight,
            "current_reps": last_reps,
            "last_rpe": last_rpe,
            "action": "maintain",
            "suggested_weight": last_weight,
            "reasoning": ""
        }
        
        # Check if this is an assisted exercise (weight = assistance, higher = easier)
        is_assisted = is_assisted_exercise(exercise_name)
        
        # RPE-based recommendations
        if last_rpe < 7.5:
            # Too easy - need to make it harder
            if is_assisted:
                # For assisted exercises: decrease assistance weight to make it harder
                suggested_decrease = max(2.5, last_weight * 0.025)  # At least 2.5kg or 2.5% decrease
                recommendation.update({
                    "action": "decrease",
                    "suggested_weight": max(0, last_weight - suggested_decrease),
                    "reasoning": f"RPE {last_rpe} too low, reduce assistance by {suggested_decrease:.1f}kg to make it harder"
                })
            else:
                # For regular exercises: increase load weight
                suggested_increase = max(2.5, last_weight * 0.025)  # At least 2.5kg or 2.5% increase
                recommendation.update({
                    "action": "increase",
                    "suggested_weight": last_weight + suggested_increase,
                    "reasoning": f"RPE {last_rpe} indicates room for progression (+{suggested_increase:.1f}kg)"
                })
        elif last_rpe > 9.0:
            # Too hard - need to make it easier
            if is_assisted:
                # For assisted exercises: increase assistance weight to make it easier
                suggested_increase = max(2.5, last_weight * 0.05)  # At least 2.5kg or 5% increase
                recommendation.update({
                    "action": "increase",
                    "suggested_weight": last_weight + suggested_increase,
                    "reasoning": f"RPE {last_rpe} too high, increase assistance by {suggested_increase:.1f}kg for better form"
                })
            else:
                # For regular exercises: decrease load weight
                suggested_decrease = max(2.5, last_weight * 0.05)  # At least 2.5kg or 5% decrease
                recommendation.update({
                    "action": "decrease", 
                    "suggested_weight": max(0, last_weight - suggested_decrease),
                    "reasoning": f"RPE {last_rpe} too high, reduce by {suggested_decrease:.1f}kg for better form"
                })
        else:
            recommendation["reasoning"] = f"RPE {last_rpe} is in good range - maintain current weight"
        
        return recommendation

class EmailSender:
    """Handle email notifications for Hevy coaching reports."""
    
    def __init__(self):
        self.email_user = os.getenv("EMAIL_USER")
        self.email_password = os.getenv("EMAIL_PASSWORD")
        self.to_email = os.getenv("TO_EMAIL", self.email_user)  # Default to sender if not specified
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
    
    def test_connection(self) -> bool:
        """Test email configuration without sending."""
        if not self.email_user or not self.email_password:
            print("❌ Missing EMAIL_USER or EMAIL_PASSWORD environment variables")
            return False
        
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_user, self.email_password)
            server.quit()
            print(f"✅ Successfully connected to {self.smtp_server}")
            return True
        except Exception as e:
            print(f"❌ Email connection failed: {e}")
            return False
    
    def create_condensed_email_content(self, report_content: str) -> str:
        """Create a condensed, mobile-friendly version of the report for email."""
        lines = report_content.split('\n')
        
        # Extract key metrics
        grade = ""
        assessment = ""
        progression = ""
        adjustments_needed = []
        good_weights = []
        key_insights = []
        
        # Parse the report for key information
        in_adjustments = False
        in_good_weights = False
        in_insights = False
        
        for line in lines:
            # Session quality
            if "Overall Grade" in line and ":" in line:
                grade = line.split(":", 1)[1].strip()
            elif "Assessment" in line and ":" in line:
                assessment = line.split(":", 1)[1].strip()
            elif "Progression" in line and "progressed" in line:
                progression = line.split(":", 1)[1].strip()
            
            # Next session recommendations
            elif "Weight Adjustments Needed" in line:
                in_adjustments = True
                in_good_weights = False
                in_insights = False
            elif "Keep These Weights" in line:
                in_adjustments = False
                in_good_weights = True
                in_insights = False
            elif "Smart Focus Points" in line:
                in_adjustments = False
                in_good_weights = False
                in_insights = True
            elif line.startswith("• **") and in_adjustments:
                exercise = line.split("**")[1]
                adjustments_needed.append(exercise)
            elif line.startswith("• **") and in_good_weights:
                exercise = line.split("**")[1]
                good_weights.append(exercise)
            elif line.startswith("• ") and in_insights:
                key_insights.append(line[2:])  # Remove bullet point
        
        # Create condensed content
        condensed = f"""
        <div class="quick-summary">
            <h2>📊 Today's Session Summary</h2>
            <div class="grade-box">
                <span class="grade">{grade}</span>
                <p>{assessment}</p>
                <p class="progression">{progression}</p>
            </div>
        </div>

        <div class="action-section">
            <h2>🎯 Next Session Actions</h2>
        """
        
        if adjustments_needed:
            condensed += f"""
            <div class="adjustments">
                <h3>🔧 Weight Changes Needed ({len(adjustments_needed)})</h3>
                <ul>
            """
            for exercise in adjustments_needed[:5]:  # Show max 5
                condensed += f"<li><strong>{exercise}</strong></li>"
            if len(adjustments_needed) > 5:
                condensed += f"<li><em>...and {len(adjustments_needed) - 5} more</em></li>"
            condensed += "</ul></div>"
        
        if good_weights:
            count_display = f" ({len(good_weights)})" if len(good_weights) > 3 else ""
            condensed += f"""
            <div class="good-weights">
                <h3>✅ Keep Current Weights{count_display}</h3>
            """
            if len(good_weights) <= 3:
                condensed += "<ul>"
                for exercise in good_weights:
                    condensed += f"<li>{exercise}</li>"
                condensed += "</ul>"
            else:
                condensed += f"<p>All other exercises are at optimal weights - maintain current loads!</p>"
            condensed += "</div>"
        
        if key_insights:
            condensed += f"""
            <div class="insights">
                <h3>💡 Key Focus Points</h3>
                <ul>
            """
            for insight in key_insights[:3]:  # Show top 3 insights
                condensed += f"<li>{insight}</li>"
            condensed += "</ul></div>"
        
        condensed += "</div>"
        
        # Add simple collapsible full report (no scrolling, just expand)
        full_html = self.markdown_to_html(report_content)
        condensed += f"""
        <div class="full-report">
            <details>
                <summary>📄 View Complete Detailed Analysis</summary>
                <div class="detailed-content">
                    {full_html}
                </div>
            </details>
        </div>
        """
        
        return condensed
    
    def send_report(self, report_content: str, markdown_file: str = None) -> bool:
        """Send the coaching report via email."""
        if not self.email_user or not self.email_password:
            print("❌ Email credentials not configured")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_user
            msg['To'] = self.to_email
            msg['Subject'] = f"🏋️‍♂️ Hevy Coaching Report - {datetime.now().strftime('%Y-%m-%d')}"
            
            # Use markdown file content if available, otherwise use report_content
            content_to_convert = report_content
            if markdown_file and os.path.exists(markdown_file):
                try:
                    with open(markdown_file, 'r', encoding='utf-8') as f:
                        content_to_convert = f.read()
                except Exception as e:
                    print(f"⚠️ Could not read markdown file, using report_content: {e}")
            
            # Convert to HTML with enhanced formatting
            full_html_content = self.markdown_to_html(content_to_convert)
            
            # Create comprehensive HTML email body
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        max-width: 800px;
                        margin: 0 auto;
                        padding: 10px;
                        background-color: #f8f9fa;
                    }}
                    .container {{
                        background-color: white;
                        padding: 20px;
                        border-radius: 8px;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    }}
                    
                    /* Headers */
                    h1.main-title {{
                        color: #2c3e50;
                        border-bottom: 3px solid #3498db;
                        padding: 15px;
                        margin-bottom: 20px;
                        font-size: 1.8em;
                        text-align: center;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        border-radius: 8px;
                    }}
                    .quick-summary-header h1 {{
                        background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
                        color: #2c3e50;
                        padding: 15px;
                        border-radius: 8px;
                        text-align: center;
                        margin: 20px 0;
                        font-size: 1.5em;
                    }}
                    h2.section-header {{
                        color: #34495e;
                        border-bottom: 2px solid #ecf0f1;
                        padding: 12px 0 8px 0;
                        margin-top: 30px;
                        margin-bottom: 15px;
                        font-size: 1.3em;
                        background: #f8f9fa;
                        padding-left: 10px;
                        border-left: 4px solid #3498db;
                    }}
                    h3.subsection-header {{
                        color: #2c3e50;
                        margin-top: 20px;
                        margin-bottom: 10px;
                        font-size: 1.1em;
                        padding: 8px 0;
                        border-bottom: 1px solid #dee2e6;
                    }}
                    h4 {{
                        color: #2c3e50;
                        margin: 15px 0 8px 0;
                        font-size: 1.0em;
                    }}
                    
                    /* Text styling */
                    p {{
                        margin: 10px 0;
                    }}
                    strong {{
                        color: #2c3e50;
                    }}
                    
                    /* Lists */
                    ul, ol {{
                        margin: 10px 0;
                        padding-left: 25px;
                    }}
                    li {{
                        margin: 5px 0;
                    }}
                    
                    /* Code and preformatted text */
                    pre, code {{
                        background-color: #f8f9fa;
                        padding: 2px 6px;
                        border-radius: 4px;
                        font-family: 'Monaco', 'Menlo', monospace;
                        font-size: 0.9em;
                    }}
                    pre {{
                        padding: 12px;
                        margin: 10px 0;
                        overflow-x: auto;
                        border-left: 4px solid #3498db;
                    }}
                    
                    /* AI sections */
                    .ai-section {{
                        background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 50%, #fecfef 100%);
                        border-left: 4px solid #e91e63;
                        padding: 15px;
                        margin: 15px 0;
                        border-radius: 0 6px 6px 0;
                    }}
                    .ai-section h3 {{
                        margin-top: 0;
                        color: #c2185b;
                    }}
                    .ai-content {{
                        margin: 8px 0;
                        line-height: 1.6;
                    }}
                    
                    /* Metrics */
                    .metric {{
                        padding: 12px 15px;
                        margin: 8px 0;
                        border-radius: 6px;
                        border-left: 4px solid;
                        font-weight: 500;
                    }}
                    .metric.primary {{
                        background: #e3f2fd;
                        border-color: #2196f3;
                    }}
                    .metric.secondary {{
                        background: #f3e5f5;
                        border-color: #9c27b0;
                    }}
                    .metric.success {{
                        background: #e8f5e8;
                        border-color: #4caf50;
                    }}
                    .metric.warning {{
                        background: #fff3e0;
                        border-color: #ff9800;
                    }}
                    .metric.info {{
                        background: #f0f4c3;
                        border-color: #8bc34a;
                    }}
                    
                    /* Recommendations */
                    .recommendations {{
                        margin: 15px 0;
                        padding: 15px;
                        border-radius: 6px;
                        border-left: 4px solid;
                    }}
                    .recommendations.increases {{
                        background: #e8f5e8;
                        border-color: #4caf50;
                    }}
                    .recommendations.decreases {{
                        background: #ffebee;
                        border-color: #f44336;
                    }}
                    .recommendations.maintain {{
                        background: #e3f2fd;
                        border-color: #2196f3;
                    }}
                    .recommendations.general {{
                        background: #f3e5f5;
                        border-color: #9c27b0;
                    }}
                    .recommendations h4 {{
                        margin-top: 0;
                        margin-bottom: 10px;
                    }}
                    .recommendations ul {{
                        margin: 10px 0;
                        padding-left: 20px;
                    }}
                    .exercise-rec {{
                        margin: 8px 0;
                        padding: 4px 0;
                    }}
                    .general-rec {{
                        margin: 6px 0;
                    }}
                    
                    /* Exercise Analysis */
                    .exercise-analysis {{
                        background: #f8f9fa;
                        border: 1px solid #dee2e6;
                        border-radius: 6px;
                        margin: 10px 0;
                        padding: 12px;
                    }}
                    .exercise-analysis h4 {{
                        margin-top: 0;
                        margin-bottom: 8px;
                        color: #2c3e50;
                    }}
                    .exercise-details {{
                        font-size: 0.95em;
                        line-height: 1.5;
                    }}
                    
                    /* Priority Actions */
                    .priority-actions {{
                        background: #fff3cd;
                        border-left: 4px solid #ffc107;
                        padding: 15px;
                        margin: 15px 0;
                        border-radius: 0 6px 6px 0;
                    }}
                    .priority-actions h3 {{
                        margin-top: 0;
                        color: #856404;
                    }}
                    .priority-actions ol {{
                        margin: 10px 0;
                        padding-left: 25px;
                    }}
                    .priority-item {{
                        margin: 8px 0;
                        font-weight: 500;
                    }}
                    
                    /* Overall Progress */
                    .overall-progress {{
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        padding: 15px;
                        border-radius: 6px;
                        text-align: center;
                        margin: 15px 0;
                        font-weight: bold;
                    }}
                    
                    /* Grades and indicators */
                    .grade {{
                        padding: 4px 8px;
                        border-radius: 4px;
                        font-weight: bold;
                        margin: 0 4px;
                    }}
                    .grade-A, .grade-A\\+ {{
                        background: #4caf50;
                        color: white;
                    }}
                    .grade-B, .grade-B\\+ {{
                        background: #8bc34a;
                        color: white;
                    }}
                    .grade-C, .grade-C\\+ {{
                        background: #ff9800;
                        color: white;
                    }}
                    .grade-D {{
                        background: #f44336;
                        color: white;
                    }}
                    
                    .trend {{
                        font-size: 1.2em;
                        margin: 0 4px;
                    }}
                    
                    .percentage {{
                        font-weight: bold;
                        padding: 2px 4px;
                        border-radius: 3px;
                        background: #f8f9fa;
                    }}
                    
                    /* Horizontal rules */
                    hr.section-divider {{
                        border: none;
                        border-top: 1px solid #dee2e6;
                        margin: 20px 0;
                    }}
                    hr.major-divider {{
                        border: none;
                        border-top: 3px solid #3498db;
                        margin: 30px 0;
                    }}
                    
                    /* Lists */
                    ul.main-list {{
                        margin: 15px 0;
                        padding-left: 25px;
                    }}
                    li.main-point {{
                        margin: 8px 0;
                        line-height: 1.5;
                    }}
                    
                    /* Tables */
                    table {{
                        width: 100%;
                        border-collapse: collapse;
                        margin: 15px 0;
                        background: white;
                        border-radius: 6px;
                        overflow: hidden;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }}
                    th, td {{
                        border: 1px solid #dee2e6;
                        padding: 12px 15px;
                        text-align: left;
                    }}
                    th {{
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        font-weight: bold;
                    }}
                    tr:nth-child(even) {{
                        background: #f8f9fa;
                    }}
                    
                    /* Mobile responsiveness */
                    @media (max-width: 600px) {{
                        body {{
                            padding: 5px;
                        }}
                        .container {{
                            padding: 15px;
                        }}
                        h1 {{
                            font-size: 1.4em;
                        }}
                        h2 {{
                            font-size: 1.2em;
                        }}
                        h3 {{
                            font-size: 1.0em;
                        }}
                        pre {{
                            font-size: 0.8em;
                            padding: 8px;
                        }}
                        table {{
                            font-size: 0.9em;
                        }}
                        th, td {{
                            padding: 6px 8px;
                        }}
                    }}
                    
                    /* Print styles */
                    @media print {{
                        .container {{
                            box-shadow: none;
                            border: 1px solid #ccc;
                        }}
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    {full_html_content}
                    
                    <div class="footer" style="margin-top: 40px; padding-top: 20px; border-top: 2px solid #ecf0f1; text-align: center; color: #7f8c8d; font-size: 0.9em;">
                        <p><strong>📧 Generated on {datetime.now().strftime('%Y-%m-%d at %H:%M')}</strong></p>
                        <p>🤖 Enhanced with AI coaching insights | 💪 Keep crushing your goals!</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Create plain text fallback (condensed version)
            plain_text = self.create_plain_text_summary(report_content)
            text_body = f"""🏋️‍♂️ Daily Hevy Coaching Report

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}

{plain_text}

─────────────────────────────────────────────────────────────
💡 AI-powered coaching analysis
Generated by Hevy Coach Pro
            """
            
            # Attach both HTML and plain text versions
            msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
            msg.attach(MIMEText(html_body, 'html', 'utf-8'))
            
            # Still attach markdown file as backup (optional)
            if markdown_file and os.path.exists(markdown_file):
                with open(markdown_file, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {os.path.basename(markdown_file)}'
                )
                msg.attach(part)
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_user, self.email_password)
            text = msg.as_string()
            server.sendmail(self.email_user, self.to_email, text)
            server.quit()
            
            print(f"✅ Report emailed successfully to {self.to_email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False
    
    def create_plain_text_summary(self, content: str) -> str:
        """Create a plain text summary of key points."""
        lines = content.split('\n')
        
        summary = ""
        
        # Extract session quality
        for line in lines:
            if "Overall Grade" in line:
                summary += f"📊 {line.strip()}\n"
            elif "Assessment" in line:
                summary += f"📝 {line.strip()}\n"
            elif "Progression" in line and "progressed" in line:
                summary += f"💪 {line.strip()}\n"
        
        summary += f"\n🎯 NEXT SESSION ACTIONS:\n"
        summary += f"────────────────────────\n"
        
        # Extract weight adjustments
        in_adjustments = False
        adjustment_count = 0
        for line in lines:
            if "Weight Adjustments Needed" in line:
                in_adjustments = True
            elif "Keep These Weights" in line:
                in_adjustments = False
            elif line.startswith("• **") and in_adjustments and adjustment_count < 3:
                exercise = line.split("**")[1]
                summary += f"🔧 {exercise}\n"
                adjustment_count += 1
        
        if adjustment_count == 0:
            summary += f"✅ All exercises at optimal weights!\n"
        
        # Add key insights
        summary += f"\n💡 KEY FOCUS:\n"
        summary += f"• Aim for RPE 7.5-9 for optimal growth\n"
        summary += f"• Listen to your body and adjust accordingly\n"
        
        return summary
    
    def markdown_to_html(self, content: str) -> str:
        """Convert markdown-formatted report content to properly formatted HTML."""
        import re
        
        # Start with the content
        html = content
        
        # Convert main headers with special styling
        html = re.sub(r'^🏋️‍♂️  (.+)$', r'<h1 class="main-title">🏋️‍♂️ \1</h1>', html, flags=re.MULTILINE)
        html = re.sub(r'^🚀 (.+)$', r'<div class="quick-summary-header"><h1>🚀 \1</h1></div>', html, flags=re.MULTILINE)
        
        # Convert section headers with emojis 
        html = re.sub(r'^(⭐|📈|🎯|🔄|📊|🏆|📋) \*\*(.+?)\*\*$', r'<h2 class="section-header">\1 <strong>\2</strong></h2>', html, flags=re.MULTILINE)
        
        # Convert subsection headers
        html = re.sub(r'^\*\*(.+?)\*\*$', r'<h3 class="subsection-header">\1</h3>', html, flags=re.MULTILINE)
        
        # Convert bold text
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
        
        # Convert section dividers
        html = re.sub(r'^-{50,}$', '<hr class="section-divider">', html, flags=re.MULTILINE)
        html = re.sub(r'^={50,}$', '<hr class="major-divider">', html, flags=re.MULTILINE)
        
        # Convert AI sections with special styling
        html = re.sub(r'^🤖 \*\*(.+?)\*\*:$', r'<div class="ai-section"><h3>🤖 \1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^   (.+)$', r'<p class="ai-content">\1</p></div>', html, flags=re.MULTILINE)
        
        # Convert metric lines with special styling
        html = re.sub(r'^🎯 \*\*(.+?)\*\*: (.+)$', r'<div class="metric primary">🎯 <strong>\1</strong>: \2</div>', html, flags=re.MULTILINE)
        html = re.sub(r'^📝 \*\*(.+?)\*\*: (.+)$', r'<div class="metric secondary">📝 <strong>\1</strong>: \2</div>', html, flags=re.MULTILINE)
        html = re.sub(r'^💪 \*\*(.+?)\*\*: (.+)$', r'<div class="metric success">💪 <strong>\1</strong>: \2</div>', html, flags=re.MULTILINE)
        html = re.sub(r'^🔥 \*\*(.+?)\*\*: (.+)$', r'<div class="metric warning">🔥 <strong>\1</strong>: \2</div>', html, flags=re.MULTILINE)
        html = re.sub(r'^📈 \*\*(.+?)\*\*: (.+)$', r'<div class="metric info">📈 <strong>\1</strong>: \2</div>', html, flags=re.MULTILINE)
        html = re.sub(r'^📅 \*\*(.+?)\*\*: (.+)$', r'<div class="metric info">📅 <strong>\1</strong>: \2</div>', html, flags=re.MULTILINE)
        html = re.sub(r'^📊 \*\*(.+?)\*\*: (.+)$', r'<div class="metric info">📊 <strong>\1</strong>: \2</div>', html, flags=re.MULTILINE)
        
        # Convert exercise recommendations with special styling
        html = re.sub(r'^📈 \*\*Suggested Increases\*\*:$', r'<div class="recommendations increases"><h4>📈 Suggested Increases</h4><ul>', html, flags=re.MULTILINE)
        html = re.sub(r'^📉 \*\*Suggested Decreases\*\*:$', r'<div class="recommendations decreases"><h4>📉 Suggested Decreases</h4><ul>', html, flags=re.MULTILINE)
        html = re.sub(r'^✅ \*\*Maintain Current Weights\*\*:$', r'<div class="recommendations maintain"><h4>✅ Maintain Current Weights</h4><ul>', html, flags=re.MULTILINE)
        html = re.sub(r'^💡 \*\*General Recommendations\*\*:$', r'</ul></div><div class="recommendations general"><h4>💡 General Recommendations</h4><ul>', html, flags=re.MULTILINE)
        
        # Convert bullet points with proper nesting
        html = re.sub(r'^   • \*\*(.+?)\*\*: (.+)$', r'<li class="exercise-rec"><strong>\1</strong>: \2</li>', html, flags=re.MULTILINE)
        html = re.sub(r'^   • (.+)$', r'<li class="general-rec">\1</li>', html, flags=re.MULTILINE)
        html = re.sub(r'^• \*\*(.+?)\*\*: (.+)$', r'<li class="main-point"><strong>\1</strong>: \2</li>', html, flags=re.MULTILINE)
        html = re.sub(r'^• (.+)$', r'<li class="main-point">\1</li>', html, flags=re.MULTILINE)
        
        # Convert exercise analysis blocks
        html = re.sub(r'^\*\*(.+?)\*\*\n((?:   .+\n)*)', r'<div class="exercise-analysis"><h4>\1</h4><div class="exercise-details">\2</div></div>', html, flags=re.MULTILINE | re.DOTALL)
        
        # Convert priority actions  
        html = re.sub(r'^⚡ \*\*Priority Actions\*\*:$', r'<div class="priority-actions"><h3>⚡ Priority Actions</h3><ol>', html, flags=re.MULTILINE)
        html = re.sub(r'^   (\d+)\. (.+)$', r'<li class="priority-item">\2</li>', html, flags=re.MULTILINE)
        
        # Convert progress indicators
        html = re.sub(r'^📊 \*\*Overall Progress\*\*: (.+)$', r'<div class="overall-progress">📊 <strong>Overall Progress</strong>: \1</div>', html, flags=re.MULTILINE)
        
        # Convert grades to styled spans
        html = re.sub(r'(A\+|A|B\+|B|C\+|C|D) \((\d+)/100\)', r'<span class="grade grade-\1">\1 (\2/100)</span>', html)
        
        # Convert trend emojis to styled spans
        html = re.sub(r'(📈|📉|➡️)', r'<span class="trend">\1</span>', html)
        
        # Convert percentages to styled spans
        html = re.sub(r'([+-]?\d+\.?\d*%)', r'<span class="percentage">\1</span>', html)
        
        # Wrap consecutive list items in ul tags where not already wrapped
        html = re.sub(r'(<li class="main-point">.*?</li>(?:\n<li class="main-point">.*?</li>)*)', r'<ul class="main-list">\1</ul>', html, flags=re.DOTALL)
        
        # Close open recommendation divs
        html = html.replace('</ul></div><div class="recommendations', '</ul></div>\n<div class="recommendations')
        html = html + '</ul></div>' if 'recommendations' in html and not html.endswith('</ul></div>') else html
        
        # Close priority actions
        html = html.replace('<ol>\n<li class="priority-item">', '<ol><li class="priority-item">')
        if 'priority-actions' in html and not html.endswith('</ol></div>'):
            html = html + '</ol></div>'
        
        # Convert line breaks to HTML paragraphs for better structure
        # Split into paragraphs first
        paragraphs = html.split('\n\n')
        formatted_paragraphs = []
        
        for para in paragraphs:
            para = para.strip()
            if para:
                # Don't wrap if already has HTML tags
                if '<div' in para or '<h' in para or '<ul' in para or '<ol' in para or '<li' in para:
                    formatted_paragraphs.append(para)
                else:
                    # Wrap plain text in paragraphs
                    para = para.replace('\n', '<br>')
                    formatted_paragraphs.append(f'<p>{para}</p>')
        
        html = '\n\n'.join(formatted_paragraphs)
        
        return html
    
    def markdown_to_plain_text(self, content: str) -> str:
        """Convert markdown-formatted content to clean plain text."""
        import re
        
        # Start with the content
        text = content
        
        # Remove markdown bold formatting
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        
        # Clean up section dividers
        text = re.sub(r'^-{50,}$', '─' * 50, text, flags=re.MULTILINE)
        text = re.sub(r'^={50,}$', '═' * 50, text, flags=re.MULTILINE)
        
        # Convert bullet points to simple dashes
        text = re.sub(r'^• ', '• ', text, flags=re.MULTILINE)
        text = re.sub(r'^  • ', '  • ', text, flags=re.MULTILINE)
        
        return text

class HevyStatsClient:
    def __init__(self, api_key: str):
        if not api_key:
            print("❌ Error: HEVY_API_KEY environment variable not set")
            print("Please run: export HEVY_API_KEY='your-api-key-here'")
            sys.exit(1)
            
        self.api_key = api_key
        self.base_url = "https://api.hevyapp.com"
        self.headers = {
            "api-key": api_key,
            "Content-Type": "application/json"
        }
    
    def get_workout_events(self, page: int = 1, page_size: int = 10, since: Optional[str] = None) -> Dict:
        """
        Fetch workout events from the Hevy API.
        
        Args:
            page: Page number (default: 1)
            page_size: Number of items per page (max 10, default: 10)
            since: ISO date string to fetch events since (default: last 30 days)
        
        Returns:
            Dictionary containing workout events data
        """
        if since is None:
            # Default to last 30 days
            since_date = datetime.now() - timedelta(days=30)
            since = since_date.isoformat() + "Z"
        
        params = {
            "page": page,
            "pageSize": min(page_size, 10),  # API max is 10
            "since": since
        }
        
        url = f"{self.base_url}/v1/workouts/events"
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching workout events: {e}")
            sys.exit(1)
    
    def get_all_recent_workouts(self, days: int = 30) -> List[Dict]:
        """
        Fetch all workout events from the last N days.
        
        Args:
            days: Number of days back to fetch (default: 30)
        
        Returns:
            List of all workout events
        """
        since_date = datetime.now() - timedelta(days=days)
        since = since_date.isoformat() + "Z"
        
        all_events = []
        page = 1
        
        print(f"🔄 Fetching workout events from last {days} days...")
        
        while True:
            data = self.get_workout_events(page=page, page_size=10, since=since)
            events = data.get("events", [])
            
            if not events:
                break
                
            all_events.extend(events)
            print(f"   📄 Page {page}: {len(events)} events")
            
            # Check if we've reached the last page
            if page >= data.get("page_count", 1):
                break
                
            page += 1
        
        print(f"✅ Total events fetched: {len(all_events)}")
        return all_events
    
    def clean_null_values(self, data):
        """
        Recursively remove null/None values from dictionaries and lists to reduce JSON file size.
        
        Args:
            data: The data structure to clean
        
        Returns:
            Cleaned data structure without null values
        """
        if isinstance(data, dict):
            cleaned = {}
            for key, value in data.items():
                if value is not None:
                    cleaned_value = self.clean_null_values(value)
                    if cleaned_value is not None and cleaned_value != {} and cleaned_value != []:
                        cleaned[key] = cleaned_value
            return cleaned
        elif isinstance(data, list):
            cleaned = []
            for item in data:
                cleaned_item = self.clean_null_values(item)
                if cleaned_item is not None and cleaned_item != {} and cleaned_item != []:
                    cleaned.append(cleaned_item)
            return cleaned
        else:
            return data

def filter_recent_data(df: pd.DataFrame, days: int = 90) -> pd.DataFrame:
    """
    Filter DataFrame to only include data from the last N days.
    
    Args:
        df: DataFrame with workout data
        days: Number of days to keep (default: 90)
    
    Returns:
        Filtered DataFrame with only recent data
    """
    if len(df) == 0:
        return df
    
    # Ensure date column is datetime
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    
    # Calculate cutoff date
    cutoff_date = datetime.now() - timedelta(days=days)
    
    # Filter to recent data only
    recent_df = df[df["date"] >= cutoff_date]
    
    print(f"🔄 Filtered to last {days} days: {len(recent_df)} sets from {recent_df['date'].min()} to {recent_df['date'].max()}")
    
    return recent_df

def filter_excluded_exercises(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter out exercises that should be ignored from analysis.
    
    Args:
        df: DataFrame with workout data
    
    Returns:
        Filtered DataFrame without excluded exercises
    """
    if len(df) == 0:
        return df
    
    # List of exercises to exclude from analysis
    EXCLUDED_EXERCISES = [
        "Warm Up",
        "Treadmill",
        "Walking", 
        "Running",
        "Elliptical",
        "Bike",
        "Stair Climber",
        "Rest",
        "Stretching",
        "Meditation",
        "Cardio"
    ]
    
    original_count = len(df)
    
    # Filter out excluded exercises (case-insensitive)
    df_filtered = df[~df["exercise"].str.lower().isin([ex.lower() for ex in EXCLUDED_EXERCISES])]
    
    excluded_count = original_count - len(df_filtered)
    excluded_exercises = df[df["exercise"].str.lower().isin([ex.lower() for ex in EXCLUDED_EXERCISES])]["exercise"].unique()
    
    if excluded_count > 0:
        print(f"🚫 Excluded {excluded_count} sets from {len(excluded_exercises)} exercise types: {', '.join(excluded_exercises)}")
    
    return df_filtered

def events_to_df(events_file: str) -> pd.DataFrame:
    """
    Convert workout events JSON to a pandas DataFrame.
    
    Args:
        events_file: Path to the JSON file containing workout events
    
    Returns:
        DataFrame with flattened workout data
    """
    try:
        with open(events_file, 'r') as f:
            events = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: File {events_file} not found")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"❌ Error: Invalid JSON in {events_file}")
        sys.exit(1)
    
    rows = []
    for event in events:
        if event.get("type") != "updated":
            continue
            
        workout = event.get("workout", {})
        workout_date = datetime.fromisoformat(workout.get("start_time", "").replace('Z', '+00:00'))
        workout_title = workout.get("title", "Untitled Workout")
        
        for exercise in workout.get("exercises", []):
            exercise_title = exercise.get("title", "Unknown Exercise")
            exercise_notes = exercise.get("notes", "")
            
            for set_data in exercise.get("sets", []):
                if set_data.get("type") != "normal":  # Skip warm-ups, drop sets, etc.
                    continue
                    
                rows.append({
                    "date": workout_date.date(),
                    "workout": workout_title,
                    "exercise": exercise_title,
                    "exercise_notes": exercise_notes,
                    "weight": set_data.get("weight_kg", 0.0) or 0.0,
                    "reps": set_data.get("reps", 0) or 0,
                    "rpe": set_data.get("rpe"),
                    "duration_seconds": set_data.get("duration_seconds"),
                    "distance_meters": set_data.get("distance_meters"),
                    "set_index": set_data.get("index", 0)
                })
    
    df = pd.DataFrame(rows)
    if len(df) > 0:
        df = df.sort_values(["date", "exercise", "set_index"])
    
    print(f"📊 Converted {len(df)} sets from {len(events)} events")
    return df

def latest_session_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute statistics for the latest session of each exercise.
    
    Args:
        df: DataFrame with workout data
    
    Returns:
        DataFrame with latest session stats per exercise
    """
    if len(df) == 0:
        return pd.DataFrame()
    
    # Get the most recent date for each exercise
    latest_dates = df.groupby("exercise")["date"].max()
    
    # Filter to only include sets from the latest session of each exercise
    latest_rows = []
    for exercise, latest_date in latest_dates.items():
        exercise_latest = df[(df["exercise"] == exercise) & (df["date"] == latest_date)]
        latest_rows.append(exercise_latest)
    
    if not latest_rows:
        return pd.DataFrame()
    
    latest_df = pd.concat(latest_rows, ignore_index=True)
    
    # Calculate stats per exercise
    stats = latest_df.groupby("exercise").agg({
        "date": "max",
        "reps": ["count", "mean", "sum"],
        "weight": "mean",
        "rpe": "mean"
    }).round(1)
    
    # Flatten column names
    stats.columns = ["date", "sets", "avg_reps", "total_reps", "avg_weight", "avg_rpe"]
    
    # Calculate total volume (weight × reps × sets)
    stats["total_volume"] = (stats["avg_weight"] * stats["total_reps"]).round(1)
    
    return stats

def get_30_day_overview(df: pd.DataFrame) -> Dict:
    """
    Get overview statistics for the past 30 days.
    
    Args:
        df: DataFrame with workout data
    
    Returns:
        Dictionary with 30-day overview stats
    """
    if len(df) == 0:
        return {}
    
    # Overall stats
    total_workouts = df["workout"].nunique()
    total_exercises = df["exercise"].nunique()
    date_range = (df["date"].min(), df["date"].max())
    
    # Exercise frequency and volume over 30 days
    exercise_stats = df.groupby("exercise").agg({
        "date": "nunique",  # sessions per exercise
        "reps": ["sum", "mean"],
        "weight": "mean"
    }).round(1)
    
    exercise_stats.columns = ["sessions", "total_reps", "avg_reps", "avg_weight"]
    exercise_stats["total_volume"] = (exercise_stats["avg_weight"] * exercise_stats["total_reps"]).round(1)
    
    # Top exercises by frequency and volume
    top_by_frequency = exercise_stats.nlargest(5, "sessions")
    top_by_volume = exercise_stats.nlargest(5, "total_volume")
    
    # Weekly breakdown
    df_with_week = df.copy()
    df_with_week["date"] = pd.to_datetime(df_with_week["date"])
    df_with_week["week"] = df_with_week["date"].dt.isocalendar().week
    weekly_stats = df_with_week.groupby("week").agg({
        "workout": "nunique",
        "reps": "sum",
        "weight": lambda x: (x * df_with_week.loc[x.index, "reps"]).sum()
    }).round(1)
    weekly_stats.columns = ["workouts", "total_reps", "total_volume"]
    
    return {
        "date_range": date_range,
        "total_workouts": total_workouts,
        "total_exercises": total_exercises,
        "exercise_stats": exercise_stats,
        "top_by_frequency": top_by_frequency,
        "top_by_volume": top_by_volume,
        "weekly_stats": weekly_stats
    }

def get_realistic_weight_recommendation(current_weight: float, target_change_pct: float, sets_data: List[Dict]) -> float:
    """
    Calculate a realistic weight recommendation based on typical gym equipment increments.
    
    Args:
        current_weight: Current average weight
        target_change_pct: Desired percentage change (e.g., 0.95 for 5% decrease)
        sets_data: List of set data to infer equipment increments
    
    Returns:
        Realistic weight recommendation rounded to appropriate increment
    """
    # Calculate ideal target weight
    ideal_weight = current_weight * target_change_pct
    
    # Infer equipment increment from actual weights used
    weights_used = [s["weight"] for s in sets_data if s["weight"] > 0]
    
    # Determine increment pattern
    increment = 2.5  # Default assumption for machines
    
    if len(weights_used) >= 2:
        # Look for common increments in the data
        unique_weights = sorted(set(weights_used))
        if len(unique_weights) >= 2:
            diffs = [unique_weights[i+1] - unique_weights[i] for i in range(len(unique_weights)-1)]
            common_increments = [d for d in diffs if d > 0 and d <= 10]  # Reasonable range
            if common_increments:
                increment = min(common_increments)  # Use smallest observed increment
    
    # Round to nearest realistic increment
    if increment >= 2.5:
        # Round to nearest 2.5kg for machines
        realistic_weight = round(ideal_weight / 2.5) * 2.5
    else:
        # Round to nearest 1kg for dumbbells/plates
        realistic_weight = round(ideal_weight)
    
    # Ensure we don't recommend the exact same weight if change is needed
    if abs(realistic_weight - current_weight) < increment * 0.5:
        if target_change_pct < 1.0:  # Decreasing
            realistic_weight = current_weight - increment
        else:  # Increasing
            realistic_weight = current_weight + increment
    
    return max(0, realistic_weight)  # Don't go below 0

def get_last_session_only(df: pd.DataFrame) -> Dict:
    """
    Get detailed breakdown of ONLY the most recent workout session (single date).
    
    Args:
        df: DataFrame with workout data
    
    Returns:
        Dictionary with last session details
    """
    if len(df) == 0:
        return {}
    
    # Find the single most recent workout date
    latest_date = df["date"].max()
    latest_session = df[df["date"] == latest_date]
    
    if len(latest_session) == 0:
        return {}
    
    # Get workout title and date
    workout_info = {
        "date": latest_date,
        "workout_title": latest_session["workout"].iloc[0],
        "total_exercises": latest_session["exercise"].nunique(),
        "total_sets": len(latest_session),
        "exercises": []
    }
    
    # Group by exercise and get set details for this session only
    for exercise, exercise_data in latest_session.groupby("exercise"):
        sets_data = []
        total_volume = 0
        rpe_values = []
        
        for _, row in exercise_data.iterrows():
            set_volume = (row["weight"] * row["reps"]) if row["weight"] > 0 else 0
            total_volume += set_volume
            sets_data.append({
                "weight": row["weight"],
                "reps": row["reps"],
                "rpe": row["rpe"],
                "volume": set_volume
            })
            if row["rpe"] and not pd.isna(row["rpe"]):
                rpe_values.append(row["rpe"])
        
        rep_range = REP_RANGE.get(exercise, None)
        avg_reps = exercise_data["reps"].mean()
        avg_weight = exercise_data["weight"].mean()
        avg_rpe = exercise_data["rpe"].mean()
        
        # Get peak (highest) and final set RPE for better analysis
        peak_rpe = max(rpe_values) if rpe_values else None
        final_rpe = rpe_values[-1] if rpe_values else None
        
        # Check if this is an assisted exercise (weight = assistance, higher = easier)
        is_assisted = is_assisted_exercise(exercise)
        
        # Determine verdict for this session - prioritize RPE over rep ranges
        if rep_range is None or rep_range[0] is None:
            verdict = "❓ no target"
            suggestion = "add rep target to rep_rules.py"
        else:
            # First check RPE if available (RPE takes priority)
            if peak_rpe and not pd.isna(peak_rpe):
                if peak_rpe >= 9.5:
                    verdict = "⬇️ too heavy"
                    if is_assisted:
                        # For assisted exercises: increase assistance to make it easier
                        new_weight = get_realistic_weight_recommendation(avg_weight, 1.05, sets_data)
                        suggestion = f"increase assistance to {new_weight:.1f}kg next time (peak RPE {peak_rpe:.1f} too high)"
                    else:
                        # For regular exercises: decrease load
                        new_weight = get_realistic_weight_recommendation(avg_weight, 0.95, sets_data)
                        suggestion = f"reduce to {new_weight:.1f}kg next time (peak RPE {peak_rpe:.1f} too high)"
                elif peak_rpe <= 7.0:
                    verdict = "⬆️ too light"
                    if is_assisted:
                        # For assisted exercises: decrease assistance to make it harder
                        new_weight = get_realistic_weight_recommendation(avg_weight, 0.95, sets_data)
                        suggestion = f"reduce assistance to {new_weight:.1f}kg next time (peak RPE {peak_rpe:.1f} too low)"
                    else:
                        # For regular exercises: increase load
                        new_weight = get_realistic_weight_recommendation(avg_weight, 1.05, sets_data)
                        suggestion = f"increase to {new_weight:.1f}kg next time (peak RPE {peak_rpe:.1f} too low)"
                elif final_rpe and final_rpe >= 9.0:
                    # Final set at RPE 9+ means good progression to failure
                    verdict = "✅ optimal"
                    suggestion = "perfect intensity - maintain this weight!"
                elif 7.5 <= peak_rpe <= 9.0:
                    verdict = "✅ optimal"
                    suggestion = "perfect intensity - maintain this weight!"
                else:
                    # Fall back to rep-based analysis with RPE adjustment
                    if avg_reps < rep_range[0]:
                        verdict = "⬇️ too heavy"
                        if is_assisted:
                            # For assisted exercises: increase assistance to make it easier
                            new_weight = get_realistic_weight_recommendation(avg_weight, 1.10, sets_data)
                            suggestion = f"increase assistance to {new_weight:.1f}kg next time"
                        else:
                            # For regular exercises: decrease load
                            new_weight = get_realistic_weight_recommendation(avg_weight, 0.90, sets_data)
                            suggestion = f"reduce to {new_weight:.1f}kg next time"
                    elif avg_reps > rep_range[1]:
                        verdict = "⬆️ too light"
                        if is_assisted:
                            # For assisted exercises: decrease assistance to make it harder
                            new_weight = get_realistic_weight_recommendation(avg_weight, 0.95, sets_data)
                            suggestion = f"reduce assistance to {new_weight:.1f}kg next time"
                        else:
                            # For regular exercises: increase load
                            new_weight = get_realistic_weight_recommendation(avg_weight, 1.05, sets_data)
                            suggestion = f"increase to {new_weight:.1f}kg next time"
                    else:
                        verdict = "✅ in range"
                        suggestion = "maintain this weight (good RPE and reps)"
            else:
                # No RPE data, fall back to rep-based analysis only
                if avg_reps < rep_range[0]:
                    verdict = "⬇️ too heavy"
                    if is_assisted:
                        # For assisted exercises: increase assistance to make it easier
                        new_weight = get_realistic_weight_recommendation(avg_weight, 1.10, sets_data)
                        suggestion = f"increase assistance to {new_weight:.1f}kg next time"
                    else:
                        # For regular exercises: decrease load
                        new_weight = get_realistic_weight_recommendation(avg_weight, 0.90, sets_data)
                        suggestion = f"reduce to {new_weight:.1f}kg next time"
                elif avg_reps > rep_range[1]:
                    verdict = "⬆️ too light"
                    if is_assisted:
                        # For assisted exercises: decrease assistance to make it harder
                        new_weight = get_realistic_weight_recommendation(avg_weight, 0.90, sets_data)
                        suggestion = f"reduce assistance to {new_weight:.1f}kg next time"
                    else:
                        # For regular exercises: increase load
                        new_weight = get_realistic_weight_recommendation(avg_weight, 1.05, sets_data)
                        suggestion = f"increase to {new_weight:.1f}kg next time"
                else:
                    verdict = "✅ in range"
                    suggestion = "maintain this weight (no RPE data)"
        
        workout_info["exercises"].append({
            "name": exercise,
            "sets": sets_data,
            "num_sets": len(sets_data),
            "avg_weight": avg_weight,
            "avg_reps": avg_reps,
            "avg_rpe": avg_rpe,
            "peak_rpe": peak_rpe,
            "final_rpe": final_rpe,
            "total_volume": total_volume,
            "verdict": verdict,
            "suggestion": suggestion,
            "target_range": rep_range
        })
    
    # Sort exercises by volume for this session
    workout_info["exercises"].sort(key=lambda x: x["total_volume"], reverse=True)
    
    return workout_info

def print_comprehensive_report(df: pd.DataFrame):
    """
    Print a comprehensive report with clear separation of 30-day trends and last session.
    
    Args:
        df: Full workout DataFrame
    """
    print("\n" + "="*80)
    print("🏋️‍♂️  HEVY COMPREHENSIVE COACHING REPORT")
    print("="*80)
    
    if len(df) == 0:
        print("❌ No workout data found for analysis")
        return
    
    # Initialize AI coach
    ai_coach = AICoach()
    
    # Calculate all the new metrics
    progression_data = get_exercise_progression(df)
    last_session = get_last_session_only(df)
    session_quality = calculate_session_quality(last_session, progression_data)
    periodization = detect_plateaus_and_periodization(progression_data)
    volume_recovery = get_volume_recovery_insights(df)
    exercise_evolution = analyze_exercise_evolution(df)
    comprehensive_trends = get_comprehensive_trends(df)
    
    # Get cyclical routine information for AI context
    next_workout_info = {}
    if api_key := os.getenv("HEVY_API_KEY"):
        workout_cycle = WorkoutCycle(api_key)
        if workout_cycle.is_available():
            # Use unfiltered data for cycle detection (includes treadmill/cardio for rest day detection)
            df_with_cardio = filter_recent_data(events_to_df("hevy_events.json"), 90)
            next_workout_info = workout_cycle.get_next_workout_info(df_with_cardio)
    
    # 🚀 QUICK SUMMARY - Mobile-friendly, action-focused
    print("\n" + "🚀 QUICK SUMMARY".center(80))
    print("=" * 80)
    
    if last_session:
        session_date = last_session.get("date", "Unknown")
        print(f"📅 **Latest Session**: {session_date}")
        print(f"📊 **Grade**: {session_quality['grade']} ({session_quality['overall_score']:.0f}/100)")
        print(f"📈 **Progress**: {session_quality['progressed']} improved, {session_quality['smart_adjustments']} smart adjustments")
        
        # AI-Powered Personalized Insights
        if ai_coach.is_available():
            print(f"\n🤖 **AI COACH INSIGHTS**:")
            ai_summary = ai_coach.generate_session_summary(
                session_quality, last_session, comprehensive_trends
            )
            if ai_summary:
                print(f"   {ai_summary}")
            
            ai_focus = ai_coach.generate_next_session_focus(last_session, progression_data)
            if ai_focus:
                print(f"\n🎯 **Next Session Focus**:")
                print(f"   {ai_focus}")
        
        # Quick action items (top 3 priority)
        priority_actions = []
        if last_session.get("exercises"):
            for ex in sorted(last_session["exercises"], 
                           key=lambda x: abs((x.get("peak_rpe") or 8.0) - 8.5), reverse=True)[:3]:
                if ex["verdict"] in ["⬇️ too heavy", "⬆️ too light"]:
                    action = f"{ex['name']}: {ex['verdict']}"
                    if ex.get("suggestion"):
                        action += f" → {ex['suggestion']}"
                    priority_actions.append(action)
        
        if priority_actions:
            print(f"\n⚡ **Priority Actions**:")
            for i, action in enumerate(priority_actions, 1):
                print(f"   {i}. {action}")
        
        # Overall trajectory
        fitness_trend = comprehensive_trends.get("fitness_trajectory", "Stable")
        avg_progression = comprehensive_trends.get("avg_progression_rate", 0)
        print(f"\n📊 **Overall Progress**: {fitness_trend} ({avg_progression:+.1f}kg/week avg)")
    
    print("\n" + "="*80)
    
    # ⭐ SESSION QUALITY ASSESSMENT
    print("\n⭐ **SESSION QUALITY ASSESSMENT**")
    print("-" * 50)
    
    if session_quality:
        print(f"🎯 **Overall Grade**: {session_quality['grade']} ({session_quality['overall_score']:.0f}/100)")
        print(f"📝 **Assessment**: {session_quality['description']}")
        print(f"💪 **Progression**: {session_quality['progressed']} progressed, {session_quality['maintained']} maintained, {session_quality['smart_adjustments']} smart adjustments, {session_quality['regressed']} regressed")
        print(f"🔥 **Intensity Score**: {session_quality['avg_rpe_score']:.0f}/100 (RPE balance)")
        print(f"📈 **Progress Score**: {session_quality['avg_progression_score']:.0f}/100 (weight progression)")
    else:
        print("❌ No recent session data available for assessment")
    
    # 📈 EXERCISE PROGRESSION ANALYSIS
    print(f"\n📈 **EXERCISE PROGRESSION ANALYSIS**")
    print("-" * 50)
    
    if progression_data:
        for exercise, data in list(progression_data.items())[:8]:  # Show top 8 exercises
            sessions = data["sessions"]
            if len(sessions) >= 2:
                current = sessions[0]
                previous = sessions[1]
                
                # Show progression with trend
                trend_emoji = "📈" if data["weight_change"] > 0 else "📉" if data["weight_change"] < 0 else "➡️"
                
                print(f"**{exercise}**")
                print(f"   Sessions: {current['avg_weight']:.1f}kg×{current['avg_reps']:.1f} (today) → {previous['avg_weight']:.1f}kg×{previous['avg_reps']:.1f} ({previous['session_ago']}d ago)")
                print(f"   Trend: {trend_emoji} {data['weight_change']:+.1f}kg ({data['weight_change_pct']:+.1f}%)")
                
                if len(sessions) >= 3:
                    print(f"   Overall: {data['trend_change_pct']:+.1f}% over {data['sessions_count']} sessions")
                
                if data["is_stagnant"]:
                    print(f"   ⚠️ Stagnant for {data['sessions_count']} sessions - consider deload")
                print()
        
        # Add AI Exercise Insights
        if ai_coach.is_available() and last_session and last_session.get("exercises"):
            exercise_insights = ai_coach.generate_exercise_insights(last_session["exercises"], progression_data)
            if exercise_insights:
                print(f"🤖 **AI EXERCISE INSIGHTS**:")
                for exercise, insight in exercise_insights.items():
                    print(f"   • **{exercise}**: {insight}")
                print()
    else:
        print("❌ Insufficient data for exercise progression analysis")
    
    # 🎯 TRAINING PERIODIZATION INSIGHTS
    print(f"\n🎯 **TRAINING PERIODIZATION INSIGHTS**")
    print("-" * 50)
    
    if periodization:
        print(f"📊 **Program Status**: {periodization['program_status']}")
        print(f"💡 **Recommendation**: {periodization['program_suggestion']}")
        print(f"📈 **Plateau Rate**: {periodization['plateau_percentage']:.0f}% of exercises")
        
        # Add AI Trend Analysis
        if ai_coach.is_available():
            ai_trend_analysis = ai_coach.generate_trend_analysis(comprehensive_trends, periodization)
            if ai_trend_analysis:
                print(f"\n🤖 **AI TREND ANALYSIS**:")
                print(f"   {ai_trend_analysis}")
        
        if periodization["progressing_exercises"]:
            print(f"\n✅ **Progressing Exercises** ({len(periodization['progressing_exercises'])}):")
            for ex in periodization["progressing_exercises"][:5]:
                print(f"   • {ex['name']}: +{ex['progress_pct']:.1f}%")
        
        if periodization["smart_adjustments"]:
            print(f"\n✅ **Smart Adjustments** ({len(periodization['smart_adjustments'])}):")
            for ex in periodization["smart_adjustments"][:3]:
                print(f"   • {ex['name']}: {ex['justification']}")
        
        if periodization["plateaued_exercises"]:
            print(f"\n⚠️ **Plateaued Exercises** ({len(periodization['plateaued_exercises'])}):")
            for ex in periodization["plateaued_exercises"][:5]:
                print(f"   • {ex['name']}: {ex['sessions_stagnant']} sessions")
        
        if periodization["deload_candidates"]:
            print(f"\n🔄 **Deload Candidates**: {', '.join(periodization['deload_candidates'][:3])}")
    
    # 🔄 CYCLICAL ROUTINE TRACKING
    if api_key := os.getenv("HEVY_API_KEY"):
        workout_cycle = WorkoutCycle(api_key)
        if workout_cycle.is_available():
            print(f"\n🔄 **CYCLICAL ROUTINE TRACKING**")
            print("-" * 50)
            
            if next_workout_info and "error" not in next_workout_info:
                print(f"📅 **Next Workout**: {next_workout_info['workout_name']}")
                print(f"🔢 **Cycle Position**: Day {next_workout_info['cycle_day_index'] + 1}")
                print(f"📊 **Days Until Repeat**: {next_workout_info['days_until_same_workout']}")
                
                if not next_workout_info["is_rest_day"]:
                    recommendations = workout_cycle.get_routine_specific_recommendations(df, next_workout_info)
                    if recommendations["type"] == "workout_specific":
                        exercise_recs = recommendations["exercise_recommendations"]
                        if exercise_recs:
                            print(f"⏰ **Cycle Info**: This workout repeats every {next_workout_info['days_until_same_workout']} days")
                            print(f"\n🎯 **Exercise-Specific Recommendations for {next_workout_info['workout_name']}**:")
                            
                            # Categorize recommendations
                            increases = []
                            decreases = []
                            maintains = []
                            
                            for exercise, rec in exercise_recs.items():
                                if rec["action"] == "increase":
                                    increases.append((exercise, rec))
                                elif rec["action"] == "decrease":
                                    decreases.append((exercise, rec))
                                else:
                                    maintains.append((exercise, rec))
                            
                            # Show increases
                            if increases:
                                print(f"\n📈 **Suggested Increases**:")
                                for exercise, rec in increases:
                                    print(f"   • **{exercise}**: {rec['current_weight']:.1f}kg → {rec['suggested_weight']:.1f}kg ({rec['reasoning']})")
                            
                            # Show decreases  
                            if decreases:
                                print(f"\n📉 **Suggested Decreases**:")
                                for exercise, rec in decreases:
                                    print(f"   • **{exercise}**: {rec['current_weight']:.1f}kg → {rec['suggested_weight']:.1f}kg ({rec['reasoning']})")
                            
                            # Show maintains
                            if maintains:
                                print(f"\n✅ **Maintain Current Weights**:")
                                for exercise, rec in maintains:
                                    print(f"   • **{exercise}**: Keep {rec['current_weight']:.1f}kg ({rec['reasoning']})")
                            
                            # Show general recommendations
                            if recommendations.get("general_recommendations"):
                                print(f"\n💡 **General Recommendations**:")
                                for rec in recommendations["general_recommendations"]:
                                    print(f"   • {rec}")
                        
                        # Add AI insights as supplement to structured recommendations
                        if ai_coach.is_available():
                            ai_next_day = ai_coach.generate_next_day_overview(
                                last_session, next_workout_info, comprehensive_trends, volume_recovery
                            )
                            if ai_next_day:
                                print(f"\n🤖 **AI WORKOUT STRATEGY**:")
                                print(f"   {ai_next_day}")
                else:
                    print(f"😴 **Rest Day** - Focus on recovery!")
                    # Add AI recovery insights for rest days
                    if ai_coach.is_available():
                        ai_recovery = ai_coach.generate_recovery_insights(volume_recovery, comprehensive_trends)
                        if ai_recovery:
                            print(f"\n🤖 **AI RECOVERY STRATEGY**:")
                            print(f"   {ai_recovery}")
            else:
                print("💡 Configure your routine cycle for personalized next-workout recommendations")
        else:
            print(f"\n💡 **Cyclical Routine Tracking Available**")
            print("-" * 50)
            print("📝 Copy routine_config.example.py to routine_config.py to enable:")
            print("   • Next workout predictions based on your cycle")
            print("   • Exercise-specific weight recommendations")
            print("   • Integration with your Hevy routine templates")
    
    # 📊 VOLUME & RECOVERY ANALYSIS
    print(f"\n📊 **VOLUME & RECOVERY ANALYSIS**")
    print("-" * 50)
    
    if volume_recovery:
        print(f"📈 **Volume Trend**: {volume_recovery['volume_trend']} ({volume_recovery['volume_change_pct']:+.1f}%)")
        print(f"😴 **Recovery Status**: {volume_recovery['recovery_status']}")
        print(f"📅 **Days Since Last**: {volume_recovery['days_since_last']} days")
        print(f"⚡ **Training Frequency**: {volume_recovery['avg_rest_days']:.1f} days between sessions")
        
        # Add AI Recovery Insights
        if ai_coach.is_available():
            ai_recovery = ai_coach.generate_recovery_insights(volume_recovery, comprehensive_trends)
            if ai_recovery:
                print(f"\n🤖 **AI RECOVERY INSIGHTS**:")
                print(f"   {ai_recovery}")
        
        if volume_recovery["muscle_volume"]:
            print(f"\n💪 **Muscle Group Volume** (last period):")
            sorted_muscle_volume = sorted(volume_recovery["muscle_volume"].items(), 
                                        key=lambda x: x[1], reverse=True)
            for muscle, volume in sorted_muscle_volume[:5]:
                print(f"   • {muscle.title()}: {volume:,.0f}kg")
    
    # 🏆 PEAK PERFORMANCE ANALYSIS
    print(f"\n🏆 **PEAK PERFORMANCE ANALYSIS**")
    print("-" * 50)
    
    exercise_peaks = comprehensive_trends.get("exercise_peaks", {})
    if exercise_peaks:
        for exercise, peak_data in list(exercise_peaks.items())[:8]:
            print(f"**{exercise}**")
            print(f"   {peak_data['peak_status']}: {peak_data['peak_assessment']}")
            if peak_data.get("peak_rpe"):
                print(f"   Peak RPE: {peak_data['peak_rpe']:.1f}")
            print()
    
    # 📈 COMPREHENSIVE FITNESS TRENDS  
    print(f"\n📈 **COMPREHENSIVE FITNESS TRENDS**")
    print("-" * 50)
    
    if comprehensive_trends:
        print(f"🎯 **Overall Trajectory**: {comprehensive_trends['fitness_trajectory']}")
        print(f"📝 **Description**: {comprehensive_trends['trajectory_desc']}")
        print(f"⚡ **Average Progression**: {comprehensive_trends['avg_progression_rate']:+.1f}kg/week")
        print(f"📊 **Training Frequency**: {comprehensive_trends['training_frequency']:.1f} sessions/week")
        print(f"📅 **Analysis Period**: {comprehensive_trends['total_days']} days, {comprehensive_trends['total_sessions']} sessions")
        
        # Exercise trends summary
        exercise_trends = comprehensive_trends.get("exercise_trends", {})
        if exercise_trends:
            growth_categories = {}
            for exercise, data in exercise_trends.items():
                status = data["growth_status"]
                if status not in growth_categories:
                    growth_categories[status] = []
                growth_categories[status].append(exercise)
            
            print(f"\n📊 **Exercise Growth Summary**:")
            for status, exercises in growth_categories.items():
                print(f"   {status}: {len(exercises)} exercises")
                if len(exercises) <= 3:
                    print(f"      ({', '.join(exercises)})")
    
    # 📋 DECISION QUALITY EVOLUTION
    print(f"\n📋 **DECISION QUALITY EVOLUTION**")
    print("-" * 50)
    
    if exercise_evolution:
        total_decisions = sum(data["total_decisions"] for data in exercise_evolution.values())
        total_good = sum(len(data["good_decisions"]) for data in exercise_evolution.values())
        total_missed = sum(len(data["missed_opportunities"]) for data in exercise_evolution.values())
        
        if total_decisions > 0:
            overall_efficiency = (total_good / total_decisions) * 100
            print(f"🎯 **Overall Decision Efficiency**: {overall_efficiency:.0f}% ({total_good}/{total_decisions})")
            print(f"✅ **Good Decisions**: {total_good}")
            print(f"❌ **Missed Opportunities**: {total_missed}")
            
            # Show exercises with most missed opportunities (learning focus)
            missed_by_exercise = [(exercise, len(data["missed_opportunities"])) 
                                for exercise, data in exercise_evolution.items()]
            missed_by_exercise.sort(key=lambda x: x[1], reverse=True)
            
            if missed_by_exercise and missed_by_exercise[0][1] > 0:
                print(f"\n📚 **Learning Focus** (most missed opportunities):")
                for exercise, missed_count in missed_by_exercise[:3]:
                    if missed_count > 0:
                        efficiency = exercise_evolution[exercise]["efficiency_score"]
                        print(f"   • **{exercise}**: {missed_count} missed, {efficiency:.0f}% efficiency")
                        
                        # Show recent missed opportunity
                        if exercise_evolution[exercise]["missed_opportunities"]:
                            recent_miss = exercise_evolution[exercise]["missed_opportunities"][0]
                            print(f"     Recent: {recent_miss['missed_opportunity']}")
        else:
            print("📊 Insufficient session history for decision quality analysis")
    

    
    print("\n" + "="*80)

def export_recent_workouts(df: pd.DataFrame, days: int = 30) -> str:
    """
    Export recent workouts to a clean, readable CSV format.
    
    Args:
        df: DataFrame with workout data
        days: Number of recent days to export (default: 30)
    
    Returns:
        Filename of the exported CSV file
    """
    if len(df) == 0:
        print("❌ No workout data to export")
        return ""
    
    # Filter to recent data
    df_recent = filter_recent_data(df, days=days)
    
    if len(df_recent) == 0:
        print(f"❌ No workout data found in the last {days} days")
        return ""
    
    # Create export-friendly DataFrame
    export_df = df_recent.copy()
    export_df["date"] = pd.to_datetime(export_df["date"]).dt.strftime("%Y-%m-%d")
    
    # Calculate additional useful columns
    export_df["volume"] = export_df["weight"] * export_df["reps"]
    export_df["weight_kg"] = export_df["weight"]  # Explicit unit clarity
    
    # Reorder and rename columns for clarity
    export_columns = {
        "date": "Date",
        "workout": "Workout_Name", 
        "exercise": "Exercise",
        "weight_kg": "Weight_kg",
        "reps": "Reps",
        "rpe": "RPE",
        "volume": "Volume_kg",
        "exercise_notes": "Exercise_Notes"
    }
    
    # Select and rename columns
    export_df = export_df[list(export_columns.keys())].rename(columns=export_columns)
    
    # Sort by date and exercise for readability
    export_df = export_df.sort_values(["Date", "Exercise", "Weight_kg"])
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"hevy_workouts_export_{timestamp}.csv"
    
    # Export to CSV
    export_df.to_csv(filename, index=False)
    
    # Print summary
    total_sets = len(export_df)
    total_workouts = export_df["Date"].nunique()
    total_exercises = export_df["Exercise"].nunique()
    date_range = (export_df["Date"].min(), export_df["Date"].max())
    total_volume = export_df["Volume_kg"].sum()
    
    print(f"\n📊 **WORKOUT DATA EXPORT**")
    print(f"✅ Exported to: {filename}")
    print(f"📅 Date Range: {date_range[0]} to {date_range[1]}")
    print(f"🏃 Total Workouts: {total_workouts}")
    print(f"💪 Total Exercises: {total_exercises}")
    print(f"📋 Total Sets: {total_sets}")
    print(f"🏋️ Total Volume: {total_volume:,.0f}kg")
    
    # Show sample of data
    print(f"\n📄 **Sample Data Preview**:")
    sample_df = export_df.head(8)
    print(sample_df.to_string(index=False, max_colwidth=15))
    
    if len(export_df) > 8:
        print(f"... and {len(export_df) - 8} more rows")
    
    return filename

def save_report_to_markdown(df: pd.DataFrame) -> str:
    """
    Save the comprehensive report to a markdown file.
    
    Args:
        df: Full workout DataFrame
    
    Returns:
        Filename of the saved markdown file
    """
    import io
    from contextlib import redirect_stdout
    
    # Capture the report output
    markdown_content = io.StringIO()
    with redirect_stdout(markdown_content):
        print_comprehensive_report(df)
    
    # Save to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"hevy_coaching_report_{timestamp}.md"
    
    with open(filename, 'w') as f:
        f.write(markdown_content.getvalue())
    
    return filename

def get_exercise_progression(df: pd.DataFrame) -> Dict:
    """
    Track exercise progression over the last 3-4 sessions for each exercise.
    
    Args:
        df: DataFrame with workout data
    
    Returns:
        Dictionary with progression data for each exercise
    """
    if len(df) == 0:
        return {}
    
    progression_data = {}
    
    for exercise in df["exercise"].unique():
        exercise_df = df[df["exercise"] == exercise].copy()
        
        # Get unique session dates for this exercise
        session_dates = sorted(exercise_df["date"].unique(), reverse=True)
        
        if len(session_dates) < 2:
            continue  # Need at least 2 sessions to track progression
        
        sessions = []
        for i, date in enumerate(session_dates[:4]):  # Last 4 sessions max
            session_data = exercise_df[exercise_df["date"] == date]
            
            avg_weight = session_data["weight"].mean()
            avg_reps = session_data["reps"].mean()
            avg_rpe = session_data["rpe"].mean()
            total_volume = (session_data["weight"] * session_data["reps"]).sum()
            
            sessions.append({
                "date": date,
                "session_ago": i,
                "avg_weight": avg_weight,
                "avg_reps": avg_reps,
                "avg_rpe": avg_rpe,
                "total_volume": total_volume,
                "sets": len(session_data)
            })
        
        # Calculate progression metrics
        if len(sessions) >= 2:
            latest = sessions[0]
            previous = sessions[1]
            
            weight_change = latest["avg_weight"] - previous["avg_weight"]
            weight_change_pct = (weight_change / previous["avg_weight"]) * 100 if previous["avg_weight"] > 0 else 0
            volume_change = latest["total_volume"] - previous["total_volume"]
            volume_change_pct = (volume_change / previous["total_volume"]) * 100 if previous["total_volume"] > 0 else 0
            
            # Detect stagnation (same weight for 3+ sessions)
            weights = [s["avg_weight"] for s in sessions[:3]]
            is_stagnant = len(set(weights)) == 1 and len(weights) >= 3
            
            # Progression trend over all sessions
            if len(sessions) >= 3:
                first_weight = sessions[-1]["avg_weight"]
                trend_change = latest["avg_weight"] - first_weight
                trend_change_pct = (trend_change / first_weight) * 100 if first_weight > 0 else 0
            else:
                trend_change = weight_change
                trend_change_pct = weight_change_pct
            
            progression_data[exercise] = {
                "sessions": sessions,
                "weight_change": weight_change,
                "weight_change_pct": weight_change_pct,
                "volume_change": volume_change,
                "volume_change_pct": volume_change_pct,
                "trend_change_pct": trend_change_pct,
                "is_stagnant": is_stagnant,
                "sessions_count": len(sessions)
            }
    
    return progression_data

def calculate_session_quality(last_session: Dict, progression_data: Dict) -> Dict:
    """
    Calculate a quality score for the most recent session.
    
    Args:
        last_session: Last session data from get_last_session_only()
        progression_data: Exercise progression data
    
    Returns:
        Dictionary with session quality metrics
    """
    if not last_session or not last_session.get("exercises"):
        return {}
    
    total_exercises = len(last_session["exercises"])
    
    # Count exercises by status with RPE-aware categorization
    progressed = 0          # Weight increased appropriately
    maintained = 0          # Maintained weight with good RPE
    smart_adjustments = 0   # Strategic weight reductions based on RPE
    regressed = 0          # Actual performance decline
    
    rpe_scores = []
    progression_scores = []
    
    for exercise in last_session["exercises"]:
        exercise_name = exercise["name"]
        
        # RPE quality using peak RPE (7.5-9.0 is ideal range)
        peak_rpe = exercise.get("peak_rpe")
        final_rpe = exercise.get("final_rpe")
        
        if peak_rpe and not pd.isna(peak_rpe):
            if 7.5 <= peak_rpe <= 9.0:
                rpe_score = 100  # Perfect RPE range
            elif final_rpe and final_rpe >= 9.0 and peak_rpe <= 9.5:
                rpe_score = 95   # Good progression to failure
            elif 7.0 <= peak_rpe < 7.5:
                rpe_score = 80   # Slightly too easy
            elif 9.0 < peak_rpe <= 9.5:
                rpe_score = 85   # Slightly too hard but acceptable
            elif 6.5 <= peak_rpe < 7.0:
                rpe_score = 65   # Too easy
            elif 9.5 < peak_rpe <= 10:
                rpe_score = 60   # Too hard
            else:
                rpe_score = 40   # Way off
            rpe_scores.append(rpe_score)
        
        # Enhanced progression quality assessment with RPE context
        if exercise_name in progression_data:
            prog_data = progression_data[exercise_name]
            
            # Get previous session's RPE if available
            previous_rpe = None
            if len(prog_data["sessions"]) >= 2:
                previous_session = prog_data["sessions"][1]  # Previous session (sessions[0] is current)
                previous_rpe = previous_session.get("avg_rpe")
            
            if prog_data["weight_change"] > 0:
                # Weight increased
                progressed += 1
                if previous_rpe and previous_rpe <= 7.5:
                    progression_scores.append(100)  # Good increase from low RPE
                else:
                    progression_scores.append(90)   # Increase but unsure about RPE context
            elif prog_data["weight_change"] == 0:
                # Weight maintained
                if prog_data["is_stagnant"]:
                    progression_scores.append(60)  # Stagnant
                else:
                    maintained += 1
                    progression_scores.append(80)  # Maintained appropriately
            else:
                # Weight decreased - assess if it was smart or a regression
                if previous_rpe and previous_rpe >= 9.5:
                    # Strategic weight reduction from high RPE
                    smart_adjustments += 1
                    progression_scores.append(85)  # Smart adjustment
                elif previous_rpe and previous_rpe >= 9.0:
                    # Reasonable weight reduction from challenging RPE
                    smart_adjustments += 1
                    progression_scores.append(75)  # Reasonable adjustment
                else:
                    # Weight decrease without clear high RPE justification
                    regressed += 1
                    progression_scores.append(45)  # Actual regression
        else:
            progression_scores.append(70)  # No data, neutral
    
    # Calculate overall scores
    avg_rpe_score = sum(rpe_scores) / len(rpe_scores) if rpe_scores else 70
    avg_progression_score = sum(progression_scores) / len(progression_scores) if progression_scores else 70
    
    # Weighted overall score
    overall_score = (avg_rpe_score * 0.4) + (avg_progression_score * 0.6)
    
    # Determine grade with enhanced descriptions
    if overall_score >= 90:
        grade = "A+"
        description = "Excellent session! Great progression and intensity balance."
    elif overall_score >= 85:
        grade = "A"
        description = "Great session with solid progression."
    elif overall_score >= 80:
        grade = "B+"
        description = "Good session, minor room for improvement."
    elif overall_score >= 75:
        grade = "B"
        description = "Decent session, consider adjusting intensity."
    elif overall_score >= 70:
        grade = "C+"
        description = "Average session, focus on progression."
    elif overall_score >= 65:
        grade = "C"
        description = "Below average, review your training approach."
    else:
        grade = "D"
        description = "Poor session, consider deload or technique focus."
    
    return {
        "overall_score": overall_score,
        "grade": grade,
        "description": description,
        "avg_rpe_score": avg_rpe_score,
        "avg_progression_score": avg_progression_score,
        "progressed": progressed,
        "maintained": maintained,
        "smart_adjustments": smart_adjustments,
        "regressed": regressed,
        "total_exercises": total_exercises
    }

def detect_plateaus_and_periodization(progression_data: Dict) -> Dict:
    """
    Detect plateaus and provide periodization suggestions with RPE context.
    
    Args:
        progression_data: Exercise progression data
    
    Returns:
        Dictionary with periodization insights and suggestions
    """
    plateaued_exercises = []
    progressing_exercises = []
    regressing_exercises = []
    smart_adjustments = []  # New category for RPE-justified decreases
    deload_candidates = []
    
    total_exercises = len(progression_data)
    
    for exercise, data in progression_data.items():
        if data["is_stagnant"]:
            plateaued_exercises.append({
                "name": exercise,
                "sessions_stagnant": data["sessions_count"]
            })
            
            # If stagnant for 3+ sessions, consider deload
            if data["sessions_count"] >= 3:
                deload_candidates.append(exercise)
        
        elif data["trend_change_pct"] > 2:  # Growing >2% over period
            progressing_exercises.append({
                "name": exercise,
                "progress_pct": data["trend_change_pct"]
            })
        
        elif data["trend_change_pct"] < -2:  # Declining >2%
            # Check if this decline was RPE-justified (smart adjustment)
            sessions = data["sessions"]
            
            # Look for high RPE sessions that might justify the weight decrease
            high_rpe_detected = False
            if len(sessions) >= 2:
                # Check if any recent session had high RPE (>=9.5)
                for session in sessions[:3]:  # Check last 3 sessions
                    session_rpe = session.get("avg_rpe")
                    if session_rpe and session_rpe >= 9.5:
                        high_rpe_detected = True
                        break
                
                # Also check if there was a concerning RPE trend
                rpe_values = []
                for session in sessions[:3]:
                    if session.get("avg_rpe") and not pd.isna(session.get("avg_rpe")):
                        rpe_values.append(session["avg_rpe"])
                
                # If average RPE over recent sessions was >9.0, justify the decrease
                if rpe_values and sum(rpe_values) / len(rpe_values) >= 9.0:
                    high_rpe_detected = True
            
            if high_rpe_detected:
                smart_adjustments.append({
                    "name": exercise,
                    "decline_pct": data["trend_change_pct"],
                    "justification": "RPE-based smart adjustment"
                })
            else:
                regressing_exercises.append({
                    "name": exercise,
                    "decline_pct": data["trend_change_pct"]
                })
    
    # Overall program assessment - consider smart adjustments as positive
    effective_progressing = len(progressing_exercises) + len(smart_adjustments)
    plateau_pct = (len(plateaued_exercises) / total_exercises) * 100 if total_exercises > 0 else 0
    
    if plateau_pct > 50:
        program_status = "🚨 Major Plateau"
        program_suggestion = "Consider a deload week or program change"
    elif plateau_pct > 30:
        program_status = "⚠️ Moderate Plateau"
        program_suggestion = "Review programming and consider technique focus"
    elif effective_progressing > len(plateaued_exercises) + len(regressing_exercises):
        program_status = "📈 Progressing Well"
        program_suggestion = "Keep current program, great momentum!"
    else:
        program_status = "🔄 Mixed Progress"
        program_suggestion = "Fine-tune weights and recovery"
    
    return {
        "plateaued_exercises": plateaued_exercises,
        "progressing_exercises": progressing_exercises,
        "regressing_exercises": regressing_exercises,
        "smart_adjustments": smart_adjustments,  # New category
        "deload_candidates": deload_candidates,
        "plateau_percentage": plateau_pct,
        "program_status": program_status,
        "program_suggestion": program_suggestion,
        "total_exercises": total_exercises
    }

def get_volume_recovery_insights(df: pd.DataFrame) -> Dict:
    """
    Analyze volume trends and recovery indicators.
    
    Args:
        df: DataFrame with workout data
    
    Returns:
        Dictionary with volume and recovery insights
    """
    if len(df) == 0:
        return {}
    
    df_copy = df.copy()
    df_copy["date"] = pd.to_datetime(df_copy["date"])
    df_copy["week"] = df_copy["date"].dt.isocalendar().week
    df_copy["volume"] = df_copy["weight"] * df_copy["reps"]
    
    # Weekly volume analysis
    weekly_volume = df_copy.groupby("week")["volume"].sum().sort_index()
    weeks = list(weekly_volume.index)
    
    volume_trend = "stable"
    volume_change_pct = 0
    
    if len(weeks) >= 2:
        current_week = weekly_volume.iloc[-1]
        previous_week = weekly_volume.iloc[-2]
        volume_change_pct = ((current_week - previous_week) / previous_week) * 100 if previous_week > 0 else 0
        
        if volume_change_pct > 10:
            volume_trend = "increasing rapidly"
        elif volume_change_pct > 5:
            volume_trend = "increasing moderately"
        elif volume_change_pct < -10:
            volume_trend = "decreasing rapidly"
        elif volume_change_pct < -5:
            volume_trend = "decreasing moderately"
    
    # Recovery analysis
    workout_dates = sorted(df_copy["date"].dt.date.unique())
    
    if len(workout_dates) >= 2:
        last_workout = workout_dates[-1]
        previous_workout = workout_dates[-2]
        days_since_last = (datetime.now().date() - last_workout).days
        rest_between_last = (last_workout - previous_workout).days
        
        # Average rest between workouts
        if len(workout_dates) >= 3:
            rest_periods = []
            for i in range(1, len(workout_dates)):
                rest_periods.append((workout_dates[i] - workout_dates[i-1]).days)
            avg_rest = sum(rest_periods) / len(rest_periods)
        else:
            avg_rest = rest_between_last
        
        # Recovery status
        if days_since_last <= 1:
            recovery_status = "🔥 High frequency"
        elif days_since_last <= 2:
            recovery_status = "⚡ Good frequency"
        elif days_since_last <= 4:
            recovery_status = "✅ Optimal recovery"
        elif days_since_last <= 7:
            recovery_status = "😴 Extended rest"
        else:
            recovery_status = "🚨 Long break"
    else:
        days_since_last = 0
        rest_between_last = 0
        avg_rest = 0
        recovery_status = "📊 Insufficient data"
    
    # Body part volume breakdown
    muscle_groups = {
        "legs": ["leg press", "squat", "leg extension", "leg curl", "calf", "bulgarian"],
        "chest": ["bench", "chest", "push-up", "dip"],
        "back": ["row", "pull", "lat", "deadlift"],
        "shoulders": ["shoulder", "press", "raise", "shrug"],
        "arms": ["curl", "tricep", "bicep"]
    }
    
    muscle_volume = {}
    for muscle, keywords in muscle_groups.items():
        muscle_df = df_copy[df_copy["exercise"].str.lower().str.contains("|".join(keywords), na=False)]
        if len(muscle_df) > 0:
            muscle_volume[muscle] = muscle_df["volume"].sum()
    
    return {
        "weekly_volume": weekly_volume,
        "volume_trend": volume_trend,
        "volume_change_pct": volume_change_pct,
        "days_since_last": days_since_last,
        "rest_between_last": rest_between_last,
        "avg_rest_days": avg_rest,
        "recovery_status": recovery_status,
        "muscle_volume": muscle_volume,
        "total_weekly_workouts": len(workout_dates)
    }

def analyze_exercise_evolution(df: pd.DataFrame) -> Dict:
    """
    Analyze the evolution of each exercise over multiple sessions, 
    providing recommendations for past sessions and identifying missed opportunities.
    
    Args:
        df: DataFrame with workout data
    
    Returns:
        Dictionary with exercise evolution analysis
    """
    if len(df) == 0:
        return {}
    
    # Get the absolute latest date across all exercises for reference
    absolute_latest_date = df["date"].max()
    
    evolution_data = {}
    
    for exercise in df["exercise"].unique():
        exercise_df = df[df["exercise"] == exercise].copy()
        
        # Get unique session dates for this exercise
        session_dates = sorted(exercise_df["date"].unique(), reverse=True)
        
        if len(session_dates) < 3:  # Need at least 3 sessions for meaningful evolution analysis
            continue
        
        sessions_analysis = []
        
        for i, date in enumerate(session_dates[:5]):  # Analyze last 5 sessions max
            session_data = exercise_df[exercise_df["date"] == date]
            
            avg_weight = session_data["weight"].mean()
            avg_reps = session_data["reps"].mean()
            avg_rpe = session_data["rpe"].mean()
            total_volume = (session_data["weight"] * session_data["reps"]).sum()
            
            # Get RPE values for this session
            rpe_values = [rpe for rpe in session_data["rpe"].values if rpe and not pd.isna(rpe)]
            peak_rpe = max(rpe_values) if rpe_values else None
            final_rpe = rpe_values[-1] if rpe_values else None
            
            # Determine the current session's performance verdict using RPE-focused logic
            rep_range = REP_RANGE.get(exercise, None)
            
            if rep_range is None or rep_range[0] is None:
                verdict = "❓ no target"
            else:
                # Prioritize RPE analysis
                if peak_rpe and not pd.isna(peak_rpe):
                    if peak_rpe >= 9.5:
                        verdict = "⬇️ too heavy (RPE)"
                    elif peak_rpe <= 7.0:
                        verdict = "⬆️ too light (RPE)"
                    elif final_rpe and final_rpe >= 9.0:
                        # Final set at RPE 9+ means good progression to failure
                        verdict = "✅ optimal"
                    elif 7.5 <= peak_rpe <= 9.0:
                        verdict = "✅ optimal"
                    else:
                        # Fall back to rep analysis with RPE context
                        if avg_reps < rep_range[0]:
                            verdict = "⬇️ too heavy"
                        elif avg_reps > rep_range[1]:
                            verdict = "⬆️ too light"
                        else:
                            verdict = "✅ in range"
                else:
                    # No RPE data, use rep-based analysis
                    if avg_reps < rep_range[0]:
                        verdict = "⬇️ too heavy"
                    elif avg_reps > rep_range[1]:
                        verdict = "⬆️ too light"
                    else:
                        verdict = "✅ in range"
            
            sessions_analysis.append({
                "date": date,
                "session_ago": i,
                "avg_weight": avg_weight,
                "avg_reps": avg_reps,
                "avg_rpe": avg_rpe,
                "peak_rpe": peak_rpe,
                "final_rpe": final_rpe,
                "total_volume": total_volume,
                "sets": len(session_data),
                "verdict": verdict
            })
        
        # Analyze decision quality: what actually happened vs what should have happened
        missed_opportunities = []
        good_decisions = []
        
        for i in range(len(sessions_analysis) - 1):
            current = sessions_analysis[i]
            previous = sessions_analysis[i + 1]
            
            weight_change = current["avg_weight"] - previous["avg_weight"]
            
            # What actually happened
            if weight_change > 0.5:
                actual_action = "increased"
            elif weight_change < -0.5:
                actual_action = "decreased"
            else:
                actual_action = "maintained"
            
            # What should have happened based on previous session's verdict
            if previous["verdict"] in ["⬇️ too heavy", "⬇️ too heavy (RPE)"]:
                optimal_action = "decrease"
            elif previous["verdict"] in ["⬆️ too light", "⬆️ too light (RPE)"]:
                optimal_action = "increase"
            elif previous["verdict"] in ["✅ optimal", "✅ in range"]:
                # If previous session was optimal/good, maintaining or small increase is fine
                optimal_action = "maintain"
            else:  # "❓ no target"
                optimal_action = "unknown"
                continue  # Skip analysis if we don't have targets
            
            # Convert to past tense for display
            def to_past_tense(action):
                if action == "maintain":
                    return "maintained"
                elif action == "increase":
                    return "increased"
                elif action == "decrease":
                    return "decreased"
                else:
                    return action
            
            # Compare actual vs optimal
            if optimal_action == "unknown":
                continue  # Skip if we can't determine optimal action
            
            # Evaluate decision quality - be more lenient with "maintain" decisions
            decision_is_good = False
            
            # Evaluate decision quality with comprehensive RPE consideration
            decision_is_good = False
            
            # First, check if the current session's RPE justifies the action taken
            current_rpe = current.get("peak_rpe")
            
            if optimal_action == "decrease" and actual_action == "decreased":
                decision_is_good = True
            elif optimal_action == "increase" and actual_action == "increased":
                decision_is_good = True
            elif optimal_action == "maintain":
                # For maintain, check if the action was RPE-justified
                if actual_action in ["maintained", "increased"]:
                    decision_is_good = True
                elif actual_action == "decreased":
                    # Weight decrease from "optimal" previous session is justified if current RPE is high
                    if current_rpe and current_rpe >= 9.0:
                        decision_is_good = True
                    # Also justified if previous session RPE was actually high
                    elif previous.get("peak_rpe") and previous.get("peak_rpe") >= 9.0:
                        decision_is_good = True
            else:
                # For other cases, check if current session RPE justifies the action
                if actual_action == "decreased" and current_rpe and current_rpe >= 9.5:
                    decision_is_good = True  # Decrease justified by high current RPE
                elif actual_action == "increased" and current_rpe and current_rpe <= 7.5:
                    decision_is_good = True  # Increase justified by low current RPE
                elif actual_action == "maintained":
                    decision_is_good = True  # Maintaining is generally safe
            
            if decision_is_good:
                good_decisions.append({
                    "from_date": previous["date"],
                    "to_date": current["date"],
                    "action": actual_action,
                    "weight_change": weight_change,
                    "verdict": "✅ good decision"
                })
            else:
                missed_opportunities.append({
                    "from_date": previous["date"],
                    "to_date": current["date"],
                    "should_have": optimal_action,
                    "actually_did": actual_action,
                    "weight_change": weight_change,
                    "missed_opportunity": f"should have {to_past_tense(optimal_action)} but {actual_action} instead"
                })
        
        # Calculate progression efficiency
        total_decisions = len(good_decisions) + len(missed_opportunities)
        efficiency_score = (len(good_decisions) / total_decisions * 100) if total_decisions > 0 else 0
        
        evolution_data[exercise] = {
            "sessions": sessions_analysis,
            "good_decisions": good_decisions,
            "missed_opportunities": missed_opportunities,
            "efficiency_score": efficiency_score,
            "total_decisions": total_decisions,
            "absolute_latest_date": absolute_latest_date  # Add reference date
        }
    
    return evolution_data

def get_comprehensive_trends(df: pd.DataFrame) -> Dict:
    """
    Analyze comprehensive trends including volume, strength progression, and performance trajectories.
    
    Args:
        df: DataFrame with workout data
    
    Returns:
        Dictionary with trend analysis data
    """
    if len(df) == 0:
        return {}
    
    df_copy = df.copy()
    df_copy["date"] = pd.to_datetime(df_copy["date"])
    df_copy["volume"] = df_copy["weight"] * df_copy["reps"]
    df_copy["week"] = df_copy["date"].dt.isocalendar().week
    df_copy["day_number"] = (df_copy["date"] - df_copy["date"].min()).dt.days
    
    # Weekly volume analysis
    weekly_stats = df_copy.groupby("week").agg({
        "date": ["max", "min", "nunique"],  # Added min and nunique for days per week
        "volume": "sum",
        "weight": "mean", 
        "reps": "sum",
        "exercise": "nunique"
    }).round(1)
    weekly_stats.columns = ["week_end", "week_start", "days_in_week", "total_volume", "avg_weight", "total_reps", "unique_exercises"]
    
    # Determine if current week is partial
    current_week = df_copy["week"].max()
    current_week_data = weekly_stats.loc[current_week]
    current_week_days = current_week_data["days_in_week"]
    
    # Consider a week "complete" if it has 3+ workout days (reasonable for most programs)
    is_current_week_partial = current_week_days < 3
    
    # Volume trend analysis - exclude partial weeks from trend calculation
    volume_trend = "stable"
    volume_velocity = 0
    complete_weeks = weekly_stats[weekly_stats["days_in_week"] >= 3] if is_current_week_partial else weekly_stats
    
    if len(complete_weeks) >= 2:
        # Calculate trend over complete weeks only
        recent_weeks = complete_weeks.iloc[-3:] if len(complete_weeks) >= 3 else complete_weeks.iloc[-2:]
        week_numbers = list(range(len(recent_weeks)))
        volumes = recent_weeks["total_volume"].values
        
        # Linear regression for trend
        if len(week_numbers) > 1:
            slope = (volumes[-1] - volumes[0]) / (week_numbers[-1] - week_numbers[0]) if week_numbers[-1] != week_numbers[0] else 0
            volume_velocity = slope  # kg per week
            
            if slope > 500:
                volume_trend = "rapidly increasing"
            elif slope > 200:
                volume_trend = "steadily increasing"
            elif slope > -200:
                volume_trend = "stable"
            elif slope > -500:
                volume_trend = "declining"
            else:
                volume_trend = "rapidly declining"
    elif is_current_week_partial:
        volume_trend = "partial week"
        volume_velocity = 0
    
    # Exercise-specific strength trends
    exercise_trends = {}
    for exercise in df_copy["exercise"].unique():
        exercise_data = df_copy[df_copy["exercise"] == exercise].copy()
        exercise_data = exercise_data.sort_values("date")
        
        if len(exercise_data) < 3:
            continue  # Need at least 3 sessions for trend analysis
        
        # Get session-level statistics (average weight per session)
        session_stats = exercise_data.groupby("date").agg({
            "weight": "mean",
            "reps": "mean", 
            "volume": "sum",
            "rpe": "mean"
        }).reset_index()
        session_stats = session_stats.sort_values("date")
        
        # Calculate weekly progression rate
        if len(session_stats) >= 2:
            days_span = (session_stats["date"].iloc[-1] - session_stats["date"].iloc[0]).days
            weight_change = session_stats["weight"].iloc[-1] - session_stats["weight"].iloc[0]
            weekly_rate = (weight_change / (days_span / 7)) if days_span > 0 else 0
        else:
            weekly_rate = 0
        
        # Enhanced growth classification with RPE context
        if weekly_rate > 1.0:
            growth_status = "💪 Strong Growth"
        elif weekly_rate > 0.3:
            growth_status = "📈 Steady Growth"
        elif weekly_rate > -0.3:
            growth_status = "🔄 Maintaining"
        elif weekly_rate > -1.0:
            # Check if the decline is RPE-justified
            recent_sessions_with_rpe = session_stats.tail(3)
            high_rpe_detected = False
            
            # Check for high RPE in recent sessions
            for _, session in recent_sessions_with_rpe.iterrows():
                if session.get("rpe") and not pd.isna(session["rpe"]) and session["rpe"] >= 9.5:
                    high_rpe_detected = True
                    break
            
            # Also check average RPE trend
            rpe_values = [rpe for rpe in recent_sessions_with_rpe["rpe"].values if rpe and not pd.isna(rpe)]
            if rpe_values and sum(rpe_values) / len(rpe_values) >= 9.0:
                high_rpe_detected = True
            
            if high_rpe_detected:
                growth_status = "✅ Smart Adjustment"
            else:
                growth_status = "📉 Slight Decline"
        else:
            # For significant declines, also check RPE context
            recent_sessions_with_rpe = session_stats.tail(3)
            high_rpe_detected = False
            
            # Check for very high RPE in recent sessions
            for _, session in recent_sessions_with_rpe.iterrows():
                if session.get("rpe") and not pd.isna(session["rpe"]) and session["rpe"] >= 9.5:
                    high_rpe_detected = True
                    break
            
            if high_rpe_detected:
                growth_status = "✅ Smart Deload"
            else:
                growth_status = "⚠️ Significant Decline"
        
        exercise_trends[exercise] = {
            "weekly_progression_rate": weekly_rate,
            "growth_status": growth_status,
            "current_weight": session_stats["weight"].iloc[-1],
            "peak_weight": session_stats["weight"].max(),
            "recent_sessions": session_stats.tail(3)  # Last 3 sessions for display
        }
    
    # Overall fitness trajectory
    total_sessions = df_copy["date"].nunique()
    total_days = (df_copy["date"].max() - df_copy["date"].min()).days + 1
    training_frequency = total_sessions / (total_days / 7) if total_days > 0 else 0  # sessions per week
    
    # Calculate overall strength index (average of all exercise progressions)
    if exercise_trends:
        progression_rates = [data["weekly_progression_rate"] for data in exercise_trends.values()]
        avg_progression_rate = sum(progression_rates) / len(progression_rates)
        
        # Overall fitness trajectory assessment
        if avg_progression_rate > 0.3:
            fitness_trajectory = "🚀 Excellent Progress"
            trajectory_desc = "Strong upward trend across multiple exercises"
        elif avg_progression_rate > 0.1:
            fitness_trajectory = "📈 Good Progress"
            trajectory_desc = "Steady improvements in most exercises"
        elif avg_progression_rate > -0.1:
            fitness_trajectory = "🔄 Maintenance Phase"
            trajectory_desc = "Stable performance, consider progressive overload"
        else:
            fitness_trajectory = "📉 Declining Phase"
            trajectory_desc = "Consider deload, recovery focus, or program change"
    else:
        avg_progression_rate = 0
        fitness_trajectory = "📊 Insufficient Data"
        trajectory_desc = "Need more sessions for trend analysis"
    
    # Enhanced peak performance analysis with RPE context
    exercise_peaks = {}
    for exercise, data in exercise_trends.items():
        exercise_data = df_copy[df_copy["exercise"] == exercise].copy()
        
        # Get session-level data with RPE information
        session_stats = exercise_data.groupby("date").agg({
            "weight": "mean",
            "rpe": ["mean", "max"]  # Both average and peak RPE per session
        }).reset_index()
        session_stats.columns = ["date", "weight", "avg_rpe", "peak_rpe"]
        session_stats = session_stats.sort_values("date")
        
        peak_weight = session_stats["weight"].max()
        current_weight = session_stats["weight"].iloc[-1]
        
        # Find the session where peak weight was achieved
        peak_session = session_stats[session_stats["weight"] == peak_weight].iloc[-1]  # Most recent peak
        peak_rpe = peak_session["peak_rpe"] if not pd.isna(peak_session["peak_rpe"]) else None
        
        # Distance from peak
        peak_gap = peak_weight - current_weight
        peak_gap_pct = (peak_gap / peak_weight) * 100 if peak_weight > 0 else 0
        
        # RPE-aware peak status assessment
        if peak_gap_pct <= 2:
            peak_status = "🏆 At Peak"
            peak_assessment = "at all-time peak!"
        elif peak_gap_pct <= 5:
            peak_status = "🎯 Near Peak"
            peak_assessment = f"{peak_gap:.1f}kg below peak ({peak_gap_pct:.1f}% gap)"
        elif peak_gap_pct <= 10:
            # Check if the peak was achieved at unsustainable RPE
            if peak_rpe and peak_rpe >= 9.5:
                peak_status = "✅ Smart Adjustment"
                peak_assessment = f"{peak_gap:.1f}kg below unsustainable peak (peak RPE {peak_rpe:.1f} was too high)"
            else:
                peak_status = "📊 Below Peak"
                peak_assessment = f"{peak_gap:.1f}kg below peak ({peak_gap_pct:.1f}% gap)"
        else:
            # Check if the peak was achieved at unsustainable RPE
            if peak_rpe and peak_rpe >= 9.5:
                peak_status = "✅ Smart Deload"
                peak_assessment = f"{peak_gap:.1f}kg below unsustainable peak (peak RPE {peak_rpe:.1f} was too high - good deload)"
            else:
                peak_status = "⚠️ Far from Peak"
                peak_assessment = f"{peak_gap:.1f}kg below peak ({peak_gap_pct:.1f}% gap)"
        
        exercise_peaks[exercise] = {
            "peak_weight": peak_weight,
            "current_weight": current_weight,
            "peak_gap": peak_gap,
            "peak_gap_pct": peak_gap_pct,
            "peak_status": peak_status,
            "peak_assessment": peak_assessment,
            "peak_rpe": peak_rpe
        }
    
    return {
        "weekly_stats": weekly_stats,
        "volume_trend": volume_trend,
        "volume_velocity": volume_velocity,
        "exercise_trends": exercise_trends,
        "fitness_trajectory": fitness_trajectory,
        "trajectory_desc": trajectory_desc,
        "avg_progression_rate": avg_progression_rate,
        "training_frequency": training_frequency,
        "total_sessions": total_sessions,
        "total_days": total_days,
        "exercise_peaks": exercise_peaks
    }

def validate_setup() -> bool:
    """
    Validate user setup and provide helpful feedback.
    
    Returns:
        True if setup is valid, False otherwise
    """
    print("🔍 **SETUP VALIDATION**")
    print("=" * 50)
    
    issues_found = []
    warnings = []
    
    # Check API key
    api_key = os.getenv("HEVY_API_KEY")
    if not api_key:
        issues_found.append("❌ HEVY_API_KEY environment variable not set")
        print("💡 Fix: Add HEVY_API_KEY to your .env file or export it")
    else:
        print("✅ API key found")
        
        # Test API connection
        try:
            client = HevyStatsClient(api_key)
            test_data = client.get_workout_events(page=1, page_size=1, since=(datetime.now() - timedelta(days=7)).isoformat() + "Z")
            if test_data and test_data.get("workout_events"):
                print("✅ API connection successful")
            else:
                print("⚠️ API connected but no recent workouts found")
        except Exception as e:
            issues_found.append(f"❌ API connection failed: {e}")
    
    # Check AI coaching setup
    print("\n🤖 **AI COACHING SETUP**")
    if OPENAI_AVAILABLE and openai_api_key:
        print("✅ OpenAI integration available")
        
        # Test AI connection
        try:
            ai_coach = AICoach()
            if ai_coach.is_available():
                print("✅ AI coaching ready - GPT-4o-mini will provide personalized insights")
                
                # Quick test call (minimal cost)
                test_response = ai_coach.generate_session_summary(
                    {"grade": "B+", "overall_score": 85, "progressed": 3, "smart_adjustments": 2, "regressed": 0},
                    {"exercises": [{"name": "Bench Press", "verdict": "✅ optimal", "peak_rpe": 8.5}]},
                    {"fitness_trajectory": "Improving", "avg_progression_rate": 1.2, "training_frequency": 4.5}
                )
                if test_response:
                    print("✅ AI coaching test successful")
                    print(f"   Sample insight: \"{test_response[:60]}...\"")
                else:
                    warnings.append("⚠️ AI test call failed - check API key and credits")
            else:
                warnings.append("⚠️ AI coaching unavailable")
        except Exception as e:
            warnings.append(f"⚠️ AI setup issue: {e}")
    else:
        print("💡 AI coaching not configured")
        print("   • Add OPENAI_API_KEY to .env file for personalized insights")
        print("   • pip install openai")
        print("   • Cost: ~$0.01-0.05 per report with GPT-4o-mini")
    
    # Check rep rules configuration
    print("\n📏 **REP RULES CONFIGURATION**")
    try:
        from rep_rules import REP_RANGE
        configured_exercises = len(REP_RANGE)
        print(f"✅ Rep rules configured for {configured_exercises} exercises")
        
        # Show sample
        sample_exercises = list(REP_RANGE.keys())[:3]
        for ex in sample_exercises:
            range_info = REP_RANGE[ex]
            print(f"   • {ex}: {range_info}")
            
    except ImportError:
        warnings.append("⚠️ rep_rules.py not found - create it for exercise-specific targets")
    
    # Check routine configuration
    print("\n🔄 **CYCLICAL ROUTINE CONFIGURATION**")
    if ROUTINE_CONFIG_AVAILABLE:
        print("✅ Cyclical routine tracking configured")
        cycle_length = len(CYCLE_PATTERN) if CYCLE_PATTERN else 0
        print(f"   • Cycle length: {cycle_length} days")
        
        if ROUTINE_TITLE_MAPPING:
            print(f"   • {len(ROUTINE_TITLE_MAPPING)} routine titles mapped")
    else:
        print("💡 Cyclical routine tracking not configured")
        print("   • Copy routine_config.example.py to routine_config.py")
        print("   • Customize for your workout split")
    
    # Summary
    print("\n" + "=" * 50)
    if issues_found:
        print("❌ **SETUP ISSUES FOUND**:")
        for issue in issues_found:
            print(f"   {issue}")
        print("\n💡 Fix these issues before running analysis")
        return False
    else:
        print("✅ **CORE SETUP COMPLETE**")
        if warnings:
            print("\n⚠️ **OPTIONAL ENHANCEMENTS**:")
            for warning in warnings:
                print(f"   {warning}")
        
        print(f"\n🚀 Ready to run: python hevy_stats.py analyze")
        return True

def main():
    parser = argparse.ArgumentParser(description="Hevy Stats Fetcher & Coach Analysis")
    parser.add_argument("mode", nargs='?', default="both", choices=["fetch", "analyze", "export", "both", "validate"], 
                       help="Mode: fetch data from API, analyze existing data, export to CSV, both fetch+analyze, or validate setup (default: both)")
    parser.add_argument("--days", type=int, default=30,
                       help="Number of days to fetch/export (default: 30)")
    parser.add_argument("--infile", type=str, default="hevy_events.json",
                       help="Input JSON file for analysis (default: hevy_events.json)")
    parser.add_argument("--outfile", type=str, default="hevy_events.json",
                       help="Output JSON file for fetched data (default: hevy_events.json)")
    parser.add_argument("--save-csv", action="store_true",
                       help="Save analysis results to CSV file")
    parser.add_argument("--save-markdown", action="store_true",
                       help="Save coaching report as Markdown file")
    parser.add_argument("--email", action="store_true",
                       help="Send report via email (requires email environment variables)")
    parser.add_argument("--test-email", action="store_true",
                       help="Test email configuration without generating report")
    
    args = parser.parse_args()
    
    # Validate setup mode
    if args.mode == "validate":
        validate_setup()
        return
    
    # Test email configuration if requested
    if args.test_email:
        email_sender = EmailSender()
        if email_sender.test_connection():
            print("🎉 Email configuration is working!")
        else:
            print("❌ Email configuration failed. Check environment variables.")
        return
    
    print(f"🎯 Running in '{args.mode}' mode...")
    
    # Get API key from environment
    api_key = os.getenv("HEVY_API_KEY")
    
    if args.mode in ["fetch", "both"]:
        if not api_key:
            print("❌ Error: HEVY_API_KEY environment variable not set")
            print("Please run: export HEVY_API_KEY='your-api-key-here'")
            sys.exit(1)
        
        print(f"🚀 Fetching Hevy workout data...")
        client = HevyStatsClient(api_key)
        
        try:
            events = client.get_all_recent_workouts(days=args.days)
            
            if not events:
                print("❌ No workout events found")
                return
            
            # Clean and save data
            cleaned_events = client.clean_null_values(events)
            with open(args.outfile, 'w') as f:
                json.dump(cleaned_events, f, indent=2)
            print(f"💾 Data saved to {args.outfile} (null values removed)")
            
        except Exception as e:
            print(f"❌ Error during fetch: {e}")
            sys.exit(1)
    
    if args.mode in ["analyze", "export", "both"]:
        print(f"\n🔍 Processing workout data from {args.infile}...")
        
        # Convert to DataFrame
        df = events_to_df(args.infile)
        
        if len(df) == 0:
            print("❌ No workout data found for processing")
            return
        
        # Filter to recent data
        filter_days = 90 if args.mode == "analyze" else args.days
        df = filter_recent_data(df, days=filter_days)
        
        if len(df) == 0:
            print(f"❌ No workout data found in the last {filter_days} days")
            return
        
        # Filter out excluded exercises (warm-ups, cardio, etc.)
        df = filter_excluded_exercises(df)
        
        if len(df) == 0:
            print("❌ No relevant exercise data found after filtering")
            return
        
        if args.mode == "export":
            # Export-only mode
            csv_file = export_recent_workouts(df, days=args.days)
            print(f"\n🎉 Export completed! Data saved to {csv_file}")
            return
        
        # Full analysis mode (analyze or both)
        # Print comprehensive coaching report
        print_comprehensive_report(df)
        
        # Auto-save to markdown
        markdown_file = save_report_to_markdown(df)
        print(f"\n📝 Report automatically saved to {markdown_file}")
        
        # Auto-export recent workouts to CSV
        csv_file = export_recent_workouts(df, days=30)
        
        # Optional email sending
        if args.email:
            print(f"\n📧 Sending email...")
            email_sender = EmailSender()
            
            # Capture report content for email
            import io
            from contextlib import redirect_stdout
            
            report_content = io.StringIO()
            with redirect_stdout(report_content):
                print_comprehensive_report(df)
            
            success = email_sender.send_report(
                report_content.getvalue(), 
                markdown_file
            )
            
            if not success:
                print("💡 Tip: Set EMAIL_USER and EMAIL_PASSWORD environment variables for email functionality")
        
        # Optional CSV save (simplified) - now redundant since we auto-export
        if args.save_csv:
            print(f"📊 CSV export already completed automatically as {csv_file}")
        
        # Legacy save-markdown option (now redundant since we auto-save)
        if args.save_markdown:
            print(f"📝 Markdown already saved automatically as {markdown_file}")

if __name__ == "__main__":
    main() 