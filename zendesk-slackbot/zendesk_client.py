import requests
import re
from datetime import datetime, timedelta
from urllib.parse import urlparse
from config import ZENDESK_BASE_URL, ZENDESK_EMAIL, ZENDESK_API_TOKEN

class ZendeskClient:
    def __init__(self):
        self.base_url = ZENDESK_BASE_URL
        self.auth = (f"{ZENDESK_EMAIL}/token", ZENDESK_API_TOKEN)
        self.headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'ZendeskSlackbot/1.0'
        }
    
    def _make_request(self, endpoint, params=None):
        """Make authenticated request to Zendesk API"""
        try:
            url = f"{self.base_url}/{endpoint}"
            response = requests.get(
                url, 
                auth=self.auth, 
                headers=self.headers, 
                params=params,
                timeout=30,
                verify=True
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            # Log safely without exposing sensitive data
            print(f"Error making request to Zendesk API: {type(e).__name__}")
            return None
    
    def _sanitize_email(self, email):
        """Validate and sanitize email address"""
        if not email:
            raise ValueError("Email cannot be empty")
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValueError("Invalid email format")
        
        return email.strip().lower()
    
    def _validate_zendesk_url(self, url):
        """Validate Zendesk URL to prevent SSRF attacks"""
        if not url:
            return None
        
        try:
            parsed = urlparse(url)
            if not parsed.hostname or not parsed.hostname.endswith('.zendesk.com'):
                print("Warning: Invalid Zendesk URL detected")
                return None
            return parsed.hostname
        except Exception:
            print("Warning: Could not parse Zendesk URL")
            return None
    
    def get_user_by_email(self, email):
        """Find user by email address"""
        try:
            sanitized_email = self._sanitize_email(email)
            params = {'query': f'email:{sanitized_email}'}
            result = self._make_request('users/search.json', params)
            
            if result and result.get('count', 0) > 0:
                return result['users'][0]
            return None
        except ValueError as e:
            print(f"Invalid email provided: {type(e).__name__}")
            return None
    
    def get_agent_tickets_last_week(self, agent_email):
        """Get tickets assigned to agent in the last 7 days"""
        user = self.get_user_by_email(agent_email)
        if not user:
            return None
        
        user_id = user['id']
        week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        params = {
            'query': f'assignee:{user_id} created>={week_ago} type:ticket',
            'sort_by': 'created_at',
            'sort_order': 'desc'
        }
        
        result = self._make_request('search.json', params)
        return result.get('results', []) if result else []
    
    def get_ticket_comments(self, ticket_id):
        """Get all comments for a specific ticket"""
        result = self._make_request(f'tickets/{ticket_id}/comments.json')
        return result.get('comments', []) if result else []
    
    def get_agent_performance_metrics(self, agent_email):
        """Get comprehensive performance metrics for an agent"""
        tickets = self.get_agent_tickets_last_week(agent_email)
        if not tickets:
            return None
        
        user = self.get_user_by_email(agent_email)
        if not user:
            return None
        
        user_id = user.get('id')
        
        metrics = {
            'total_tickets': len(tickets),
            'urgent_tickets': [],
            'on_hold_tickets': [],
            'solved_tickets': 0,
            'internal_comments': 0,
            'external_comments': 0,
            'agent_name': user.get('name', 'Unknown'),
            'agent_email': agent_email,
            'old_tickets': [],
            'positive_csat': [],
            'negative_csat': [],
            'sla_breaches': []
        }
        
        # Get additional metrics
        metrics['old_tickets'] = self.get_old_tickets(agent_email)
        metrics['positive_csat'] = self.get_csat_tickets(agent_email, positive=True)
        metrics['negative_csat'] = self.get_csat_tickets(agent_email, positive=False)
        metrics['sla_breaches'] = self.get_sla_breach_tickets(agent_email)
        
        for ticket in tickets:
            # Count solved tickets
            if ticket.get('status') == 'solved':
                metrics['solved_tickets'] += 1
            
            # Track urgent tickets
            if ticket.get('priority') == 'urgent':
                metrics['urgent_tickets'].append({
                    'id': ticket['id'],
                    'subject': ticket.get('subject', 'No subject'),
                    'status': ticket.get('status'),
                    'url': ticket.get('url')
                })
            
            # Track on-hold tickets
            if ticket.get('status') == 'hold':
                metrics['on_hold_tickets'].append({
                    'id': ticket['id'],
                    'subject': ticket.get('subject', 'No subject'),
                    'url': ticket.get('url')
                })
            
            # Count comments (internal vs external)
            comments = self.get_ticket_comments(ticket['id'])
            for comment in comments:
                if comment.get('author_id') == user_id:
                    if comment.get('public', True):
                        metrics['external_comments'] += 1
                    else:
                        metrics['internal_comments'] += 1
        
        return metrics
    
    def get_tickets_by_status(self, agent_email, status):
        """Get tickets by specific status for an agent"""
        user = self.get_user_by_email(agent_email)
        if not user:
            return []
        
        user_id = user.get('id')
        params = {
            'query': f'assignee:{user_id} status:{status} type:ticket'
        }
        
        result = self._make_request('search.json', params)
        return result.get('results', []) if result else []
    
    def get_old_tickets(self, agent_email):
        """Get tickets assigned to agent that are over 2 weeks old"""
        user = self.get_user_by_email(agent_email)
        if not user:
            return []
        
        user_id = user.get('id')
        two_weeks_ago = (datetime.now() - timedelta(days=14)).strftime('%Y-%m-%d')
        
        params = {
            'query': f'assignee:{user_id} created<={two_weeks_ago} type:ticket status<solved status<closed',
            'sort_by': 'created_at',
            'sort_order': 'asc'
        }
        
        result = self._make_request('search.json', params)
        tickets = result.get('results', []) if result else []
        
        old_tickets = []
        for ticket in tickets:
            old_tickets.append({
                'id': ticket['id'],
                'subject': ticket.get('subject', 'No subject'),
                'status': ticket.get('status'),
                'priority': ticket.get('priority'),
                'created_at': ticket.get('created_at'),
                'url': ticket.get('url')
            })
        
        return old_tickets
    
    def get_csat_tickets(self, agent_email, positive=True):
        """Get tickets with CSAT ratings (positive or negative) in the last week"""
        user = self.get_user_by_email(agent_email)
        if not user:
            return []
        
        user_id = user.get('id')
        week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        # Get tickets solved by this agent in the last week
        params = {
            'query': f'assignee:{user_id} updated>={week_ago} status:solved type:ticket',
            'sort_by': 'updated_at',
            'sort_order': 'desc'
        }
        
        result = self._make_request('search.json', params)
        tickets = result.get('results', []) if result else []
        
        csat_tickets = []
        for ticket in tickets:
            # Get satisfaction ratings for this ticket
            satisfaction = self._make_request(f'tickets/{ticket["id"]}/satisfaction_rating.json')
            
            if satisfaction and satisfaction.get('satisfaction_rating'):
                rating = satisfaction['satisfaction_rating']
                score = rating.get('score')
                
                # Determine if this is positive or negative rating
                is_positive = score in ['good', 'great']
                is_negative = score in ['bad', 'not_good']
                
                if (positive and is_positive) or (not positive and is_negative):
                    csat_tickets.append({
                        'id': ticket['id'],
                        'subject': ticket.get('subject', 'No subject'),
                        'score': score,
                        'comment': rating.get('comment', ''),
                        'url': ticket.get('url')
                    })
        
        return csat_tickets
    
    def get_sla_breach_tickets(self, agent_email):
        """Get tickets with SLA breaches for an agent"""
        user = self.get_user_by_email(agent_email)
        if not user:
            return []
        
        user_id = user.get('id')
        week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        # Get tickets assigned to this agent in the last week
        params = {
            'query': f'assignee:{user_id} updated>={week_ago} type:ticket',
            'sort_by': 'updated_at',
            'sort_order': 'desc'
        }
        
        result = self._make_request('search.json', params)
        tickets = result.get('results', []) if result else []
        
        breach_tickets = []
        for ticket in tickets:
            # Get SLA policy information for this ticket
            sla_policies = self._make_request(f'tickets/{ticket["id"]}/sla_policies.json')
            
            if sla_policies and sla_policies.get('sla_policies'):
                for policy in sla_policies['sla_policies']:
                    policy_metrics = policy.get('policy_metrics', [])
                    
                    for metric in policy_metrics:
                        if metric.get('breach') and metric.get('business_hours') is not None:
                            # Calculate breach time
                            breach_time = metric.get('business_hours', 0)
                            breach_minutes = int(breach_time / 60) if breach_time else 0
                            
                            breach_tickets.append({
                                'id': ticket['id'],
                                'subject': ticket.get('subject', 'No subject'),
                                'metric': metric.get('metric'),
                                'breach_minutes': breach_minutes,
                                'breach_hours': round(breach_minutes / 60, 1) if breach_minutes > 60 else 0,
                                'url': ticket.get('url')
                            })
                            break  # Only report first breach per ticket
        
        return breach_tickets