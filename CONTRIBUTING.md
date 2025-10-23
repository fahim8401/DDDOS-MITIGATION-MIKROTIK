# Contributing to MikroTik DDoS Monitor

Thank you for considering contributing to this project! This document provides guidelines for contributing.

## How to Contribute

### Reporting Bugs

Before creating a bug report:
1. Check existing issues to avoid duplicates
2. Collect relevant information (logs, configuration, RouterOS version)
3. Create a minimal reproduction case

Include in your bug report:
- **Description**: Clear description of the issue
- **Steps to Reproduce**: Detailed steps to reproduce
- **Expected Behavior**: What should happen
- **Actual Behavior**: What actually happens
- **Environment**: OS, Python version, RouterOS version
- **Logs**: Relevant log excerpts

### Suggesting Features

Feature requests are welcome! Please:
1. Check if the feature already exists or is planned
2. Clearly describe the use case
3. Explain why it would be valuable
4. Provide examples if possible

### Code Contributions

#### Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR-USERNAME/DDDOS-MITIGATION-MIKROTIK.git
   cd DDDOS-MITIGATION-MIKROTIK
   ```

3. Create a branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

4. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   ```

#### Development Guidelines

**Code Style**
- Follow PEP 8 guidelines
- Use Black for code formatting: `black .`
- Use type hints where appropriate
- Write descriptive variable and function names

**Documentation**
- Update README.md if adding features
- Add docstrings to functions and classes
- Update API documentation for new endpoints
- Include inline comments for complex logic

**Testing**
- Write tests for new features
- Ensure existing tests pass: `pytest`
- Aim for good test coverage
- Test with different RouterOS versions if possible

**Commits**
- Use clear, descriptive commit messages
- Reference issues in commits (e.g., "Fixes #123")
- Keep commits focused and atomic
- Follow conventional commits format:
  ```
  feat: add new attack detection algorithm
  fix: resolve connection timeout issue
  docs: update API documentation
  test: add tests for IP blocking
  ```

#### Pull Request Process

1. **Before Submitting**
   - Run tests: `pytest`
   - Run linter: `flake8 .`
   - Format code: `black .`
   - Update documentation
   - Update CHANGELOG.md if applicable

2. **PR Description**
   - Describe what changed and why
   - Reference related issues
   - Include screenshots for UI changes
   - List any breaking changes

3. **Review Process**
   - Maintainers will review your PR
   - Address feedback promptly
   - Be open to suggestions
   - Keep the PR scope focused

4. **After Approval**
   - Squash commits if requested
   - Ensure CI passes
   - Wait for maintainer to merge

## Code of Conduct

### Our Standards

- Be respectful and inclusive
- Accept constructive criticism gracefully
- Focus on what's best for the project
- Show empathy towards others

### Unacceptable Behavior

- Harassment or discrimination
- Trolling or inflammatory comments
- Personal attacks
- Publishing private information
- Other unprofessional conduct

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+ (for frontend)
- Docker (optional)
- MikroTik router or emulator

### Environment Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Install dev dependencies
pip install pytest pytest-cov black flake8 mypy

# Setup pre-commit hooks (optional)
pip install pre-commit
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_monitor.py

# Run with verbose output
pytest -v
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm start

# Run tests
npm test

# Build for production
npm run build
```

### Testing with MikroTik

If you don't have a physical MikroTik router:

1. Use the [CHR (Cloud Hosted Router)](https://mikrotik.com/download) in VirtualBox
2. Use Docker-based RouterOS simulation
3. Use the free trial license for testing

## Project Structure

```
DDDOS-MITIGATION-MIKROTIK/
├── mt_ddos_monitor.py      # Main monitoring application
├── api/
│   └── app.py              # Flask API
├── frontend/
│   ├── src/                # React source
│   └── public/             # Static files
├── scripts/
│   └── mikrotik-scripts.rsc # RouterOS configuration
├── tests/                  # Test files
├── docs/                   # Documentation
├── config.yml              # Configuration
└── requirements.txt        # Python dependencies
```

## API Development

When adding new API endpoints:

1. Add route handler in `api/app.py`
2. Use `@require_api_key` decorator
3. Return JSON responses
4. Add error handling
5. Document in `docs/API.md`
6. Write tests

Example:

```python
@app.route('/api/new-endpoint', methods=['GET'])
@require_api_key
def new_endpoint():
    """Description of endpoint"""
    try:
        # Implementation
        return jsonify({'result': 'success'}), 200
    except Exception as e:
        logging.error(f"Error: {e}")
        return jsonify({'error': str(e)}), 500
```

## Release Process

Releases are managed by maintainers:

1. Update version in relevant files
2. Update CHANGELOG.md
3. Create git tag: `git tag -a v1.0.0 -m "Release 1.0.0"`
4. Push tag: `git push origin v1.0.0`
5. Create GitHub release
6. Build and publish Docker images

## Questions?

- Open a discussion on GitHub Discussions
- Check existing documentation
- Review closed issues for similar questions

## License

By contributing, you agree that your contributions will be licensed under the project's MIT License.

---

Thank you for contributing! 🎉
