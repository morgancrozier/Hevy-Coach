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

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not installed, skip
    pass

# RPE-based coaching guidelines
RPE_GUIDELINES = {
    "increase_threshold": 7.5,     # If RPE below this, suggest weight increase
    "decrease_threshold": 9.0,     # If RPE above this, suggest weight decrease
    "increase_factor": 1.05,       # 5% weight increase
    "decrease_factor": 0.95,       # 5% weight decrease
}

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
        
        for _, row in exercise_data.iterrows():
            set_volume = (row["weight"] * row["reps"]) if row["weight"] > 0 else 0
            total_volume += set_volume
            sets_data.append({
                "weight": row["weight"],
                "reps": row["reps"],
                "rpe": row["rpe"],
                "volume": set_volume
            })
        
        rep_range = REP_RANGE.get(exercise, None)
        avg_reps = exercise_data["reps"].mean()
        avg_weight = exercise_data["weight"].mean()
        avg_rpe = exercise_data["rpe"].mean()
        
        # Determine verdict for this session
        if rep_range is None or rep_range[0] is None:
            verdict = "❓ no target"
            suggestion = "add rep target to rep_rules.py"
        elif avg_reps < rep_range[0]:
            verdict = "⬇️ too heavy"
            new_weight = avg_weight * 0.9
            suggestion = f"reduce to ~{new_weight:.1f}kg next time"
        elif avg_reps > rep_range[1]:
            verdict = "⬆️ too light"
            new_weight = avg_weight * 1.05
            suggestion = f"increase to ~{new_weight:.1f}kg next time"
        else:
            verdict = "✅ in range"
            # RPE-based fine-tuning even when reps are in range
            if avg_rpe and not pd.isna(avg_rpe):
                if avg_rpe < RPE_GUIDELINES["increase_threshold"]:
                    new_weight = avg_weight * RPE_GUIDELINES["increase_factor"]
                    suggestion = f"increase to ~{new_weight:.1f}kg next time (RPE {avg_rpe:.1f} too low)"
                elif avg_rpe > RPE_GUIDELINES["decrease_threshold"]:
                    new_weight = avg_weight * RPE_GUIDELINES["decrease_factor"]
                    suggestion = f"reduce to ~{new_weight:.1f}kg next time (RPE {avg_rpe:.1f} too high)"
                else:
                    suggestion = "perfect - maintain this weight!"
            else:
                suggestion = "maintain this weight (no RPE data)"
        
        workout_info["exercises"].append({
            "name": exercise,
            "sets": sets_data,
            "num_sets": len(sets_data),
            "avg_weight": avg_weight,
            "avg_reps": avg_reps,
            "avg_rpe": avg_rpe,
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
    
    # Calculate all the new metrics
    progression_data = get_exercise_progression(df)
    last_session = get_last_session_only(df)
    session_quality = calculate_session_quality(last_session, progression_data)
    periodization = detect_plateaus_and_periodization(progression_data)
    volume_recovery = get_volume_recovery_insights(df)
    exercise_evolution = analyze_exercise_evolution(df)
    
    # ========================
    # 1. SESSION QUALITY SCORE
    # ========================
    print("\n⭐ **SESSION QUALITY ASSESSMENT**")
    print("-" * 50)
    
    if session_quality:
        print(f"🎯 **Overall Grade**: {session_quality['grade']} ({session_quality['overall_score']:.0f}/100)")
        print(f"📝 **Assessment**: {session_quality['description']}")
        print(f"💪 **Progression**: {session_quality['progressed']} progressed, {session_quality['maintained']} maintained, {session_quality['regressed']} regressed")
        print(f"🔥 **Intensity Score**: {session_quality['avg_rpe_score']:.0f}/100 (RPE balance)")
        print(f"📈 **Progress Score**: {session_quality['avg_progression_score']:.0f}/100 (weight progression)")
    
    # ========================
    # 2. EXERCISE PROGRESSION TRENDS
    # ========================
    print(f"\n\n📈 **EXERCISE PROGRESSION ANALYSIS**")
    print("-" * 50)
    
    if progression_data:
        print("🔍 **Last 3-4 Sessions Per Exercise**:")
        
        # Sort by most recent volume for display
        sorted_exercises = sorted(progression_data.items(), 
                                key=lambda x: x[1]["sessions"][0]["total_volume"], reverse=True)
        
        for exercise, data in sorted_exercises[:8]:  # Show top 8 exercises
            sessions = data["sessions"]
            latest = sessions[0]
            
            print(f"\n**{exercise}**")
            
            # Show progression across sessions
            session_strs = []
            for i, session in enumerate(sessions[:3]):
                days_ago = (latest["date"] - session["date"]).days
                age_str = "today" if days_ago == 0 else f"{days_ago}d ago"
                session_strs.append(f"{session['avg_weight']:.1f}kg×{session['avg_reps']:.1f} ({age_str})")
            
            print(f"   Sessions: {' → '.join(session_strs)}")
            
            # Show trend
            if data["weight_change"] > 0:
                trend_emoji = "📈"
                trend_desc = f"+{data['weight_change']:.1f}kg (+{data['weight_change_pct']:.1f}%)"
            elif data["weight_change"] < 0:
                trend_emoji = "📉"
                trend_desc = f"{data['weight_change']:.1f}kg ({data['weight_change_pct']:.1f}%)"
            else:
                if data["is_stagnant"]:
                    trend_emoji = "⚠️"
                    trend_desc = f"stagnant for {data['sessions_count']} sessions"
                else:
                    trend_emoji = "➡️"
                    trend_desc = "maintained"
            
            print(f"   Trend: {trend_emoji} {trend_desc}")
            
            # Overall trend across all sessions
            if len(sessions) >= 3:
                overall_trend = data["trend_change_pct"]
                if abs(overall_trend) >= 2:
                    print(f"   Overall: {overall_trend:+.1f}% over {len(sessions)} sessions")
    
    # ========================
    # 3. HISTORICAL EXERCISE EVOLUTION
    # ========================
    print(f"\n\n🔍 **HISTORICAL EXERCISE EVOLUTION ANALYSIS**")
    print("-" * 50)
    
    if exercise_evolution:
        print("📚 **Learning from Past Sessions** (what should have happened vs what did happen):")
        
        # Sort by efficiency score (worst decisions first to highlight learning opportunities)
        sorted_evolution = sorted(exercise_evolution.items(), 
                                key=lambda x: x[1]["efficiency_score"])
        
        for exercise, data in sorted_evolution[:6]:  # Show top 6 exercises with most learning potential
            sessions = data["sessions"]
            efficiency = data["efficiency_score"]
            absolute_latest_date = data["absolute_latest_date"]
            
            print(f"\n**{exercise}** (Decision Efficiency: {efficiency:.0f}%)")
            
            # Show session-by-session analysis
            session_strs = []
            for session in sessions[:4]:  # Show last 4 sessions
                days_ago = (absolute_latest_date - session["date"]).days
                age_str = "today" if days_ago == 0 else f"{days_ago}d ago"
                
                # Color code the verdict
                verdict_emoji = {
                    "✅ optimal": "✅",
                    "✅ in range": "✅", 
                    "⬇️ too heavy": "🔴",
                    "⬇️ too heavy (RPE)": "🟠",
                    "⬆️ too light": "🟢",
                    "⬆️ too light (RPE)": "🟡",
                    "❓ no target": "❓"
                }.get(session["verdict"], "❓")
                
                session_str = f"{session['avg_weight']:.1f}kg×{session['avg_reps']:.1f} {verdict_emoji} ({age_str})"
                session_strs.append(session_str)
            
            print(f"   Sessions: {' → '.join(session_strs)}")
            
            # Show missed opportunities
            if data["missed_opportunities"]:
                print(f"   ⚠️ **Missed Opportunities**:")
                for miss in data["missed_opportunities"][:2]:  # Show top 2 missed opportunities
                    days_ago = (absolute_latest_date - miss["to_date"]).days
                    print(f"     • {days_ago}d ago: {miss['missed_opportunity']}")
            
            # Show good decisions  
            if data["good_decisions"]:
                recent_good = [d for d in data["good_decisions"] if 
                             (absolute_latest_date - d["to_date"]).days <= 7]
                if recent_good:
                    print(f"   ✅ **Recent Good Decisions**: {len(recent_good)} optimal weight changes")
            
            # Learning insight
            if efficiency < 50:
                print(f"   💡 **Key Learning**: Focus on RPE feedback - weight changes seem reactive rather than proactive")
            elif efficiency < 75:
                print(f"   💡 **Key Learning**: Good overall, but a few missed opportunities for faster progression")
            else:
                print(f"   💡 **Key Learning**: Excellent decision making - keep following your instincts!")
        
        # Overall evolution insights
        avg_efficiency = sum(data["efficiency_score"] for data in exercise_evolution.values()) / len(exercise_evolution)
        total_decisions = sum(data["total_decisions"] for data in exercise_evolution.values())
        total_missed = sum(len(data["missed_opportunities"]) for data in exercise_evolution.values())
        
        print(f"\n📊 **Overall Decision Quality**:")
        print(f"• **Average Efficiency**: {avg_efficiency:.0f}% across all exercises")
        print(f"• **Total Decisions Analyzed**: {total_decisions}")
        print(f"• **Missed Opportunities**: {total_missed} (learning potential)")
        
        if avg_efficiency >= 80:
            print(f"• 🌟 **Assessment**: Excellent intuitive coaching - you're making great decisions!")
        elif avg_efficiency >= 65:
            print(f"• 🎯 **Assessment**: Good decision making with room for optimization")
        else:
            print(f"• 📚 **Assessment**: Significant learning opportunity - pay closer attention to RPE and rep feedback")
    
    # ========================
    # 4. PERIODIZATION & PLATEAU DETECTION
    # ========================
    print(f"\n\n🎯 **TRAINING PERIODIZATION INSIGHTS**")
    print("-" * 50)
    
    if periodization:
        print(f"📊 **Program Status**: {periodization['program_status']}")
        print(f"💡 **Recommendation**: {periodization['program_suggestion']}")
        print(f"📈 **Plateau Rate**: {periodization['plateau_percentage']:.0f}% of exercises")
        
        if periodization["progressing_exercises"]:
            print(f"\n🚀 **Making Great Progress** ({len(periodization['progressing_exercises'])} exercises):")
            for ex in periodization["progressing_exercises"][:5]:
                print(f"• **{ex['name']}**: +{ex['progress_pct']:.1f}% progression")
        
        if periodization["plateaued_exercises"]:
            print(f"\n⚠️ **Plateaued Exercises** ({len(periodization['plateaued_exercises'])} exercises):")
            for ex in periodization["plateaued_exercises"][:5]:
                print(f"• **{ex['name']}**: stagnant for {ex['sessions_stagnant']} sessions")
        
        if periodization["deload_candidates"]:
            print(f"\n🔄 **Consider Deload** ({len(periodization['deload_candidates'])} exercises):")
            for ex in periodization["deload_candidates"][:3]:
                print(f"• **{ex}**: reduce weight 10-15% for technique focus")
        
        if periodization["regressing_exercises"]:
            print(f"\n📉 **Declining Performance** ({len(periodization['regressing_exercises'])} exercises):")
            for ex in periodization["regressing_exercises"][:3]:
                print(f"• **{ex['name']}**: {ex['decline_pct']:.1f}% decline - check form/recovery")
    
    # ========================
    # 5. VOLUME & RECOVERY ANALYSIS
    # ========================
    print(f"\n\n💪 **VOLUME & RECOVERY INSIGHTS**")
    print("-" * 50)
    
    if volume_recovery:
        print(f"📅 **Recovery Status**: {volume_recovery['recovery_status']}")
        print(f"⏰ **Days Since Last Workout**: {volume_recovery['days_since_last']}")
        print(f"💤 **Average Rest Between Sessions**: {volume_recovery['avg_rest_days']:.1f} days")
        
        if volume_recovery["volume_change_pct"] != 0:
            trend_emoji = "📈" if volume_recovery["volume_change_pct"] > 0 else "📉"
            print(f"📊 **Weekly Volume Trend**: {trend_emoji} {volume_recovery['volume_trend']} ({volume_recovery['volume_change_pct']:+.1f}%)")
        
        if volume_recovery["muscle_volume"]:
            print(f"\n🎯 **Volume by Muscle Group**:")
            sorted_muscles = sorted(volume_recovery["muscle_volume"].items(), key=lambda x: x[1], reverse=True)
            for muscle, volume in sorted_muscles:
                print(f"• **{muscle.title()}**: {volume:.0f}kg total volume")
    
    # ========================
    # 6. PAST 30 DAYS OVERVIEW (CONDENSED)
    # ========================
    print("\n📊 **30-DAY OVERVIEW & TRENDS**")
    print("-" * 50)
    
    overview = get_30_day_overview(df)
    if overview:
        print(f"📅 **Period**: {overview['date_range'][0]} to {overview['date_range'][1]}")
        print(f"🏃 **Total Workouts**: {overview['total_workouts']}")
        print(f"💪 **Exercises Trained**: {overview['total_exercises']}")
        
        print(f"\n🔥 **Most Frequent Exercises**:")
        for exercise in overview["top_by_frequency"].index[:3]:
            row = overview["top_by_frequency"].loc[exercise]
            print(f"• **{exercise}**: {row['sessions']} sessions")
        
        print(f"\n🏋️ **Highest Volume Exercises**:")
        for exercise in overview["top_by_volume"].index[:3]:
            row = overview["top_by_volume"].loc[exercise]
            print(f"• **{exercise}**: {row['total_volume']:.0f}kg total")
    
    # ========================
    # 7. LAST SESSION DEEP DIVE
    # ========================
    print(f"\n\n🎯 **LAST SESSION DEEP DIVE**")
    print("-" * 50)
    
    if last_session:
        print(f"📅 **Date**: {last_session['date']}")
        print(f"🏷️ **Workout**: {last_session['workout_title']}")
        print(f"💪 **Exercises**: {last_session['total_exercises']}")
        print(f"📋 **Total Sets**: {last_session['total_sets']}")
        
        print(f"\n🔍 **Exercise-by-Exercise Breakdown**:")
        
        for i, ex in enumerate(last_session["exercises"], 1):
            # Format set details
            set_details = []
            for s in ex["sets"]:
                if s["weight"] > 0:
                    rpe_str = f" @{s['rpe']:.1f}" if s["rpe"] and not pd.isna(s["rpe"]) else ""
                    set_details.append(f"{s['weight']:.1f}kg×{s['reps']}{rpe_str}")
                else:
                    set_details.append(f"{s['reps']} reps")
            
            target_str = ""
            if ex["target_range"] is not None and ex["target_range"][0] is not None:
                target_str = f" (target: {ex['target_range'][0]}-{ex['target_range'][1]})"
            
            print(f"\n**{i}. {ex['name']}**{target_str}")
            print(f"   Sets: {' | '.join(set_details)}")
            print(f"   Average: {ex['avg_weight']:.1f}kg × {ex['avg_reps']:.1f} reps")
            
            if ex["avg_rpe"] and not pd.isna(ex["avg_rpe"]):
                print(f"   RPE: {ex['avg_rpe']:.1f}")
            
            print(f"   Volume: {ex['total_volume']:.0f}kg")
            print(f"   **{ex['verdict']}** → {ex['suggestion']}")
        
        # Session summary
        in_range = sum(1 for ex in last_session["exercises"] if ex["verdict"] == "✅ in range")
        too_heavy = sum(1 for ex in last_session["exercises"] if ex["verdict"] == "⬇️ too heavy")
        too_light = sum(1 for ex in last_session["exercises"] if ex["verdict"] == "⬆️ too light")
        no_target = sum(1 for ex in last_session["exercises"] if ex["verdict"] == "❓ no target")
        
        session_score = (in_range / len(last_session["exercises"])) * 100 if last_session["exercises"] else 0
    
    # ========================
    # 8. NEXT SESSION RECOMMENDATIONS
    # ========================
    print(f"\n\n💡 **NEXT SESSION RECOMMENDATIONS**")
    print("-" * 50)
    
    if last_session and last_session["exercises"]:
        adjustments = []
        maintains = []
        
        for ex in last_session["exercises"]:
            if ex["verdict"] == "⬇️ too heavy":
                adjustments.append(f"• **{ex['name']}**: {ex['suggestion']}")
            elif ex["verdict"] == "⬆️ too light":
                adjustments.append(f"• **{ex['name']}**: {ex['suggestion']}")
            elif ex["verdict"] == "✅ in range":
                # Check if the suggestion involves a weight change (RPE-based adjustment)
                if "increase to" in ex["suggestion"] or "reduce to" in ex["suggestion"]:
                    adjustments.append(f"• **{ex['name']}**: {ex['suggestion']}")
                else:
                    maintains.append(f"• **{ex['name']}**: keep {ex['avg_weight']:.1f}kg")
            else:  # "❓ no target"
                maintains.append(f"• **{ex['name']}**: {ex['suggestion']}")
        
        if adjustments:
            print("🔧 **Weight Adjustments Needed**:")
            for adj in adjustments:
                print(adj)
        
        if maintains:
            print(f"\n✅ **Keep These Weights** (they're working!):")
            for maint in maintains[:5]:  # Show top 5
                print(maint)
        
        # Smart focus points based on all analysis
        print(f"\n🎯 **Smart Focus Points**:")
        
        if periodization and periodization["plateau_percentage"] > 30:
            print("• ⚠️ High plateau rate - consider technique review or deload week")
        elif session_quality and session_quality["grade"] in ["A+", "A"]:
            print("• 🌟 Excellent session quality - maintain this momentum!")
        elif session_quality and session_quality["avg_rpe_score"] < 70:
            print("• 🔥 RPE too low/high - better intensity management needed")
        
        if volume_recovery and volume_recovery["days_since_last"] > 4:
            print("• ⏰ Extended rest period - ease back in gradually")
        elif volume_recovery and volume_recovery["volume_change_pct"] > 15:
            print("• 📈 Volume increasing rapidly - monitor recovery closely")
        
        print("• 🎯 Aim for RPE 7.5-9 for optimal muscle growth")
        print("• 💤 Rest 2-3 minutes between sets for compound movements")
        
        if periodization and len(periodization["deload_candidates"]) > 0:
            print("• 🔄 Consider a deload week for stagnant exercises")
    
    print("\n" + "="*80)

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
    
    # Count exercises by status
    progressed = 0  # Weight increased from last session
    maintained = 0  # Same weight, good RPE
    regressed = 0   # Weight decreased or struggling
    
    rpe_scores = []
    progression_scores = []
    
    for exercise in last_session["exercises"]:
        exercise_name = exercise["name"]
        
        # RPE quality (7-9 is ideal)
        if exercise["avg_rpe"] and not pd.isna(exercise["avg_rpe"]):
            rpe = exercise["avg_rpe"]
            if 7.5 <= rpe <= 9.0:
                rpe_score = 100  # Perfect RPE range
            elif 7.0 <= rpe < 7.5:
                rpe_score = 85   # Slightly too easy
            elif 9.0 < rpe <= 9.5:
                rpe_score = 85   # Slightly too hard
            elif 6.5 <= rpe < 7.0:
                rpe_score = 70   # Too easy
            elif 9.5 < rpe <= 10:
                rpe_score = 60   # Too hard
            else:
                rpe_score = 40   # Way off
            rpe_scores.append(rpe_score)
        
        # Progression quality
        if exercise_name in progression_data:
            prog_data = progression_data[exercise_name]
            
            if prog_data["weight_change"] > 0:
                progressed += 1
                progression_scores.append(100)
            elif prog_data["weight_change"] == 0:
                if prog_data["is_stagnant"]:
                    progression_scores.append(60)  # Stagnant
                else:
                    maintained += 1
                    progression_scores.append(80)  # Maintained
            else:
                regressed += 1
                progression_scores.append(40)  # Regressed
        else:
            progression_scores.append(70)  # No data, neutral
    
    # Calculate overall scores
    avg_rpe_score = sum(rpe_scores) / len(rpe_scores) if rpe_scores else 70
    avg_progression_score = sum(progression_scores) / len(progression_scores) if progression_scores else 70
    
    # Weighted overall score
    overall_score = (avg_rpe_score * 0.4) + (avg_progression_score * 0.6)
    
    # Determine grade
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
        "regressed": regressed,
        "total_exercises": total_exercises
    }

def detect_plateaus_and_periodization(progression_data: Dict) -> Dict:
    """
    Detect plateaus and provide periodization suggestions.
    
    Args:
        progression_data: Exercise progression data
    
    Returns:
        Dictionary with periodization insights and suggestions
    """
    plateaued_exercises = []
    progressing_exercises = []
    regressing_exercises = []
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
            regressing_exercises.append({
                "name": exercise,
                "decline_pct": data["trend_change_pct"]
            })
    
    # Overall program assessment
    plateau_pct = (len(plateaued_exercises) / total_exercises) * 100 if total_exercises > 0 else 0
    
    if plateau_pct > 50:
        program_status = "🚨 Major Plateau"
        program_suggestion = "Consider a deload week or program change"
    elif plateau_pct > 30:
        program_status = "⚠️ Moderate Plateau"
        program_suggestion = "Review programming and consider technique focus"
    elif len(progressing_exercises) > len(plateaued_exercises):
        program_status = "📈 Progressing Well"
        program_suggestion = "Keep current program, great momentum!"
    else:
        program_status = "🔄 Mixed Progress"
        program_suggestion = "Fine-tune weights and recovery"
    
    return {
        "plateaued_exercises": plateaued_exercises,
        "progressing_exercises": progressing_exercises,
        "regressing_exercises": regressing_exercises,
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
            
            # Determine the current session's performance verdict
            rep_range = REP_RANGE.get(exercise, None)
            
            if rep_range is None or rep_range[0] is None:
                verdict = "❓ no target"
            else:
                # Analyze the session performance
                if avg_reps < rep_range[0]:
                    verdict = "⬇️ too heavy"
                elif avg_reps > rep_range[1]:
                    verdict = "⬆️ too light"
                else:
                    # In range, check RPE for fine-tuning
                    if avg_rpe and not pd.isna(avg_rpe):
                        if avg_rpe < RPE_GUIDELINES["increase_threshold"]:
                            verdict = "⬆️ too light (RPE)"
                        elif avg_rpe > RPE_GUIDELINES["decrease_threshold"]:
                            verdict = "⬇️ too heavy (RPE)"
                        else:
                            verdict = "✅ optimal"
                    else:
                        verdict = "✅ in range"
            
            sessions_analysis.append({
                "date": date,
                "session_ago": i,
                "avg_weight": avg_weight,
                "avg_reps": avg_reps,
                "avg_rpe": avg_rpe,
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
            if previous["verdict"] == "⬇️ too heavy" or previous["verdict"] == "⬇️ too heavy (RPE)":
                optimal_action = "decrease"
            elif previous["verdict"] == "⬆️ too light" or previous["verdict"] == "⬆️ too light (RPE)":
                optimal_action = "increase"
            elif previous["verdict"] == "✅ optimal" or previous["verdict"] == "✅ in range":
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
            
            # Evaluate decision quality
            if (optimal_action == "decrease" and actual_action == "decreased") or \
               (optimal_action == "increase" and actual_action == "increased") or \
               (optimal_action == "maintain" and actual_action in ["maintained", "increased"]):
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

def main():
    parser = argparse.ArgumentParser(description="Hevy Stats Fetcher & Coach Analysis")
    parser.add_argument("mode", nargs='?', default="both", choices=["fetch", "analyze", "both"], 
                       help="Mode: fetch data from API, analyze existing data, or both (default: both)")
    parser.add_argument("--days", type=int, default=30,
                       help="Number of days to fetch (default: 30)")
    parser.add_argument("--infile", type=str, default="hevy_events.json",
                       help="Input JSON file for analysis (default: hevy_events.json)")
    parser.add_argument("--outfile", type=str, default="hevy_events.json",
                       help="Output JSON file for fetched data (default: hevy_events.json)")
    parser.add_argument("--save-csv", action="store_true",
                       help="Save analysis results to CSV file")
    parser.add_argument("--save-markdown", action="store_true",
                       help="Save coaching report as Markdown file")
    
    args = parser.parse_args()
    
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
    
    if args.mode in ["analyze", "both"]:
        print(f"\n🔍 Analyzing workout data from {args.infile}...")
        
        # Convert to DataFrame
        df = events_to_df(args.infile)
        
        if len(df) == 0:
            print("❌ No workout data found for analysis")
            return
        
        # Filter to last 90 days only
        df = filter_recent_data(df, days=90)
        
        if len(df) == 0:
            print("❌ No workout data found in the last 90 days")
            return
        
        # Filter out excluded exercises (warm-ups, cardio, etc.)
        df = filter_excluded_exercises(df)
        
        if len(df) == 0:
            print("❌ No relevant exercise data found after filtering")
            return
        
        # Print comprehensive coaching report
        print_comprehensive_report(df)
        
        # Auto-save to markdown
        markdown_file = save_report_to_markdown(df)
        print(f"\n📝 Report automatically saved to {markdown_file}")
        
        # Optional CSV save (simplified)
        if args.save_csv:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_file = f"hevy_workout_data_{timestamp}.csv"
            df.to_csv(csv_file, index=False)
            print(f"💾 Raw workout data saved to {csv_file}")
        
        # Legacy save-markdown option (now redundant since we auto-save)
        if args.save_markdown:
            print(f"📝 Markdown already saved automatically as {markdown_file}")

if __name__ == "__main__":
    main() 