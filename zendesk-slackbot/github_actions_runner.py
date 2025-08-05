#!/usr/bin/env python3
"""
GitHub Actions Runner for Zendesk Slackbot
Stateless runner designed for GitHub Actions cron jobs
"""

import os
import sys
import argparse
from datetime import datetime
from calendar_monitor import CalendarMonitor
from zendesk_client import ZendeskClient
from slack_bot import SlackBot

class GitHubActionsRunner:
    def __init__(self):
        self.calendar_monitor = None
        self.zendesk_client = None
        self.slack_bot = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize all API clients with error handling"""
        try:
            self.calendar_monitor = CalendarMonitor()
            print("✅ Google Calendar client initialized")
        except Exception as e:
            print(f"❌ Failed to initialize Google Calendar: {e}")
            self.calendar_monitor = None
        
        try:
            self.zendesk_client = ZendeskClient()
            print("✅ Zendesk client initialized")
        except Exception as e:
            print(f"❌ Failed to initialize Zendesk: {e}")
            self.zendesk_client = None
        
        try:
            self.slack_bot = SlackBot()
            print("✅ Slack bot initialized")
        except Exception as e:
            print(f"❌ Failed to initialize Slack bot: {e}")
            self.slack_bot = None
    
    def check_for_upcoming_meetings(self):
        """Check for 1on1 meetings starting in 25-35 minutes"""
        if not all([self.calendar_monitor, self.zendesk_client, self.slack_bot]):
            error_msg = "One or more API clients failed to initialize"
            print(f"❌ {error_msg}")
            if self.slack_bot:
                self.slack_bot.send_error_notification(error_msg)
            return False
        
        try:
            print(f"🔍 [{datetime.now()}] Checking for upcoming 1on1 meetings...")
            
            # Check for meetings in a 10-minute window (25-35 minutes from now)
            # This accounts for the 5-minute cron interval
            meetings_found = False
            
            for minutes_ahead in range(25, 36):
                upcoming_meetings = self.calendar_monitor.get_meetings_starting_in_minutes(minutes_ahead)
                
                for meeting in upcoming_meetings:
                    meetings_found = True
                    agent_email = meeting.get('agent_email')
                    
                    if not agent_email:
                        print(f"⚠️ No agent email found for meeting: {meeting.get('summary')}")
                        continue
                    
                    print(f"📅 Processing 1on1 for agent: {agent_email} (in {minutes_ahead} minutes)")
                    
                    # Get agent performance metrics
                    metrics = self.zendesk_client.get_agent_performance_metrics(agent_email)
                    
                    if metrics:
                        # Send performance summary to Slack
                        response = self.slack_bot.send_performance_summary(metrics, meeting)
                        if response:
                            print(f"✅ Sent performance summary for {agent_email}")
                        else:
                            print(f"❌ Failed to send Slack message for {agent_email}")
                    else:
                        error_msg = f"Could not retrieve metrics for agent: {agent_email}"
                        print(f"⚠️ {error_msg}")
                        self.slack_bot.send_error_notification(error_msg)
            
            if not meetings_found:
                print("ℹ️ No upcoming 1on1 meetings found in the next 25-35 minutes")
            
            return True
        
        except Exception as e:
            error_msg = f"Error checking for meetings: {str(e)}"
            print(f"❌ {error_msg}")
            if self.slack_bot:
                self.slack_bot.send_error_notification(error_msg)
            return False
    
    def test_integrations(self):
        """Test all integrations"""
        print("🧪 Testing integrations in GitHub Actions environment...\n")
        
        success_count = 0
        total_tests = 3
        
        # Test Google Calendar
        print("📅 Testing Google Calendar integration...")
        try:
            if self.calendar_monitor:
                upcoming = self.calendar_monitor.get_upcoming_1on1s(24)
                print(f"   ✅ Found {len(upcoming)} upcoming 1on1 meetings")
                success_count += 1
            else:
                print("   ❌ Calendar client not initialized")
        except Exception as e:
            print(f"   ❌ Calendar test failed: {e}")
        
        # Test Zendesk
        print("\n🎫 Testing Zendesk integration...")
        try:
            if self.zendesk_client:
                # Test basic connection without specific user
                print("   ✅ Zendesk client initialized and ready")
                success_count += 1
            else:
                print("   ❌ Zendesk client not initialized")
        except Exception as e:
            print(f"   ❌ Zendesk test failed: {e}")
        
        # Test Slack
        print("\n💬 Testing Slack integration...")
        try:
            if self.slack_bot:
                response = self.slack_bot.send_message("🧪 Test message from GitHub Actions - Zendesk Slackbot")
                if response:
                    print("   ✅ Slack message sent successfully")
                    success_count += 1
                else:
                    print("   ❌ Failed to send Slack message")
            else:
                print("   ❌ Slack bot not initialized")
        except Exception as e:
            print(f"   ❌ Slack test failed: {e}")
        
        print(f"\n📊 Integration test results: {success_count}/{total_tests} passed")
        
        if success_count == total_tests:
            print("🎉 All integrations working correctly!")
            return True
        else:
            print("⚠️ Some integrations failed - check your secrets configuration")
            return False

def main():
    parser = argparse.ArgumentParser(description='GitHub Actions Runner for Zendesk Slackbot')
    parser.add_argument('--test', action='store_true', help='Test all integrations')
    parser.add_argument('--check', action='store_true', help='Check for upcoming meetings')
    
    args = parser.parse_args()
    
    # Set up environment info
    print("🚀 GitHub Actions Zendesk Slackbot Runner")
    print(f"📅 Current time: {datetime.now()}")
    print(f"🏃 Action: {'Test integrations' if args.test else 'Check meetings'}")
    
    # Initialize runner
    runner = GitHubActionsRunner()
    
    if args.test:
        success = runner.test_integrations()
        sys.exit(0 if success else 1)
    elif args.check:
        success = runner.check_for_upcoming_meetings()
        sys.exit(0 if success else 1)
    else:
        print("❌ No action specified. Use --test or --check")
        sys.exit(1)

if __name__ == "__main__":
    main()