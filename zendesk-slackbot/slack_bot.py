import re
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from config import SLACK_BOT_TOKEN, SLACK_CHANNEL_ID

class SlackBot:
    def __init__(self):
        self.client = WebClient(token=SLACK_BOT_TOKEN)
        self.channel_id = SLACK_CHANNEL_ID
    
    def send_performance_summary(self, metrics, meeting_info):
        """Send agent performance summary to Slack"""
        if not metrics:
            self.send_message("❌ Unable to retrieve performance metrics for the upcoming 1on1.")
            return
        
        # Format the performance summary
        message = self._format_performance_message(metrics, meeting_info)
        
        try:
            response = self.client.chat_postMessage(
                channel=self.channel_id,
                text=message,
                parse='full'
            )
            return response
        except SlackApiError as e:
            print(f"Error sending message: {e.response['error']}")
            return None
    
    def _sanitize_slack_content(self, content):
        """Sanitize content for Slack to prevent information leakage"""
        if not content:
            return content
            
        # Remove email addresses
        content = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', content)
        # Remove IP addresses
        content = re.sub(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', '[IP]', content)
        # Limit length to prevent data exposure
        if len(content) > 200:
            content = content[:197] + "..."
        return content
    
    def _build_secure_zendesk_url(self, ticket):
        """Build Zendesk URL with validation"""
        try:
            ticket_id = ticket.get('id')
            ticket_url = ticket.get('url', '')
            
            if not ticket_id or not ticket_url:
                return None
                
            # Validate that URL is from Zendesk
            if '.zendesk.com' not in ticket_url:
                return None
                
            # Extract subdomain safely
            parts = ticket_url.split('/')
            if len(parts) >= 3:
                hostname = parts[2]
                if hostname.endswith('.zendesk.com'):
                    return f"https://{hostname}/agent/tickets/{ticket_id}"
            
            return None
        except Exception:
            return None
    
    def _format_performance_message(self, metrics, meeting_info):
        """Format the performance metrics into a readable Slack message"""
        agent_name = self._sanitize_slack_content(metrics.get('agent_name', 'Unknown Agent'))
        meeting_time = meeting_info.get('start_time', 'Unknown time')
        
        message = f"""
🎯 **1on1 Performance Summary**
👤 **Agent:** {agent_name}
📅 **Meeting:** {meeting_time}

📊 **Last Week Performance:**
• 📋 Total Tickets: {metrics['total_tickets']}
• ✅ Solved Tickets: {metrics['solved_tickets']}
• 💬 Internal Comments: {metrics['internal_comments']}
• 🗣️ External Comments: {metrics['external_comments']}

🚨 **Urgent Tickets ({len(metrics['urgent_tickets'])}):**
"""
        
        if metrics['urgent_tickets']:
            for ticket in metrics['urgent_tickets']:
                status_emoji = "🔴" if ticket['status'] != 'solved' else "✅"
                message += f"   {status_emoji} #{ticket['id']}: {ticket['subject'][:50]}... (Status: {ticket['status']})\n"
        else:
            message += "   ✨ No urgent tickets\n"
        
        message += f"\n⏸️ **On-Hold Tickets ({len(metrics['on_hold_tickets'])}):**\n"
        
        if metrics['on_hold_tickets']:
            for ticket in metrics['on_hold_tickets']:
                zendesk_url = self._build_secure_zendesk_url(ticket)
                subject = self._sanitize_slack_content(ticket.get('subject', 'No subject'))
                if zendesk_url:
                    message += f"   ⏸️ [#{ticket['id']}: {subject[:40]}...]({zendesk_url})\n"
                else:
                    message += f"   ⏸️ #{ticket['id']}: {subject[:40]}...\n"
        else:
            message += "   ✨ No tickets on hold\n"
        
        # Add old tickets section
        message += f"\n📅 **Old Tickets - Over 2 Weeks ({len(metrics.get('old_tickets', []))}):**\n"
        
        if metrics.get('old_tickets'):
            for ticket in metrics['old_tickets'][:5]:  # Limit to first 5
                priority_emoji = "🔴" if ticket.get('priority') == 'urgent' else "🟡" if ticket.get('priority') == 'high' else "⚪"
                zendesk_url = self._build_secure_zendesk_url(ticket)
                subject = self._sanitize_slack_content(ticket.get('subject', 'No subject'))
                if zendesk_url:
                    message += f"   {priority_emoji} [#{ticket['id']}: {subject[:40]}...]({zendesk_url}) - {ticket.get('status', 'unknown')} priority\n"
                else:
                    message += f"   {priority_emoji} #{ticket['id']}: {subject[:40]}... - {ticket.get('status', 'unknown')} priority\n"
            
            if len(metrics.get('old_tickets', [])) > 5:
                message += f"   ... and {len(metrics['old_tickets']) - 5} more\n"
        else:
            message += "   ✨ No old tickets\n"
        
        # Add CSAT sections
        message += f"\n😊 **Positive CSAT Feedback ({len(metrics.get('positive_csat', []))}):**\n"
        
        if metrics.get('positive_csat'):
            for ticket in metrics['positive_csat'][:3]:  # Limit to first 3
                score_emoji = "⭐" if ticket.get('score') == 'great' else "👍"
                zendesk_url = self._build_secure_zendesk_url(ticket)
                subject = self._sanitize_slack_content(ticket.get('subject', 'No subject'))
                comment = self._sanitize_slack_content(ticket.get('comment', ''))
                comment_preview = comment[:30] + "..." if len(comment) > 30 else comment
                if zendesk_url:
                    message += f"   {score_emoji} [#{ticket['id']}: {subject[:30]}...]({zendesk_url})\n"
                else:
                    message += f"   {score_emoji} #{ticket['id']}: {subject[:30]}...\n"
                if comment_preview:
                    message += f"      💬 \"{comment_preview}\"\n"
            
            if len(metrics.get('positive_csat', [])) > 3:
                message += f"   ... and {len(metrics['positive_csat']) - 3} more positive ratings\n"
        else:
            message += "   📝 No positive CSAT ratings this week\n"
        
        message += f"\n😔 **Negative CSAT Feedback ({len(metrics.get('negative_csat', []))}):**\n"
        
        if metrics.get('negative_csat'):
            for ticket in metrics['negative_csat'][:3]:  # Limit to first 3
                score_emoji = "👎" if ticket.get('score') == 'bad' else "😐"
                zendesk_url = self._build_secure_zendesk_url(ticket)
                subject = self._sanitize_slack_content(ticket.get('subject', 'No subject'))
                comment = self._sanitize_slack_content(ticket.get('comment', ''))
                comment_preview = comment[:30] + "..." if len(comment) > 30 else comment
                if zendesk_url:
                    message += f"   {score_emoji} [#{ticket['id']}: {subject[:30]}...]({zendesk_url})\n"
                else:
                    message += f"   {score_emoji} #{ticket['id']}: {subject[:30]}...\n"
                if comment_preview:
                    message += f"      💬 \"{comment_preview}\"\n"
            
            if len(metrics.get('negative_csat', [])) > 3:
                message += f"   ... and {len(metrics['negative_csat']) - 3} more negative ratings\n"
        else:
            message += "   ✨ No negative CSAT ratings this week\n"
        
        # Add SLA breach section
        message += f"\n⏰ **SLA Breaches ({len(metrics.get('sla_breaches', []))}):**\n"
        
        if metrics.get('sla_breaches'):
            for ticket in metrics['sla_breaches'][:5]:  # Limit to first 5
                zendesk_url = self._build_secure_zendesk_url(ticket)
                subject = self._sanitize_slack_content(ticket.get('subject', 'No subject'))
                breach_time = f"{ticket.get('breach_hours', 0)}h" if ticket.get('breach_hours', 0) > 0 else f"{ticket.get('breach_minutes', 0)}m"
                if zendesk_url:
                    message += f"   ⏰ [#{ticket['id']}: {subject[:30]}...]({zendesk_url}) - {breach_time} over SLA\n"
                else:
                    message += f"   ⏰ #{ticket['id']}: {subject[:30]}... - {breach_time} over SLA\n"
            
            if len(metrics.get('sla_breaches', [])) > 5:
                message += f"   ... and {len(metrics['sla_breaches']) - 5} more breaches\n"
        else:
            message += "   ✨ No SLA breaches\n"
        
        message += "\n💡 **Discussion Points:**\n"
        
        # Add discussion points based on metrics
        if metrics['total_tickets'] == 0:
            message += "• 🤔 No tickets assigned last week - discuss workload distribution\n"
        elif metrics['solved_tickets'] / metrics['total_tickets'] < 0.7:
            message += "• 📈 Ticket resolution rate could be improved\n"
        
        if len(metrics['urgent_tickets']) > 3:
            message += "• 🚨 High number of urgent tickets - discuss prioritization\n"
        
        if len(metrics['on_hold_tickets']) > 0:
            message += "• ⏸️ Review on-hold tickets and next steps\n"
        
        if len(metrics.get('old_tickets', [])) > 0:
            message += "• 📅 Address aging tickets - consider escalation or closure\n"
        
        if len(metrics.get('negative_csat', [])) > 0:
            message += "• 😔 Review negative feedback and improvement opportunities\n"
        
        if len(metrics.get('sla_breaches', [])) > 0:
            message += "• ⏰ Discuss SLA breach prevention strategies\n"
        
        if metrics['internal_comments'] > metrics['external_comments'] * 2:
            message += "• 💭 High internal comment ratio - review communication efficiency\n"
        
        return message
    
    def send_message(self, message):
        """Send a simple message to Slack"""
        try:
            response = self.client.chat_postMessage(
                channel=self.channel_id,
                text=message
            )
            return response
        except SlackApiError as e:
            print(f"Error sending message: {e.response['error']}")
            return None
    
    def send_error_notification(self, error_message):
        """Send error notification to Slack"""
        message = f"❌ **Zendesk Slackbot Error**\n```{error_message}```"
        return self.send_message(message)