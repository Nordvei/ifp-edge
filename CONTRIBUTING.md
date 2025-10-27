# Contributing to IFP Edge

Thank you for your interest in contributing to IFP Edge! We welcome contributions from the community.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with:

- **System info**: OS, Docker version, IFP Edge version
- **Steps to reproduce**: Clear, numbered steps
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happens
- **Logs**: Relevant log output (`docker compose logs`)

**Example**:
```
**Environment**: Ubuntu 22.04, Docker 24.0.7, IFP Edge v1.0.0

**Steps to Reproduce**:
1. Run `docker compose up -d`
2. Access Grafana at http://localhost:3001
3. Try to login with admin/admin

**Expected**: Should log in successfully
**Actual**: Returns "Invalid credentials" error

**Logs**:
```
docker logs ifp-grafana
[error] Authentication failed for user admin
```
```

### Feature Requests

We love new ideas! When requesting a feature:

1. **Search first**: Check if it's already requested
2. **Describe the problem**: What are you trying to solve?
3. **Explain the solution**: How would you implement it?
4. **Show value**: Why is this useful for others?

**Example**:
```
**Problem**: Currently, SAGE only monitors Docker containers. I want to monitor bare-metal servers.

**Proposed Solution**: Add support for Node Exporter integration so SAGE can monitor any server with Node Exporter installed.

**Value**: This would allow IFP Edge to monitor entire data centers, not just containerized workloads.
```

### Pull Requests

1. **Fork the repo**
2. **Create a branch**: `git checkout -b feature/your-feature-name`
3. **Make changes**: Write clean, documented code
4. **Test thoroughly**: Ensure nothing breaks
5. **Commit**: Use clear commit messages
6. **Push**: `git push origin feature/your-feature-name`
7. **Create PR**: Describe what you changed and why

**PR Template**:
```markdown
## Description
Brief description of what this PR does

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How did you test this? What should reviewers test?

## Checklist
- [ ] Code follows project style
- [ ] Tests pass
- [ ] Documentation updated
- [ ] No new warnings
```

## Development Setup

### Prerequisites

- Docker 20.10+
- Python 3.9+ (for SAGE development)
- Node.js 18+ (for UI development)
- Git

### Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/ifp-edge.git
cd ifp-edge

# Create development environment
cp .env.example .env

# Start development stack
docker compose -f docker-compose.dev.yml up --build

# Access services
# Grafana: http://localhost:3001
# Prometheus: http://localhost:9090
```

### Running Tests

```bash
# Python tests (SAGE)
cd services/sage
pip install -r requirements-dev.txt
pytest

# Integration tests
./scripts/test-integration.sh

# Linting
./scripts/lint.sh
```

## Code Style

### Python

- Follow [PEP 8](https://peps.python.org/pep-0008/)
- Use type hints
- Document functions with docstrings
- Maximum line length: 100 characters

**Example**:
```python
def calculate_tte(balance: float, drain_rate: float) -> Optional[float]:
    """
    Calculate time-to-empty for a wallet.

    Args:
        balance: Current token balance
        drain_rate: Tokens per hour

    Returns:
        Time in minutes until empty, or None if not draining
    """
    if drain_rate <= 0:
        return None
    return (balance / drain_rate) * 60.0
```

### JavaScript/TypeScript

- Use ES6+ features
- Prefer `const` over `let`
- Use async/await for promises
- Add JSDoc comments

### YAML/Config Files

- Use 2-space indentation
- Add comments for complex configurations
- Validate before committing

## Commit Messages

Use conventional commit format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation change
- `style`: Code style change (formatting)
- `refactor`: Code refactoring
- `test`: Adding/updating tests
- `chore`: Maintenance tasks

**Examples**:
```
feat(sage): add support for Node Exporter metrics

- Parse node_exporter metrics format
- Add new alerting rules for system metrics
- Update documentation

Closes #42
```

```
fix(o2-wallet): handle blockchain connection timeouts

The wallet service now retries failed RPC calls up to 3 times
before marking the service as unhealthy.

Fixes #58
```

## Documentation

When adding features:

1. **Update README.md** if it affects users
2. **Update INSTALL.md** if it changes installation
3. **Add inline comments** for complex logic
4. **Update API docs** if endpoints change

## Testing Guidelines

### Unit Tests

- Test individual functions in isolation
- Mock external dependencies
- Aim for >80% coverage

### Integration Tests

- Test interactions between components
- Use real Docker containers
- Clean up after tests

### Manual Testing

Before submitting a PR:

1. Start fresh: `docker compose down -v && docker compose up -d`
2. Verify all services start successfully
3. Test the specific feature you added
4. Check logs for errors
5. Verify dashboards still work

## Questions?

- **GitHub Discussions**: For questions and community help
- **GitHub Issues**: For bug reports and feature requests
- **Email**: support@infinity-folder.no (for security issues only)

## Code of Conduct

Be respectful, inclusive, and professional. We're all here to build something useful.

### Do:
- ✅ Ask questions
- ✅ Help others
- ✅ Give constructive feedback
- ✅ Admit when you're wrong

### Don't:
- ❌ Be rude or dismissive
- ❌ Make assumptions about skill level
- ❌ Spam issues/PRs
- ❌ Share others' private information

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.

---

**Thank you for contributing to IFP Edge!** 🚀

Every contribution, no matter how small, makes IFP Edge better for everyone.
