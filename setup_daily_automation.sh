#!/bin/bash

echo "🏋️‍♂️  HEVY DAILY AUTOMATION SETUP"
echo "=================================="

# Get current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "📁 Script location: $SCRIPT_DIR"

# Step 1: Create .env file if it doesn't exist
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo ""
    echo "📝 Creating .env file from example..."
    cp "$SCRIPT_DIR/setup_example.env" "$SCRIPT_DIR/.env"
    echo "✅ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file with your actual credentials!"
    echo "   - Get your Hevy API key from: https://hevy.com/developer"
    echo "   - For Gmail: use an App Password (not your regular password)"
    echo ""
    echo "Would you like to edit .env now? (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        if command -v code &> /dev/null; then
            code "$SCRIPT_DIR/.env"
        elif command -v nano &> /dev/null; then
            nano "$SCRIPT_DIR/.env"
        elif command -v vim &> /dev/null; then
            vim "$SCRIPT_DIR/.env"
        else
            echo "Please edit $SCRIPT_DIR/.env manually"
        fi
    fi
else
    echo "✅ .env file already exists"
fi

echo ""
echo "🔧 AUTOMATION OPTIONS:"
echo "======================"
echo ""
echo "1. 📧 Daily email reports (recommended)"
echo "2. 📋 Daily local reports only"
echo "3. 🗓️  Set up cron job (macOS/Linux)"
echo "4. 🧪 Test current setup"
echo ""
echo "What would you like to set up? (1-4): "
read -r choice

case $choice in
    1)
        echo ""
        echo "📧 Setting up daily email reports..."
        echo ""
        echo "This will:"
        echo "• Fetch latest workout data daily"
        echo "• Generate comprehensive coaching report"
        echo "• Email the report to you"
        echo "• Save markdown and CSV files locally"
        echo ""
        echo "Recommended cron schedule: 8 AM daily"
        echo "Add this to your crontab (run 'crontab -e'):"
        echo ""
        echo "# Hevy Daily Coaching Report (8 AM daily)"
        echo "0 8 * * * cd $SCRIPT_DIR && python3 hevy_stats.py both --email >> hevy_automation.log 2>&1"
        echo ""
        ;;
    2)
        echo ""
        echo "📋 Setting up daily local reports..."
        echo ""
        echo "This will:"
        echo "• Fetch latest workout data daily"
        echo "• Generate comprehensive coaching report"
        echo "• Save markdown and CSV files locally"
        echo "• No email sending"
        echo ""
        echo "Add this to your crontab (run 'crontab -e'):"
        echo ""
        echo "# Hevy Daily Report (8 AM daily)"
        echo "0 8 * * * cd $SCRIPT_DIR && python3 hevy_stats.py both >> hevy_automation.log 2>&1"
        echo ""
        ;;
    3)
        echo ""
        echo "🗓️  Setting up cron job..."
        echo ""
        echo "Choose your preferred time:"
        echo "1. 8:00 AM daily"
        echo "2. 9:00 AM daily"
        echo "3. 7:00 PM daily (after workout)"
        echo "4. Custom time"
        echo ""
        echo "Enter choice (1-4): "
        read -r time_choice
        
        case $time_choice in
            1) cron_time="0 8 * * *" ;;
            2) cron_time="0 9 * * *" ;;
            3) cron_time="0 19 * * *" ;;
            4) 
                echo "Enter custom cron time (e.g., '30 7 * * *' for 7:30 AM): "
                read -r cron_time
                ;;
            *) cron_time="0 8 * * *" ;;
        esac
        
        echo ""
        echo "Would you like email reports? (y/n): "
        read -r email_response
        
        if [[ "$email_response" =~ ^[Yy]$ ]]; then
            cron_command="cd $SCRIPT_DIR && python3 hevy_stats.py both --email >> hevy_automation.log 2>&1"
        else
            cron_command="cd $SCRIPT_DIR && python3 hevy_stats.py both >> hevy_automation.log 2>&1"
        fi
        
        echo ""
        echo "📅 Your cron job:"
        echo "$cron_time $cron_command"
        echo ""
        echo "To install this cron job, run:"
        echo "  crontab -e"
        echo ""
        echo "Then add the above line to your crontab."
        ;;
    4)
        echo ""
        echo "🧪 Testing current setup..."
        echo ""
        
        # Check if .env file has been configured
        if grep -q "your-hevy-api-key-here" "$SCRIPT_DIR/.env" 2>/dev/null; then
            echo "❌ .env file not configured yet"
            echo "   Please edit .env with your actual credentials"
            exit 1
        fi
        
        echo "Testing API connection..."
        cd "$SCRIPT_DIR"
        python3 hevy_stats.py fetch --days 7
        
        if [ $? -eq 0 ]; then
            echo "✅ API connection successful!"
            echo ""
            echo "Testing email configuration..."
            python3 hevy_stats.py --test-email
            
            if [ $? -eq 0 ]; then
                echo "✅ Email configuration successful!"
                echo ""
                echo "Running full test report..."
                python3 hevy_stats.py analyze --email
            else
                echo "⚠️  Email test failed - you can still use local reports"
                echo ""
                echo "Running local report test..."
                python3 hevy_stats.py analyze
            fi
        else
            echo "❌ API test failed - check your HEVY_API_KEY in .env"
        fi
        ;;
    *)
        echo "Invalid choice"
        ;;
esac

echo ""
echo "🎉 Setup complete!"
echo ""
echo "💡 Pro tips:"
echo "• Check hevy_automation.log for any issues"
echo "• Run 'python3 hevy_stats.py --help' to see all options"
echo "• Your reports will be saved as hevy_coaching_report_*.md"
echo "• CSV exports will be saved as hevy_workouts_export_*.csv" 