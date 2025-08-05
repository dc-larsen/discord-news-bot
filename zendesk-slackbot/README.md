# Zendesk Slackbot for 1on1 Performance Reports

[![Deploy to GitHub Actions](https://img.shields.io/badge/Deploy%20to-GitHub%20Actions-2088FF?style=for-the-badge&logo=github-actions&logoColor=white)](../../generate)
[![Security](https://img.shields.io/badge/Security-Enterprise%20Ready-green?style=for-the-badge&logo=shield&logoColor=white)](#security)
[![Free Tier](https://img.shields.io/badge/GitHub%20Actions-Free%20Tier-blue?style=for-the-badge&logo=github&logoColor=white)](#architecture)

> **Automatically sends customer support agent performance summaries to Slack 30 minutes before scheduled 1on1 meetings.**

![Slack Bot Demo](https://img.shields.io/badge/📱%20Slack-Integration-4A154B?style=for-the-badge&logo=slack&logoColor=white)
![Zendesk Integration](https://img.shields.io/badge/🎫%20Zendesk-API%20Integration-03363D?style=for-the-badge&logo=zendesk&logoColor=white)
![Google Calendar](https://img.shields.io/badge/📅%20Google-Calendar%20API-4285F4?style=for-the-badge&logo=google-calendar&logoColor=white)

## Features

- 📅 **Google Calendar Integration**: Monitors calendar events with "1on1" in the title
- 🎫 **Zendesk Analytics**: Retrieves comprehensive agent performance metrics
- 💬 **Slack Notifications**: Sends formatted performance summaries to managers
- ⏰ **Automated Scheduling**: Triggers notifications 30 minutes before meetings
- 📊 **Performance Metrics**:
  - Total tickets handled in the last week
  - Number of solved tickets  
  - Internal vs external comment counts
  - Urgent ticket status and details
  - On-hold tickets with direct links
  - **New:** Tickets over 2 weeks old with status and priority
  - **New:** Positive CSAT ratings with customer feedback
  - **New:** Negative CSAT ratings with feedback for improvement
  - **New:** SLA breach tickets with time overages

## 🚀 Quick Setup Guide (Beginner-Friendly)

This bot runs automatically on GitHub Actions - no servers or infrastructure needed! Follow these steps to get it running in about 15 minutes.

> **New to GitHub Actions?** No problem! This guide is designed for complete beginners.

### Step 1: Get the Code

**🎯 Use This Template (Easiest)**
1. Click the green **"Use this template"** button at the top of this page
2. Name your repository (e.g., "my-zendesk-slackbot")
3. Make sure it's set to **Public** (required for GitHub Actions free tier)
4. Click **"Create repository from template"**

**Or Fork This Repository**
1. Click the "Fork" button at the top of this GitHub page
2. This creates your own copy of the bot

### Step 2: Set Up API Access

You'll need to get API keys from three services. Don't worry - they're all free!

#### 2.1 Slack Bot Setup (5 minutes)

1. Go to https://api.slack.com/apps
2. Click **"Create New App"** → **"From scratch"**
3. Name it "1on1 Performance Bot" and select your workspace
4. Go to **"OAuth & Permissions"** in the left sidebar
5. Scroll down to **"Bot Token Scopes"** and add:
   - `chat:write` (to send messages)
   - `channels:read` (to access channels)
6. Click **"Install to Workspace"** at the top
7. Copy the **"Bot User OAuth Token"** (starts with `xoxb-`)
8. Get your channel ID:
   - Right-click on your target Slack channel → "Copy link"
   - The ID is the part after `/channels/` (looks like `C1234567890`)

#### 2.2 Zendesk API Setup (3 minutes)

1. Go to your Zendesk Admin Center
2. Navigate to **Apps and integrations** → **APIs** → **Zendesk API**
3. Enable **"Token Access"**
4. Click **"Add API token"**
5. Give it a name like "1on1 Bot" and copy the token
6. Note your Zendesk subdomain (e.g., if your URL is `company.zendesk.com`, the subdomain is `company`)

#### 2.3 Google Calendar API Setup (7 minutes)

1. Go to https://console.cloud.google.com/
2. Click **"Create Project"** (top dropdown) or select existing project
3. Name it something like "Zendesk Slackbot"
4. Go to **"APIs & Services"** → **"Library"**
5. Search for **"Google Calendar API"** and click **"Enable"**
6. Go to **"APIs & Services"** → **"Credentials"**
7. Click **"Create Credentials"** → **"OAuth client ID"**
8. Choose **"Desktop application"**
9. Download the JSON file
10. **Important**: Base64 encode the file:
    ```bash
    # Mac/Linux:
    base64 -i credentials.json | pbcopy
    
    # Windows (PowerShell):
    [Convert]::ToBase64String([IO.File]::ReadAllBytes("credentials.json")) | Set-Clipboard
    
    # Or use an online base64 encoder and paste the JSON content
    ```

### Step 3: Add Secrets to GitHub

1. Go to your GitHub repository
2. Click **"Settings"** tab (next to "Code")
3. Click **"Secrets and variables"** → **"Actions"** in the left sidebar
4. Click **"New repository secret"** and add each of these:

| Secret Name | Value | Example |
|-------------|-------|---------|
| `SLACK_BOT_TOKEN` | Your Slack bot token | `xoxb-1234567890-abcdefghijk` |
| `SLACK_CHANNEL_ID` | Your Slack channel ID | `C1234567890` |
| `ZENDESK_SUBDOMAIN` | Your Zendesk subdomain | `mycompany` |
| `ZENDESK_EMAIL` | Your Zendesk admin email | `admin@company.com` |
| `ZENDESK_API_TOKEN` | Your Zendesk API token | `abc123def456` |
| `GOOGLE_CREDENTIALS_JSON` | Base64 encoded credentials | `eyJ0eXBlIjoic2Vydmlj...` |

### Step 4: Test the Setup

1. Go to **"Actions"** tab in your repository
2. Click **"Monitor 1on1 Meetings"** workflow
3. Click **"Run workflow"** button
4. Check **"Run in test mode"** ✅
5. Click **"Run workflow"**
6. Wait 1-2 minutes and check:
   - The workflow shows green checkmarks
   - You get a test message in your Slack channel

### Step 5: You're Done! 🎉

The bot now runs automatically:
- **Every 5 minutes** during business hours (9 AM - 6 PM UTC)
- **Monday through Friday**
- Sends performance summaries **30 minutes before** any calendar event with "1on1" in the title

## 📅 How to Use

1. **Schedule 1on1 meetings** in Google Calendar with "1on1" in the title
2. **Include the agent as an attendee** (their email must match their Zendesk email)
3. **30 minutes before the meeting**, you'll get a Slack message with:
   - Last week's ticket performance
   - Urgent ticket status
   - CSAT feedback (positive and negative)
   - SLA breach information
   - Tickets over 2 weeks old
   - Discussion points for the meeting

## 🔧 Customization

Want to change when the bot runs? Edit `.github/workflows/meeting-monitor.yml`:

```yaml
# Current: Every 5 minutes, 9 AM - 6 PM UTC, Monday-Friday
- cron: '*/5 9-18 * * 1-5'

# Examples:
- cron: '*/10 8-17 * * 1-5'  # Every 10 minutes, 8 AM - 5 PM UTC
- cron: '*/5 * * * *'         # Every 5 minutes, 24/7
```

## 🐛 Troubleshooting

### "No upcoming meetings found"
- Check that calendar events have "1on1" in the title
- Verify agent email in calendar matches their Zendesk email
- Ensure the manager's calendar is being monitored

### "Error making request to Zendesk API"
- Verify Zendesk API token and email are correct
- Check that the email has admin permissions in Zendesk
- Confirm the subdomain is correct (no `.zendesk.com` suffix)

### "Error sending message"
- Verify Slack bot token starts with `xoxb-`
- Check that the bot is added to the target channel
- Ensure bot has `chat:write` permissions

### "Could not authenticate with Google"
- Re-check that credentials are properly base64 encoded
- Verify Calendar API is enabled in Google Cloud Console
- The first run might fail - OAuth tokens are cached after successful auth

## 💬 Getting Help

1. Check the **Actions** tab for detailed error logs
2. Look for error messages in your Slack channel
3. Review the troubleshooting section above
4. Create an issue in this repository with error details

## ⭐ Show Your Support

If this bot helps improve your 1on1 meetings, please:
- ⭐ **Star this repository**
- 🍴 **Share it with your team**
- 🐛 **Report issues** to help improve it
- 💡 **Contribute** new features

## 🤝 Contributing

We welcome contributions! See our [Contributing Guide](CONTRIBUTING.md) for details on:
- 🐛 Bug fixes and improvements
- ✨ New features and integrations  
- 📚 Documentation improvements
- 🔒 Security enhancements

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 📊 Performance Data Included

Each report includes comprehensive metrics for data-driven 1on1 discussions:

**📋 Ticket Analytics (Last 7 Days)**
- Total tickets assigned and solved
- Internal vs external comment counts
- Resolution rate analysis

**🚨 Priority & Status Tracking**
- Urgent tickets with current status
- On-hold tickets with direct links
- Tickets over 2 weeks old (priority flagged)

**😊 Customer Satisfaction (CSAT)**
- Positive ratings with customer feedback quotes
- Negative ratings for improvement opportunities
- Direct links to all CSAT tickets

**⏰ SLA Performance**
- Breached SLA tickets with time overages
- Direct links for investigation
- Discussion points for prevention

## Sample Slack Message

```
🎯 1on1 Performance Summary
👤 Agent: John Doe
📅 Meeting: 2024-01-15T14:00:00Z

📊 Last Week Performance:
• 📋 Total Tickets: 25
• ✅ Solved Tickets: 20
• 💬 Internal Comments: 15
• 🗣️ External Comments: 45

🚨 Urgent Tickets (2):
   🔴 #12345: Customer login issues... (Status: open)
   ✅ #12346: Payment processing error... (Status: solved)

⏸️ On-Hold Tickets (1):
   ⏸️ [#12347: Integration setup request...](https://company.zendesk.com/tickets/12347)

📅 Old Tickets - Over 2 Weeks (3):
   🔴 [#12340: Legacy system migration...](https://company.zendesk.com/tickets/12340) - open priority
   🟡 [#12341: Database optimization...](https://company.zendesk.com/tickets/12341) - high priority

😊 Positive CSAT Feedback (2):
   ⭐ [#12350: Setup assistance...](https://company.zendesk.com/tickets/12350)
      💬 "Excellent support, very helpful!"

😔 Negative CSAT Feedback (1):
   👎 [#12348: Billing inquiry...](https://company.zendesk.com/tickets/12348)
      💬 "Response was slow..."

⏰ SLA Breaches (2):
   ⏰ [#12349: Critical system down...](https://company.zendesk.com/tickets/12349) - 2.5h over SLA

💡 Discussion Points:
• 📅 Address aging tickets - consider escalation or closure
• 😔 Review negative feedback and improvement opportunities
• ⏰ Discuss SLA breach prevention strategies
```

## 📁 File Structure

```
zendesk-slackbot/
├── github_actions_runner.py     # Main GitHub Actions entry point
├── calendar_monitor.py          # Google Calendar integration
├── zendesk_client.py           # Zendesk API client
├── slack_bot.py                # Slack messaging
├── config.py                   # Configuration management
├── requirements.txt            # Python dependencies
├── .env.example               # Environment template for local testing
├── .gitignore                 # Git ignore rules
├── README.md                  # This file
├── SECURITY.md               # Security policy and guidelines
├── CONTRIBUTING.md           # Contribution guidelines
├── LICENSE                   # MIT License
└── .github/
    └── workflows/
        ├── meeting-monitor.yml    # Main monitoring workflow
        └── test-integrations.yml  # Integration testing workflow
```

## 🏗️ Architecture

This bot runs entirely on **GitHub Actions** with these benefits:
- ✅ **Zero Infrastructure**: No servers or hosting costs
- ✅ **Enterprise Ready**: Built-in security and compliance features  
- ✅ **Free Tier**: 2,000 minutes/month (more than enough)
- ✅ **Reliable**: GitHub's infrastructure handles uptime
- ✅ **Scalable**: Automatic error handling and notifications

### How It Works
1. **GitHub Actions runs every 5 minutes** during business hours
2. **Checks Google Calendar** for 1on1 meetings starting in 25-35 minutes  
3. **Pulls Zendesk metrics** for the meeting attendee (agent)
4. **Sends formatted report** to Slack with performance insights
5. **Caches OAuth tokens** securely between runs

## Troubleshooting

### Common Issues

1. **Google Calendar Authentication**: Run the script interactively first to complete OAuth flow
2. **Slack Permissions**: Ensure bot has `chat:write` permission for target channel
3. **Zendesk Rate Limits**: Built-in error handling for API limits
4. **Agent Email Matching**: Ensure calendar attendee emails match Zendesk user emails

### Debug Mode
Run with `--check` flag to test without waiting for scheduled meetings:
```bash
python main.py --check
```

## Security

### 🔒 Enterprise Security Features

This application implements comprehensive security measures suitable for enterprise environments:

#### **Credential Protection**
- ✅ Environment variable-based secrets management
- ✅ No hardcoded credentials or API keys
- ✅ Secure credential file handling in CI/CD
- ✅ Automatic cleanup of temporary credential files

#### **Input Validation & Sanitization**
- ✅ Email address validation and sanitization
- ✅ URL validation to prevent SSRF attacks
- ✅ Content sanitization for Slack messages
- ✅ API parameter validation

#### **Network Security**
- ✅ HTTPS-only communication
- ✅ SSL certificate verification
- ✅ Request timeouts to prevent hangs
- ✅ Zendesk domain validation

#### **Data Protection**
- ✅ Sensitive data filtering in logs
- ✅ PII sanitization in Slack messages
- ✅ Limited data exposure in error messages
- ✅ Secure OAuth token caching

### 🚨 Security Requirements

#### **GitHub Actions Secrets**
When setting up repository secrets, ensure:

1. **Base64 Encode Google Credentials**:
   ```bash
   base64 -i credentials.json | pbcopy
   # Paste the result as GOOGLE_CREDENTIALS_JSON secret
   ```

2. **Use Least-Privilege Tokens**:
   - **Slack**: Only `chat:write` and `channels:read` scopes
   - **Zendesk**: Read-only API access for tickets and users
   - **Google**: Calendar read-only access

3. **Regular Token Rotation**:
   - Rotate API tokens quarterly
   - Monitor access logs for anomalies
   - Revoke unused tokens immediately

#### **Network Security**
- Deploy behind corporate firewall if required
- Use VPN for additional access control
- Monitor outbound connections to third-party APIs
- Consider API gateway for request filtering

#### **Compliance Considerations**
- **GDPR**: Agent emails and customer data are processed
- **SOC 2**: Audit logging and access controls implemented
- **HIPAA**: Additional encryption may be required for healthcare
- **PCI DSS**: No payment data is processed

### 🛡️ Security Best Practices

#### **For GitHub Actions Deployment**

1. **Enable Security Features**:
   ```yaml
   # In repository settings
   - Enable "Restrict pushes that create files"
   - Enable "Require signed commits"
   - Enable "Include administrators" for branch protection
   - Enable Dependabot alerts and security updates
   ```

2. **Monitor Actions Usage**:
   - Review workflow run logs regularly
   - Set up alerts for failed security checks
   - Monitor API rate limits and usage

3. **Secret Management**:
   - Never log secrets or environment variables
   - Use short-lived tokens when possible
   - Implement secret scanning in repositories

#### **For Self-Hosted Deployment**

1. **Infrastructure Security**:
   ```bash
   # Use dedicated service account
   sudo useradd -r -s /bin/false zendesk-slackbot
   
   # Secure file permissions
   chmod 600 .env
   chown zendesk-slackbot:zendesk-slackbot .env
   
   # Use systemd hardening
   [Service]
   User=zendesk-slackbot
   NoNewPrivileges=yes
   ProtectSystem=strict
   ProtectHome=yes
   ```

2. **Network Controls**:
   - Firewall rules for outbound connections only
   - VPN access for management
   - Regular security updates

3. **Monitoring & Logging**:
   ```python
   # Enable secure logging
   import logging
   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s - %(name)s - %(levelname)s - [REDACTED]',
       handlers=[
           logging.FileHandler('/var/log/zendesk-slackbot.log'),
           logging.StreamHandler()
       ]
   )
   ```

### 🔍 Security Monitoring

#### **Key Metrics to Monitor**
- Failed authentication attempts
- Unusual API usage patterns  
- Error rates and types
- Response times and timeouts
- Certificate expiration dates

#### **Alerting Setup**
```yaml
# Example GitHub Actions monitoring
- name: Security Alert
  if: failure()
  uses: 8398a7/action-slack@v3
  with:
    status: failure
    text: "🚨 Security incident detected in Zendesk Slackbot"
```

### 🚨 Incident Response

#### **In Case of Security Incident**

1. **Immediate Actions**:
   - Disable GitHub Actions workflows
   - Rotate all API tokens immediately
   - Review access logs for compromise
   - Notify security team

2. **Investigation**:
   - Collect logs from all systems
   - Check for data exfiltration
   - Review recent code changes
   - Audit user access

3. **Recovery**:
   - Deploy patched version
   - Update security controls
   - Document lessons learned
   - Update incident response plan

### 📋 Security Checklist

Before deploying to production:

- [ ] All secrets stored in GitHub repository secrets
- [ ] Google credentials base64 encoded
- [ ] API tokens use least-privilege access
- [ ] Webhook URLs verified and secured
- [ ] Security scanning enabled (Dependabot, CodeQL)
- [ ] Access logging configured
- [ ] Incident response plan documented
- [ ] Regular security review scheduled
- [ ] Compliance requirements verified
- [ ] Backup and recovery procedures tested

### 🔗 Additional Resources

- [GitHub Actions Security Hardening](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [Slack Security Best Practices](https://slack.com/help/articles/115005265063-Best-practices-for-app-security)
- [Zendesk API Security](https://developer.zendesk.com/documentation/core_concepts/security/)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request