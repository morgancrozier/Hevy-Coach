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

# RPE-based coaching guidelines
RPE_GUIDELINES = {
    "increase_threshold": 7.5,     # If RPE below this, suggest weight increase
    "decrease_threshold": 9.0,     # If RPE above this, suggest weight decrease
    "increase_factor": 1.05,       # 5% weight increase
    "decrease_factor": 0.95,       # 5% weight decrease
}

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
            
            # Create condensed email content
            condensed_content = self.create_condensed_email_content(report_content)
            
            # Create HTML email body with simplified mobile-friendly styling
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                        line-height: 1.5;
                        color: #333;
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 15px;
                        background-color: #f8f9fa;
                    }}
                    .container {{
                        background-color: white;
                        padding: 20px;
                        border-radius: 8px;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    }}
                    h1 {{
                        color: #2c3e50;
                        border-bottom: 2px solid #3498db;
                        padding-bottom: 8px;
                        margin-bottom: 20px;
                        font-size: 1.4em;
                    }}
                    h2 {{
                        color: #34495e;
                        margin-top: 20px;
                        margin-bottom: 12px;
                        font-size: 1.1em;
                    }}
                    h3 {{
                        color: #2c3e50;
                        margin-top: 12px;
                        margin-bottom: 8px;
                        font-size: 1em;
                    }}
                    
                    /* Quick Summary Styling */
                    .quick-summary {{
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        padding: 20px;
                        border-radius: 8px;
                        margin-bottom: 20px;
                        text-align: center;
                    }}
                    .grade-box {{
                        background: rgba(255,255,255,0.15);
                        padding: 15px;
                        border-radius: 6px;
                        margin-top: 10px;
                    }}
                    .grade {{
                        font-size: 1.8em;
                        font-weight: bold;
                        display: block;
                        margin-bottom: 8px;
                    }}
                    .progression {{
                        font-weight: bold;
                        margin-top: 8px;
                        font-size: 0.95em;
                    }}
                    
                    /* Action Section Styling */
                    .action-section {{
                        background: #f8f9fa;
                        padding: 15px;
                        border-radius: 6px;
                        margin-bottom: 20px;
                    }}
                    .adjustments {{
                        background: #fff3cd;
                        border-left: 4px solid #f39c12;
                        padding: 12px;
                        margin: 8px 0;
                        border-radius: 0 4px 4px 0;
                    }}
                    .good-weights {{
                        background: #d5f4e6;
                        border-left: 4px solid #27ae60;
                        padding: 12px;
                        margin: 8px 0;
                        border-radius: 0 4px 4px 0;
                    }}
                    .insights {{
                        background: #e3f2fd;
                        border-left: 4px solid #2196f3;
                        padding: 12px;
                        margin: 8px 0;
                        border-radius: 0 4px 4px 0;
                    }}
                    
                    /* Simplified Full Report */
                    .full-report {{
                        margin-top: 25px;
                        border-top: 1px solid #dee2e6;
                        padding-top: 15px;
                    }}
                    details {{
                        background: #f8f9fa;
                        border-radius: 6px;
                        padding: 10px;
                    }}
                    summary {{
                        cursor: pointer;
                        font-weight: bold;
                        padding: 8px;
                        background: #e9ecef;
                        border-radius: 4px;
                        margin-bottom: 10px;
                        font-size: 0.95em;
                    }}
                    summary:hover {{
                        background: #dee2e6;
                    }}
                    .detailed-content {{
                        margin-top: 10px;
                        padding: 10px;
                        background: white;
                        border-radius: 4px;
                        border: 1px solid #dee2e6;
                    }}
                    
                    /* Simple list styling */
                    ul {{ 
                        padding-left: 18px; 
                        margin: 8px 0;
                    }}
                    li {{ 
                        margin: 3px 0;
                        line-height: 1.4;
                    }}
                    
                    /* Clean paragraph styling */
                    p {{
                        margin: 8px 0;
                        line-height: 1.4;
                    }}
                    
                    .footer {{
                        margin-top: 25px;
                        padding-top: 12px;
                        border-top: 1px solid #dee2e6;
                        text-align: center;
                        color: #6c757d;
                        font-size: 0.85em;
                    }}
                    
                    /* Mobile-first responsive design */
                    @media (max-width: 600px) {{
                        body {{ 
                            padding: 10px; 
                            font-size: 14px;
                        }}
                        .container {{ 
                            padding: 15px; 
                        }}
                        h1 {{ 
                            font-size: 1.2em; 
                        }}
                        h2 {{ 
                            font-size: 1em; 
                        }}
                        .grade {{ 
                            font-size: 1.5em; 
                        }}
                        .quick-summary {{
                            padding: 15px;
                        }}
                        .action-section {{
                            padding: 12px;
                        }}
                        .adjustments, .good-weights, .insights {{
                            padding: 10px;
                        }}
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🏋️‍♂️ Daily Hevy Coaching Report</h1>
                    
                    {condensed_content}
                    
                    <div class="footer">
                        <p>💡 AI-powered coaching analysis</p>
                        <p>Generated {datetime.now().strftime('%Y-%m-%d %H:%M UTC')} • <strong>Hevy Coach Pro</strong></p>
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
        """Convert markdown-formatted report content to HTML."""
        import re
        
        # Start with the content
        html = content
        
        # Convert headers
        html = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        html = re.sub(r'^\*\*(.*?)\*\*$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^(.*?)\*\*$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        
        # Convert bold text
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
        
        # Convert section dividers
        html = re.sub(r'^-{50,}$', '<hr>', html, flags=re.MULTILINE)
        html = re.sub(r'^={50,}$', '<hr style="border: 2px solid #3498db;">', html, flags=re.MULTILINE)
        
        # Convert bullet points
        html = re.sub(r'^• (.*?)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        html = re.sub(r'^  • (.*?)$', r'<li style="margin-left: 20px;">\1</li>', html, flags=re.MULTILINE)
        
        # Wrap consecutive list items in ul tags
        html = re.sub(r'(<li>.*?</li>(\n<li>.*?</li>)*)', r'<ul>\1</ul>', html, flags=re.DOTALL)
        
        # Convert metric lines to styled divs
        html = re.sub(r'^🎯 (.*?)$', r'<div class="metric">🎯 <strong>\1</strong></div>', html, flags=re.MULTILINE)
        html = re.sub(r'^📝 (.*?)$', r'<div class="metric">📝 \1</div>', html, flags=re.MULTILINE)
        html = re.sub(r'^💪 (.*?)$', r'<div class="metric">💪 \1</div>', html, flags=re.MULTILINE)
        html = re.sub(r'^🔥 (.*?)$', r'<div class="metric">🔥 \1</div>', html, flags=re.MULTILINE)
        html = re.sub(r'^📈 (.*?)$', r'<div class="metric">📈 \1</div>', html, flags=re.MULTILINE)
        
        # Convert exercise blocks
        exercise_pattern = r'\*\*(.*?)\*\*\n((?:   .*?\n)*)'
        html = re.sub(exercise_pattern, r'<div class="exercise"><h3>\1</h3>\2</div>', html, flags=re.MULTILINE)
        
        # Convert grades to styled spans
        html = re.sub(r'(A\+|A|B\+|B|C\+|C|D) \((\d+)/100\)', r'<span class="grade">\1 (\2/100)</span>', html)
        
        # Convert line breaks to HTML
        html = html.replace('\n', '<br>\n')
        
        # Clean up extra br tags
        html = re.sub(r'(<br>\n){3,}', '<br><br>\n', html)
        
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
        
        # Determine verdict for this session - prioritize RPE over rep ranges
        if rep_range is None or rep_range[0] is None:
            verdict = "❓ no target"
            suggestion = "add rep target to rep_rules.py"
        else:
            # First check RPE if available (RPE takes priority)
            if peak_rpe and not pd.isna(peak_rpe):
                if peak_rpe >= 9.5:
                    verdict = "⬇️ too heavy"
                    new_weight = get_realistic_weight_recommendation(avg_weight, 0.95, sets_data)
                    suggestion = f"reduce to {new_weight:.1f}kg next time (peak RPE {peak_rpe:.1f} too high)"
                elif peak_rpe <= 7.0:
                    verdict = "⬆️ too light"
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
                        new_weight = get_realistic_weight_recommendation(avg_weight, 0.90, sets_data)
                        suggestion = f"reduce to {new_weight:.1f}kg next time"
                    elif avg_reps > rep_range[1]:
                        verdict = "⬆️ too light"
                        new_weight = get_realistic_weight_recommendation(avg_weight, 1.05, sets_data)
                        suggestion = f"increase to {new_weight:.1f}kg next time"
                    else:
                        verdict = "✅ in range"
                        suggestion = "maintain this weight (good RPE and reps)"
            else:
                # No RPE data, fall back to rep-based analysis only
                if avg_reps < rep_range[0]:
                    verdict = "⬇️ too heavy"
                    new_weight = get_realistic_weight_recommendation(avg_weight, 0.90, sets_data)
                    suggestion = f"reduce to {new_weight:.1f}kg next time"
                elif avg_reps > rep_range[1]:
                    verdict = "⬆️ too light"
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
    
    # Calculate all the new metrics
    progression_data = get_exercise_progression(df)
    last_session = get_last_session_only(df)
    session_quality = calculate_session_quality(last_session, progression_data)
    periodization = detect_plateaus_and_periodization(progression_data)
    volume_recovery = get_volume_recovery_insights(df)
    exercise_evolution = analyze_exercise_evolution(df)
    comprehensive_trends = get_comprehensive_trends(df)
    
    # ========================
    # 1. SESSION QUALITY SCORE
    # ========================
    print("\n⭐ **SESSION QUALITY ASSESSMENT**")
    print("-" * 50)
    
    if session_quality:
        print(f"🎯 **Overall Grade**: {session_quality['grade']} ({session_quality['overall_score']:.0f}/100)")
        print(f"📝 **Assessment**: {session_quality['description']}")
        print(f"💪 **Progression**: {session_quality['progressed']} progressed, {session_quality['maintained']} maintained, {session_quality['smart_adjustments']} smart adjustments, {session_quality['regressed']} regressed")
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
    # 3. COMPREHENSIVE TRENDS & TRAJECTORIES
    # ========================
    print(f"\n\n📊 **COMPREHENSIVE TRENDS & TRAJECTORIES**")
    print("-" * 50)
    
    if comprehensive_trends:
        print(f"🎯 **Overall Fitness Trajectory**: {comprehensive_trends['fitness_trajectory']}")
        print(f"📝 **Assessment**: {comprehensive_trends['trajectory_desc']}")
        print(f"📈 **Average Progression Rate**: {comprehensive_trends['avg_progression_rate']:+.1f}kg/week across all exercises")
        print(f"🏃 **Training Frequency**: {comprehensive_trends['training_frequency']:.1f} sessions/week over {comprehensive_trends['total_days']} days")
        
        # Weekly volume trends
        if len(comprehensive_trends["weekly_stats"]) >= 2:
            print(f"\n📊 **Weekly Volume Analysis**:")
            weekly_stats = comprehensive_trends["weekly_stats"]
            
            # Check if current week is partial
            current_week_data = weekly_stats.iloc[-1]
            is_current_week_partial = current_week_data["days_in_week"] < 3
            
            if comprehensive_trends['volume_trend'] == "partial week":
                print(f"   Volume Trend: Partial week in progress ({current_week_data['days_in_week']:.0f} workout days so far)")
                print(f"   📊 Too early to assess weekly trend")
            else:
                print(f"   Volume Trend: {comprehensive_trends['volume_trend'].title()}")
                if comprehensive_trends['volume_velocity'] != 0:
                    print(f"   Volume Velocity: {comprehensive_trends['volume_velocity']:+.0f}kg/week")
            
            # Show last 3 weeks with context
            recent_weeks = weekly_stats.tail(3)
            for i, (_, week) in enumerate(recent_weeks.iterrows()):
                week_age = len(recent_weeks) - i - 1
                age_str = "this week" if week_age == 0 else f"{week_age} week{'s' if week_age > 1 else ''} ago"
                
                # Add context for partial week
                if week_age == 0 and is_current_week_partial:
                    partial_note = f" - partial week ({week['days_in_week']:.0f} days)"
                    print(f"   • {age_str}: {week['total_volume']:,.0f}kg total ({week['unique_exercises']:.0f} exercises){partial_note}")
                else:
                    print(f"   • {age_str}: {week['total_volume']:,.0f}kg total ({week['unique_exercises']:.0f} exercises)")
        
        # Exercise-specific strength trends
        if comprehensive_trends["exercise_trends"]:
            print(f"\n💪 **Strength Progression by Exercise** (per week rates):")
            
            # Sort by progression rate (best performers first)
            sorted_trends = sorted(comprehensive_trends["exercise_trends"].items(), 
                                 key=lambda x: x[1]["weekly_progression_rate"], reverse=True)
            
            for exercise, trend_data in sorted_trends[:8]:  # Show top 8
                rate = trend_data["weekly_progression_rate"]
                status = trend_data["growth_status"]
                current_weight = trend_data["current_weight"]
                peak_weight = trend_data["peak_weight"]
                
                # Calculate percentage change from first to current session
                recent_sessions = trend_data["recent_sessions"]
                if len(recent_sessions) >= 2:
                    starting_weight = recent_sessions.iloc[0]["weight"]
                    total_change_pct = ((current_weight - starting_weight) / starting_weight) * 100 if starting_weight > 0 else 0
                    days_span = (recent_sessions.iloc[-1]["date"] - recent_sessions.iloc[0]["date"]).days
                else:
                    total_change_pct = 0
                    days_span = 0
                
                print(f"\n   **{exercise}**: {status}")
                print(f"      Rate: {rate:+.1f}kg/week | Total: {total_change_pct:+.1f}% over {days_span} days")
                print(f"      Weight: {starting_weight:.1f}kg → {current_weight:.1f}kg")
                
                # Show recent session progression
                if len(recent_sessions) >= 2:
                    session_weights = [f"{row['weight']:.1f}kg" for _, row in recent_sessions.iterrows()]
                    print(f"      Recent: {' → '.join(session_weights)}")
        
        # Peak performance analysis
        if comprehensive_trends["exercise_peaks"]:
            print(f"\n🏆 **Peak Performance Analysis**:")
            
            # Group by peak status
            peak_groups = {}
            for exercise, peak_data in comprehensive_trends["exercise_peaks"].items():
                status = peak_data["peak_status"]
                if status not in peak_groups:
                    peak_groups[status] = []
                peak_groups[status].append((exercise, peak_data))
            
            # Display each group with enhanced categories
            for status in ["🏆 At Peak", "🎯 Near Peak", "✅ Smart Adjustment", "✅ Smart Deload", "📊 Below Peak", "⚠️ Far from Peak"]:
                if status in peak_groups:
                    exercises = peak_groups[status]
                    print(f"\n   **{status}** ({len(exercises)} exercises):")
                    
                    for exercise, peak_data in exercises[:5]:  # Show top 5 per group
                        assessment = peak_data["peak_assessment"]
                        print(f"      • **{exercise}**: {assessment}")
        
        # Training insights based on trends
        print(f"\n💡 **Trend-Based Insights**:")
        
        avg_rate = comprehensive_trends['avg_progression_rate']
        if avg_rate > 0.3:
            print("   • 🚀 Excellent progression rate - current program is highly effective!")
            print("   • 🎯 Focus: Maintain consistency, monitor for overreaching")
        elif avg_rate > 0.1:
            print("   • 📈 Good steady progress - sustainable progression pattern")
            print("   • 🎯 Focus: Continue current approach, consider small increases in volume")
        elif avg_rate > -0.1:
            print("   • 🔄 Maintenance phase - strength is stable")
            print("   • 🎯 Focus: Add progressive overload or consider program variation")
        else:
            print("   • ⚠️ Declining trend detected across multiple exercises")
            print("   • 🎯 Focus: Review recovery, consider deload week, check nutrition")
        
        volume_trend = comprehensive_trends['volume_trend']
        if "increasing" in volume_trend:
            print("   • 📊 Volume trending upward - monitor recovery closely")
        elif "declining" in volume_trend:
            print("   • 📊 Volume declining - may need motivation boost or program refresh")
        
        frequency = comprehensive_trends['training_frequency']
        if frequency >= 4:
            print("   • 🏃 High training frequency - excellent consistency!")
        elif frequency >= 3:
            print("   • 🏃 Good training frequency - sustainable routine")
        elif frequency >= 2:
            print("   • 🏃 Moderate frequency - consider adding 1 more session/week")
        else:
            print("   • 🏃 Low frequency - aim for 3+ sessions/week for better results")
    
    # ========================
    # 4. HISTORICAL EXERCISE EVOLUTION
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
            
            # Get target rep range for context
            rep_range = REP_RANGE.get(exercise, None)
            target_info = f" (target: {rep_range[0]}-{rep_range[1]} reps)" if rep_range and rep_range[0] else " (no target set)"
            
            print(f"\n**{exercise}**{target_info}")
            print(f"   Decision Efficiency: {efficiency:.0f}% | Sessions Analyzed: {len(sessions)}")
            
            # Show session-by-session analysis with detailed RPE context
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
                
                # Build detailed session string with RPE context
                session_str = f"{session['avg_weight']:.1f}kg×{session['avg_reps']:.1f}"
                
                # Add RPE information if available
                if session.get("peak_rpe") and not pd.isna(session["peak_rpe"]):
                    rpe_str = f"@{session['peak_rpe']:.1f}"
                    if session.get("final_rpe") and session["final_rpe"] != session["peak_rpe"]:
                        rpe_str += f"(final:{session['final_rpe']:.1f})"
                    session_str += rpe_str
                
                session_str += f" {verdict_emoji} ({age_str})"
                session_strs.append(session_str)
            
            print(f"   Sessions: {' → '.join(session_strs)}")
            
            # Show weight progression between sessions
            if len(sessions) >= 2:
                print(f"   Weight Changes:")
                for i in range(len(sessions) - 1):
                    current = sessions[i]
                    previous = sessions[i + 1]
                    weight_change = current["avg_weight"] - previous["avg_weight"]
                    
                    curr_days = (absolute_latest_date - current["date"]).days
                    prev_days = (absolute_latest_date - previous["date"]).days
                    
                    curr_str = "today" if curr_days == 0 else f"{curr_days}d ago"
                    prev_str = "today" if prev_days == 0 else f"{prev_days}d ago"
                    
                    if abs(weight_change) >= 0.1:
                        change_pct = (weight_change / previous["avg_weight"]) * 100 if previous["avg_weight"] > 0 else 0
                        change_direction = "📈" if weight_change > 0 else "📉"
                        print(f"     • {prev_str} → {curr_str}: {weight_change:+.1f}kg ({change_pct:+.1f}%) {change_direction}")
                    else:
                        print(f"     • {prev_str} → {curr_str}: maintained weight ➡️")
            
            # Show detailed missed opportunities with RPE context
            if data["missed_opportunities"]:
                print(f"   ⚠️ **Missed Opportunities** ({len(data['missed_opportunities'])} total):")
                for miss in data["missed_opportunities"][:3]:  # Show top 3 missed opportunities
                    days_ago = (absolute_latest_date - miss["to_date"]).days
                    
                    # Find the session that led to this missed opportunity
                    prev_session = None
                    curr_session = None
                    for i, session in enumerate(sessions):
                        if session["date"] == miss["to_date"]:
                            curr_session = session
                            if i + 1 < len(sessions):
                                prev_session = sessions[i + 1]
                            break
                    
                    # Create detailed explanation
                    explanation = miss['missed_opportunity']
                    if prev_session and curr_session:
                        # Add detailed RPE and rep context
                        prev_rpe = prev_session.get("peak_rpe")
                        curr_rpe = curr_session.get("peak_rpe")
                        
                        context_parts = []
                        
                        # RPE context
                        if prev_rpe and not pd.isna(prev_rpe):
                            if prev_rpe >= 9.5:
                                context_parts.append(f"previous RPE {prev_rpe:.1f} was too high")
                            elif prev_rpe <= 7.0:
                                context_parts.append(f"previous RPE {prev_rpe:.1f} was too low")
                            elif prev_session["verdict"] == "✅ optimal":
                                context_parts.append(f"previous session was optimal at RPE {prev_rpe:.1f}")
                        
                        # Rep context
                        if rep_range and rep_range[0]:
                            prev_reps = prev_session["avg_reps"]
                            if prev_reps < rep_range[0]:
                                context_parts.append(f"previous reps {prev_reps:.1f} below target {rep_range[0]}-{rep_range[1]}")
                            elif prev_reps > rep_range[1]:
                                context_parts.append(f"previous reps {prev_reps:.1f} above target {rep_range[0]}-{rep_range[1]}")
                        
                        if context_parts:
                            explanation += f" ({', '.join(context_parts)})"
                    
                    print(f"     • {days_ago}d ago: {explanation}")
            
            # Show good decisions with detailed context
            if data["good_decisions"]:
                recent_good = [d for d in data["good_decisions"] if 
                             (absolute_latest_date - d["to_date"]).days <= 14]  # Show more recent decisions
                if recent_good:
                    print(f"   ✅ **Good Decisions** ({len(recent_good)} in last 2 weeks):")
                    
                    # Show examples of good decisions with context
                    for good_example in recent_good[:2]:  # Show top 2 examples
                        days_ago = (absolute_latest_date - good_example["to_date"]).days
                        
                        # Find the sessions involved
                        for i, session in enumerate(sessions):
                            if session["date"] == good_example["to_date"]:
                                curr_session = session
                                prev_session = sessions[i + 1] if i + 1 < len(sessions) else None
                                break
                        
                        if prev_session and curr_session:
                            action_desc = {
                                "increased": "increased weight",
                                "decreased": "decreased weight", 
                                "maintained": "maintained weight"
                            }.get(good_example["action"], good_example["action"])
                            
                            weight_change = good_example.get("weight_change", 0)
                            
                            # Add context about why it was good
                            prev_rpe = prev_session.get("peak_rpe")
                            reasoning = ""
                            if prev_rpe and not pd.isna(prev_rpe):
                                if good_example["action"] == "increased" and prev_rpe <= 7.5:
                                    reasoning = f" (responded to low RPE {prev_rpe:.1f})"
                                elif good_example["action"] == "decreased" and prev_rpe >= 9.5:
                                    reasoning = f" (responded to high RPE {prev_rpe:.1f})"
                                elif good_example["action"] == "maintained" and 7.5 <= prev_rpe <= 9.0:
                                    reasoning = f" (optimal RPE {prev_rpe:.1f})"
                            
                            age_str = "today" if days_ago == 0 else f"{days_ago}d ago"
                            change_str = f" ({weight_change:+.1f}kg)" if abs(weight_change) >= 0.1 else ""
                            print(f"     • {age_str}: {action_desc}{change_str}{reasoning}")
            
            # Enhanced learning insights based on efficiency and RPE patterns
            print(f"   💡 **Key Learning**:", end=" ")
            if efficiency < 30:
                print(f"Strong focus needed on RPE interpretation - review guidelines below")
            elif efficiency < 50:
                print(f"Focus on RPE feedback - aim for peak RPE 8-9 on final sets")
            elif efficiency < 75:
                print(f"Good overall, trust your RPE readings more for weight adjustments")
            else:
                print(f"Excellent RPE-based decisions - keep listening to your body!")
            
            # Add specific recommendations for this exercise
            if data["missed_opportunities"]:
                latest_miss = data["missed_opportunities"][0]
                if "should have increased" in latest_miss["missed_opportunity"]:
                    print(f"   🎯 **Next Session**: If RPE ≤7.5, increase weight ~2-5%")
                elif "should have decreased" in latest_miss["missed_opportunity"]:
                    print(f"   🎯 **Next Session**: If RPE ≥9.5, decrease weight ~2-5%")
                else:
                    print(f"   🎯 **Next Session**: Aim for peak RPE 8-9 on final set")
            else:
                print(f"   🎯 **Next Session**: Continue current approach - it's working well!")
        
        # Enhanced overall evolution insights
        avg_efficiency = sum(data["efficiency_score"] for data in exercise_evolution.values()) / len(exercise_evolution)
        total_decisions = sum(data["total_decisions"] for data in exercise_evolution.values())
        total_missed = sum(len(data["missed_opportunities"]) for data in exercise_evolution.values())
        total_good = sum(len(data["good_decisions"]) for data in exercise_evolution.values())
        
        print(f"\n📊 **Overall Decision Quality Summary**:")
        print(f"• **Average Efficiency**: {avg_efficiency:.0f}% across {len(exercise_evolution)} exercises")
        print(f"• **Total Decisions**: {total_decisions} | Good: {total_good} | Missed: {total_missed}")
        print(f"• **Learning Potential**: {total_missed} decisions to optimize")
        
        if avg_efficiency >= 80:
            print(f"• 🌟 **Assessment**: Excellent RPE awareness - you're making great decisions!")
            print(f"• 🎯 **Focus**: Fine-tune minor details, maintain current approach")
        elif avg_efficiency >= 65:
            print(f"• 🎯 **Assessment**: Good decision making - fine-tune RPE interpretation")
            print(f"• 📈 **Focus**: Pay closer attention to RPE 9+ sessions (reduce weight next time)")
        else:
            print(f"• 📚 **Assessment**: Significant learning opportunity with RPE patterns")
            print(f"• 🔥 **Focus**: RPE 9.5+ = too hard, RPE 7- = too easy")
        
        print(f"\n💡 **Complete RPE Decision Guide**:")
        print(f"• **Peak RPE 6-7**: Too easy → increase weight 2-5% next session")
        print(f"• **Peak RPE 7.5-8.5**: Perfect intensity → maintain or small increase (+1-2%)")
        print(f"• **Peak RPE 9-9.5**: Challenging but good → maintain weight, focus on form")
        print(f"• **Peak RPE 9.5+**: Too hard → decrease weight 2-5% next session")
        print(f"• **Final set RPE 9+**: Excellent progression to failure - ideal training")
    
    # ========================
    # 5. PERIODIZATION & PLATEAU DETECTION
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
        
        # Show smart adjustments as a positive category
        if periodization.get("smart_adjustments"):
            print(f"\n✅ **Smart RPE-Based Adjustments** ({len(periodization['smart_adjustments'])} exercises):")
            for ex in periodization["smart_adjustments"][:5]:
                print(f"• **{ex['name']}**: {ex['decline_pct']:.1f}% decrease (RPE-justified)")
        
        if periodization["plateaued_exercises"]:
            print(f"\n⚠️ **Plateaued Exercises** ({len(periodization['plateaued_exercises'])} exercises):")
            for ex in periodization["plateaued_exercises"][:5]:
                print(f"• **{ex['name']}**: stagnant for {ex['sessions_stagnant']} sessions")
        
        if periodization["deload_candidates"]:
            print(f"\n🔄 **Consider Deload** ({len(periodization['deload_candidates'])} exercises):")
            for ex in periodization["deload_candidates"][:3]:
                print(f"• **{ex}**: reduce weight 10-15% for technique focus")
        
        # Only show actual declining performance (not RPE-justified)
        if periodization["regressing_exercises"]:
            print(f"\n📉 **Concerning Declines** ({len(periodization['regressing_exercises'])} exercises):")
            for ex in periodization["regressing_exercises"][:3]:
                print(f"• **{ex['name']}**: {ex['decline_pct']:.1f}% decline - check form/recovery/nutrition")
    
    # ========================
    # 6. VOLUME & RECOVERY ANALYSIS
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
                print(f"• **{muscle.title()}**: {volume:,.0f}kg total volume")
    
    # ========================
    # 7. PAST 30 DAYS OVERVIEW (CONDENSED)
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
            print(f"• **{exercise}**: {row['total_volume']:,.0f}kg total")
    
    # ========================
    # 8. LAST SESSION DEEP DIVE
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
                rpe_info = f"RPE: {ex['avg_rpe']:.1f}"
                if ex.get("peak_rpe") and not pd.isna(ex["peak_rpe"]):
                    rpe_info += f" (peak: {ex['peak_rpe']:.1f})"
                if ex.get("final_rpe") and not pd.isna(ex["final_rpe"]) and ex["final_rpe"] != ex["peak_rpe"]:
                    rpe_info += f" (final: {ex['final_rpe']:.1f})"
                print(f"   {rpe_info}")
            
            print(f"   Volume: {ex['total_volume']:,.0f}kg")
            print(f"   **{ex['verdict']}** → {ex['suggestion']}")
        
        # Session summary
        in_range = sum(1 for ex in last_session["exercises"] if ex["verdict"] == "✅ in range")
        too_heavy = sum(1 for ex in last_session["exercises"] if ex["verdict"] == "⬇️ too heavy")
        too_light = sum(1 for ex in last_session["exercises"] if ex["verdict"] == "⬆️ too light")
        no_target = sum(1 for ex in last_session["exercises"] if ex["verdict"] == "❓ no target")
        
        session_score = (in_range / len(last_session["exercises"])) * 100 if last_session["exercises"] else 0
    
    # ========================
    # 9. NEXT SESSION RECOMMENDATIONS
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

def main():
    parser = argparse.ArgumentParser(description="Hevy Stats Fetcher & Coach Analysis")
    parser.add_argument("mode", nargs='?', default="both", choices=["fetch", "analyze", "export", "both"], 
                       help="Mode: fetch data from API, analyze existing data, export to CSV, or both fetch+analyze (default: both)")
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