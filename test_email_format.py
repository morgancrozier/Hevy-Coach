#!/usr/bin/env python3

import sys
import os

# Import the EmailSender class from hevy_stats.py
sys.path.append('.')
from hevy_stats import EmailSender

def test_email_format():
    """Test the email formatting with the latest coaching report."""
    
    # Find the latest coaching report
    import glob
    reports = glob.glob("hevy_coaching_report_*.md")
    if not reports:
        print("❌ No coaching reports found. Run 'python hevy_stats.py analyze --save-markdown' first.")
        return
    
    latest_report = max(reports)
    print(f"📧 Testing email format with: {latest_report}")
    
    # Read the report content
    with open(latest_report, 'r', encoding='utf-8') as f:
        report_content = f.read()
    
    # Create EmailSender instance
    email_sender = EmailSender()
    
    # Convert to HTML
    html_content = email_sender.markdown_to_html(report_content)
    
    # Create test email file
    test_file = "test_email_output.html"
    
    # Create the full HTML structure like in send_report
    full_html = f"""
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
            
            /* AI sections */
            .ai-section {{
                background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%);
                border-left: 4px solid #2196f3;
                padding: 15px;
                margin: 15px 0;
                border-radius: 0 6px 6px 0;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .ai-section h3 {{
                margin-top: 0;
                color: #1976d2;
                font-size: 1.1em;
            }}
            .ai-content {{
                margin: 8px 0;
                line-height: 1.6;
                color: #424242;
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
            
            /* Exercise Analysis */
            .exercise-analysis {{
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                margin: 10px 0;
                padding: 12px;
            }}
            .exercise-analysis h4, h4.exercise-name {{
                margin-top: 0;
                margin-bottom: 8px;
                color: #2c3e50;
                border-bottom: 1px solid #dee2e6;
                padding-bottom: 4px;
            }}
            .exercise-details {{
                font-size: 0.95em;
                line-height: 1.5;
            }}
            
            /* Session data formatting */
            .session-data {{
                margin: 8px 0;
                padding: 8px;
                background: #e9ecef;
                border-radius: 4px;
                font-family: monospace;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            {html_content}
        </div>
    </body>
    </html>
    """
    
    # Save test file
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(full_html)
    
    print(f"✅ Test email HTML generated: {test_file}")
    print(f"🌐 Open {test_file} in your browser to see how the email will look")
    
    # Also test plain text summary
    plain_text = email_sender.create_plain_text_summary(report_content)
    print(f"\n📝 Plain text summary:")
    print("-" * 50)
    print(plain_text)

if __name__ == "__main__":
    test_email_format() 