# Contributing to Zendesk Slackbot

Thank you for your interest in contributing! This project welcomes contributions from developers of all skill levels.

## 🚀 Quick Start for Contributors

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**
4. **Test your changes** (see Testing section below)
5. **Commit your changes**: `git commit -m 'Add amazing feature'`
6. **Push to the branch**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**

## 🧪 Testing Your Changes

Since this bot integrates with external APIs, testing can be tricky. Here's how to test safely:

### Local Testing
```bash
# Copy environment template
cp .env.example .env

# Add your test credentials (use sandbox/test accounts)
# Edit .env with your test API keys

# Install dependencies
pip install -r requirements.txt

# Test individual components
python -c "from config import *; print('Config loaded successfully')"
python -c "from github_actions_runner import GitHubActionsRunner; GitHubActionsRunner().test_integrations()"
```

### Integration Testing
- Use **test Slack workspaces** and **sandbox Zendesk instances**
- Never test with production data
- Test the GitHub Actions workflow in your fork before submitting

## 📝 Types of Contributions Welcome

### 🐛 Bug Fixes
- API integration issues
- GitHub Actions workflow problems
- Security vulnerabilities
- Documentation errors

### ✨ New Features
- Additional Zendesk metrics
- New notification formats
- Integration with other platforms
- Performance improvements

### 📚 Documentation
- Setup guide improvements
- Troubleshooting additions
- Code comments and examples
- Translation to other languages

### 🔒 Security
- Security vulnerability reports
- Code security improvements
- Best practices documentation

## 🛠️ Development Guidelines

### Code Style
- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings to all functions
- Keep functions small and focused

### Security Requirements
- Never commit API keys or credentials
- Validate all external inputs
- Use HTTPS for all API calls
- Follow the security guidelines in `SECURITY.md`

### GitHub Actions
- Test workflows in your fork first
- Use secure secret handling
- Add proper error handling
- Document any new required secrets

## 📋 Pull Request Guidelines

### Before Submitting
- [ ] Code follows the project style
- [ ] All tests pass
- [ ] Security review completed
- [ ] Documentation updated
- [ ] No credentials committed

### PR Description Template
```markdown
## Description
Brief description of the changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Security improvement

## Testing
- [ ] Tested locally
- [ ] Integration tests pass
- [ ] GitHub Actions workflow tested

## Security Review
- [ ] No credentials in code
- [ ] Input validation added
- [ ] Security guidelines followed

## Documentation
- [ ] README updated if needed
- [ ] Code commented
- [ ] Examples provided if applicable
```

## 🏷️ Issue Labels

We use these labels to organize issues:

- `bug` - Something isn't working
- `enhancement` - New feature or request
- `documentation` - Improvements or additions to docs
- `good first issue` - Good for newcomers
- `help wanted` - Extra attention needed
- `security` - Security-related issues
- `setup` - Setup and configuration help

## 💬 Getting Help

### For Contributors
- Check existing issues and PRs first
- Use the appropriate issue template
- Join discussions in existing issues
- Ask questions in your PR comments

### For Users
- Use the "Setup Help" issue template
- Check the troubleshooting section first
- Provide detailed error messages
- Include your environment details

## 🎉 Recognition

Contributors will be:
- Listed in the project contributors
- Mentioned in release notes for significant contributions
- Thanked in the project README
- Invited to join the maintainer team for consistent contributors

## 📜 Code of Conduct

This project follows the [GitHub Community Guidelines](https://docs.github.com/en/site-policy/github-terms/github-community-guidelines). Please be respectful and inclusive in all interactions.

### Our Standards
- Use welcoming and inclusive language
- Be respectful of differing viewpoints
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

## 🚨 Reporting Security Issues

**Do not create public issues for security vulnerabilities.**

Please follow the security reporting process in `SECURITY.md`:
1. Email security details privately
2. Include detailed reproduction steps
3. Wait for acknowledgment before public disclosure

## 📞 Contact

- **Issues**: Use GitHub issues for bugs and feature requests
- **Security**: Follow the security reporting process
- **General**: Start a discussion in the GitHub repository

---

Thank you for contributing to make 1on1 meetings more effective for support teams everywhere! 🎯