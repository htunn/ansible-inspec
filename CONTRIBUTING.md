# Contributing to ansible-inspec

Thank you for your interest in contributing to ansible-inspec! This document provides guidelines for contributing to this project.

## Code of Conduct

This project follows the codes of conduct from our upstream projects:
- [Ansible Code of Conduct](https://docs.ansible.com/ansible/latest/community/code_of_conduct.html)
- [InSpec Code of Conduct](https://github.com/inspec/inspec/blob/main/CODE_OF_CONDUCT.md)

Please be respectful and constructive in all interactions.

## How to Contribute

### Reporting Issues

- Search existing issues before creating a new one
- Provide clear steps to reproduce bugs
- Include version information and environment details
- Use issue templates when available

### Submitting Changes

1. **Fork the repository**
   ```bash
   git clone https://github.com/your-username/ansible-inspec.git
   cd ansible-inspec
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow the coding standards
   - Add tests for new features
   - Update documentation as needed

4. **Test your changes**
   ```bash
   python -m pytest tests/
   ```

5. **Commit your changes**
   ```bash
   git commit -m "Add feature: description"
   ```
   - Use clear, descriptive commit messages
   - Reference issues when applicable

6. **Push and create a Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```

### Development Setup

```bash
# Clone the repository
git clone https://github.com/htunn/ansible-inspec.git
cd ansible-inspec

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run linting
flake8 lib/
black lib/ --check
```

## Coding Standards

- Follow PEP 8 for Python code
- Use type hints where applicable
- Write docstrings for functions and classes
- Keep functions focused and modular
- Add comments for complex logic

## Testing

- Write unit tests for new features
- Maintain or improve code coverage
- Test against multiple Python versions (3.8+)
- Integration tests for CLI commands

## Documentation

- Update README.md for user-facing changes
- Add docstrings to new functions/classes
- Update docs/ for significant features
- Include examples when appropriate

## License Compliance

Since this project combines GPL-3.0 and Apache-2.0 licensed components:

1. **All contributions must be compatible with GPL-3.0**
   - Your contributions will be licensed under GPL-3.0
   - By submitting, you agree to license your contribution under GPL-3.0

2. **Attribution requirements**
   - Credit upstream projects appropriately
   - Document any modifications to upstream code
   - Maintain license headers where applicable

3. **Acceptable contributions**
   - Original code (will be GPL-3.0)
   - Code from GPL-compatible licenses
   - Properly attributed Apache-2.0 code from InSpec
   - Properly attributed GPL-3.0 code from Ansible

4. **Unacceptable contributions**
   - Code from incompatible licenses (MIT, BSD need review)
   - Proprietary code
   - Code without clear licensing

## Questions?

If you have questions about contributing:
- Open a [Discussion](https://github.com/htunn/ansible-inspec/discussions)
- Ask in project chat
- Review existing documentation

Thank you for contributing to ansible-inspec!
