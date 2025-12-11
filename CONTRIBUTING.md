# Contributing to TravelNet Portal

Thank you for your interest in contributing to TravelNet Portal! This document provides guidelines and information for contributors.

## 🤝 How to Contribute

### Reporting Issues

1. **Check existing issues** first to avoid duplicates
2. **Use the issue template** when creating new issues
3. **Provide detailed information**:
   - Raspberry Pi model and OS version
   - TravelNet Portal version
   - Steps to reproduce the issue
   - Expected vs actual behavior
   - Relevant log outputs

### Suggesting Features

1. **Open a feature request** issue
2. **Describe the use case** and why it would be valuable
3. **Consider implementation complexity** and compatibility
4. **Be open to discussion** and alternative approaches

### Code Contributions

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature-name`
3. **Make your changes** following our coding standards
4. **Test thoroughly** on actual Raspberry Pi hardware
5. **Submit a pull request** with a clear description

## 🏗️ Development Setup

### Prerequisites

- Raspberry Pi 3B+ or newer for testing
- Python 3.8+ development environment
- Git and basic command line tools

### Local Development

```bash
# Clone your fork
git clone https://github.com/dekmaskin/TravelRouter.git
cd TravelRouter

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-flask pytest-cov black flake8
```

### Testing

```bash
# Run unit tests
pytest

# Run with coverage
pytest --cov=app

# Run linting
flake8 app/
black --check app/
```

### Testing on Raspberry Pi

Always test your changes on actual Raspberry Pi hardware:

```bash
# Copy files to Pi
scp -r . pi@YOUR_PI_IP:~/travelnet-test/

# SSH to Pi and test
ssh pi@YOUR_PI_IP
cd ~/travelnet-test
sudo ./setup-secure.sh
```

## 📝 Coding Standards

### Python Code Style

- Follow **PEP 8** style guidelines
- Use **Black** for code formatting
- Maximum line length: **88 characters**
- Use **type hints** where appropriate
- Write **docstrings** for all functions and classes

### Code Organization

- **Modular design**: Keep functions small and focused
- **Separation of concerns**: Use the existing app structure
- **Error handling**: Always handle exceptions gracefully
- **Logging**: Use the existing logging framework
- **Security**: Follow security best practices

### Example Code Style

```python
"""Module docstring describing the purpose."""

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def connect_to_wifi(ssid: str, password: Optional[str] = None) -> Dict[str, str]:
    """
    Connect to a WiFi network.
    
    Args:
        ssid: Network name to connect to
        password: Network password (None for open networks)
        
    Returns:
        Dictionary with connection status and message
        
    Raises:
        NetworkError: If connection fails
    """
    try:
        # Implementation here
        logger.info(f"Connecting to network: {ssid}")
        return {"status": "success", "message": "Connected"}
    except Exception as e:
        logger.error(f"Failed to connect to {ssid}: {e}")
        raise NetworkError(f"Connection failed: {e}")
```

## 🧪 Testing Guidelines

### Unit Tests

- Write tests for all new functionality
- Use **pytest** framework
- Mock external dependencies (network calls, system commands)
- Aim for **80%+ code coverage**

### Integration Tests

- Test on actual Raspberry Pi hardware
- Test different Pi models and OS versions
- Test various WiFi adapters and configurations
- Test edge cases and error conditions

### Test Structure

```python
import pytest
from unittest.mock import patch, MagicMock
from app.services.network_service import NetworkService


class TestNetworkService:
    def setup_method(self):
        self.service = NetworkService()
    
    @patch('subprocess.run')
    def test_scan_networks_success(self, mock_run):
        # Test implementation
        pass
    
    def test_validate_ssid_invalid(self):
        # Test implementation
        pass
```

## 📚 Documentation

### Code Documentation

- **Docstrings**: All public functions and classes
- **Type hints**: Use for function parameters and returns
- **Comments**: Explain complex logic and business rules
- **README updates**: Update documentation for new features

### User Documentation

- Update **README.md** for user-facing changes
- Update **SETUP.md** for installation changes
- Update **DEPLOYMENT.md** for deployment changes
- Create **examples** for new features

## 🔐 Security Considerations

### Security Review

All contributions are reviewed for security implications:

- **Input validation**: Sanitize all user inputs
- **Command injection**: Use parameterized commands
- **File permissions**: Set appropriate file permissions
- **Network security**: Follow network security best practices

### Sensitive Information

- **Never commit** passwords, keys, or personal information
- **Use environment variables** for configuration
- **Follow the .gitignore** patterns
- **Review commits** before pushing

## 🚀 Release Process

### Version Numbering

We use **Semantic Versioning** (semver):
- **Major**: Breaking changes
- **Minor**: New features (backward compatible)
- **Patch**: Bug fixes

### Release Checklist

- [ ] All tests pass
- [ ] Documentation updated
- [ ] Version number bumped
- [ ] Changelog updated
- [ ] Security review completed
- [ ] Tested on multiple Pi models

## 🎯 Priority Areas

We especially welcome contributions in these areas:

### High Priority
- **Bug fixes** and stability improvements
- **Security enhancements**
- **Performance optimizations**
- **Hardware compatibility** (new Pi models, WiFi adapters)

### Medium Priority
- **New features** that enhance usability
- **UI/UX improvements**
- **Documentation improvements**
- **Test coverage** expansion

### Low Priority
- **Code refactoring** (without functional changes)
- **Style improvements**
- **Development tooling**

## 📞 Getting Help

### Communication Channels

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Pull Request Comments**: For code review discussions

### Maintainer Response

- **Issues**: We aim to respond within 48 hours
- **Pull Requests**: Initial review within 1 week
- **Security Issues**: Immediate attention (email maintainers directly)

## 🏆 Recognition

Contributors are recognized in several ways:

- **Contributors list** in README.md
- **Release notes** mention significant contributions
- **GitHub contributors** page shows all contributors

## 📋 Pull Request Template

When submitting a pull request, please include:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Security enhancement

## Testing
- [ ] Unit tests pass
- [ ] Tested on Raspberry Pi
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No sensitive information included
```

## 📄 License

By contributing to TravelNet Portal, you agree that your contributions will be licensed under the same [MIT License](LICENSE) that covers the project.

---

Thank you for contributing to TravelNet Portal! Your help makes this project better for everyone. 🚀